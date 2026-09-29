"""06 · Insider Purchase Signal — seguir al directivo que compra con su propio dinero.

Cuando un ejecutivo compra acciones de su empresa con plata propia (formulario 4,
código P) suele saber algo. Las ventas dicen poco: pueden ser impuestos,
diversificación o planes programados. La señal ya está procesada en Profeta.

v1: estudio de eventos. Histórico de compras >= 500.000 USD de openinsider.com
(que agrega los formularios 4 de la SEC), se quitan los fondos que solo son
"10 %" y se toman las 5 compras más grandes de cada mes. Se compra al cierre de
la primera sesión posterior al filing y se mantiene 20 sesiones.

Aquí vive `cartera_eventos` (lo reutiliza b07).
"""
from __future__ import annotations

import io
import time

import numpy as np
import pandas as pd

from nucleo import datos, motor

FICHA = {
    "id": "b06_insiders",
    "nombre": "Compras de insiders con dinero propio (formulario 4)",
    "concepto": "Seguir al directivo que compra acciones de su empresa con su propio dinero: suele saber algo. "
                "Las ventas no se siguen (impuestos, planes programados).",
    "regla": "Compras (código P) >= 500.000 USD de directivos (sin los que solo son accionistas del 10 %); las 5 más "
             "grandes de cada mes. Largo al cierre de la primera sesión después del filing, salida a las 20 sesiones. "
             "Cada posición pesa 1/max(abiertas, 5); costo 10 pb por lado.",
    "para_quien": "Cuentas de acciones en Interactive Brokers desde 2.000-5.000 USD, desde EE. UU. o Latinoamérica.",
    "datos": "openinsider.com (formularios 4 de la SEC) + precios diarios yfinance",
    "potencial": "Alto dentro de la comunidad: la señal ya está procesada en Profeta, casi ningún retail hispano la usa y "
                 "cuesta poco convertirla en bot. Límite: las compras relevantes son pocas y la muestra crece lento.",
    "siguiente": "Pasar la fuente a Profeta (que ya separa compras con dinero propio de compensación y mide el % de la "
                 "posición) y probar el filtro 'amplía > 10 % su posición' y las compras en grupo (cluster buys).",
}

URL = ("http://openinsider.com/screener?s=&o=&pl=&ph=&ll=&lh=&fd=-1&fdr={d1}+-+{d2}&td=0&tdr=&fdlyl=&fdlyh=&daysago="
       "&xp=1&vl=500&vh=&ocl=&och=&sic1=-1&sicl=100&sich=9999&grp=0&nfl=&nfh=&nil=&nih=&nol=&noh=&v2l=&v2h=&oc2l=&oc2h="
       "&sortcol=0&cnt=1000&page={p}")


def _descargar(desde=2015) -> pd.DataFrame:
    ruta = datos.CACHE / "b06_openinsider.parquet"
    if ruta.exists():
        return pd.read_parquet(ruta)
    import requests

    partes = []
    hoy = pd.Timestamp.now()
    for ini in pd.date_range(f"{desde}-01-01", hoy, freq="QS"):
        fin = min(ini + pd.offsets.QuarterEnd(0), hoy)
        for p in range(1, 4):
            u = URL.format(d1=ini.strftime("%m%%2F%d%%2F%Y"), d2=fin.strftime("%m%%2F%d%%2F%Y"), p=p)
            h = requests.get(u, headers={"User-Agent": "Mozilla/5.0 (investigacion organigrama-quant)"}, timeout=60).text
            tablas = [t for t in pd.read_html(io.StringIO(h)) if "Ticker" in "".join(map(str, t.columns))]
            time.sleep(1.5)                                      # educado con el servidor
            if not tablas:
                break
            t = tablas[0]
            partes.append(t)
            if len(t) < 1000:
                break
        print(f"  openinsider {ini.date()} ok")
    df = pd.concat(partes, ignore_index=True)
    df.columns = [str(c).replace("\xa0", " ") for c in df.columns]
    df = df[["Filing Date", "Ticker", "Title", "Value"]].rename(
        columns={"Filing Date": "filing", "Ticker": "ticker", "Title": "cargo", "Value": "valor"})
    df["filing"] = pd.to_datetime(df["filing"])
    df["valor"] = pd.to_numeric(df["valor"].astype(str).str.replace(r"[^\d.]", "", regex=True), errors="coerce")
    df["cargo"] = df["cargo"].astype(str)
    df.to_parquet(ruta)
    return df


def precios_lote(tickers: list[str], nombre: str, desde="2014-06-01") -> pd.DataFrame:
    """Cierres ajustados de muchos tickers en lotes, con caché propia."""
    ruta = datos.CACHE / f"{nombre}.parquet"
    if ruta.exists():
        return pd.read_parquet(ruta)
    import yfinance

    cols = []
    for i in range(0, len(tickers), 100):
        lote = tickers[i:i + 100]
        d = yfinance.download(lote, start=desde, auto_adjust=True, progress=False, threads=True)
        if d is None or d.empty:
            continue
        c = d["Close"] if isinstance(d.columns, pd.MultiIndex) else d[["Close"]].rename(columns={"Close": lote[0]})
        cols.append(c)
        time.sleep(1)
    tabla = pd.concat(cols, axis=1).dropna(how="all", axis=1)
    tabla.index = pd.to_datetime(tabla.index).tz_localize(None).normalize()
    tabla = tabla.loc[:, ~tabla.columns.duplicated()]
    tabla.to_parquet(ruta)
    return tabla


def cartera_eventos(eventos: pd.DataFrame, cierres: pd.DataFrame, nombre: str, velas: int = 20,
                    costo_lado: float = 0.001, notas=None, placebo=True, extra=None, cupos: int = 1) -> motor.Resultado:
    """eventos: columnas ticker, fecha (se entra al cierre de la primera sesión >= fecha), lado (+1/-1).

    cupos: cada posición pesa 1/max(abiertas, cupos) — con una sola posición abierta no se apuesta toda la cuenta.
    Retornos diarios absurdos (> +100 % o < -90 %) se tratan como error de datos y se anulan.
    """
    ret = cierres.pct_change()
    ret = ret.where((ret < 1.0) & (ret > -0.9))
    idx = cierres.index
    n = len(idx)

    def _simular(ev: pd.DataFrame):
        suma = np.zeros(n)
        activos = np.zeros(n)
        giros = np.zeros(n)
        filas = []
        for e in ev.itertuples():
            if e.ticker not in cierres.columns:
                continue
            i = idx.searchsorted(pd.Timestamp(e.fecha).tz_localize(None).normalize())
            if i >= n - 1 or not np.isfinite(cierres[e.ticker].iloc[i]):
                continue
            j = min(i + velas, n - 1)
            r = ret[e.ticker].iloc[i + 1:j + 1].to_numpy(float)
            r = np.where(np.isfinite(r), r, 0.0) * e.lado
            suma[i + 1:j + 1] += r
            activos[i + 1:j + 1] += 1
            giros[i + 1] += 1
            giros[j] += 1
            filas.append({"entrada": idx[i], "salida": idx[j], "lado": int(e.lado), "ticker": e.ticker,
                          "ret": float(np.prod(1 + r) - 1 - 2 * costo_lado), "velas": j - i})
        den = np.maximum(activos, cupos)
        rend = pd.Series(suma / den - giros / den * costo_lado, index=idx)
        return rend, pd.DataFrame(filas)

    rend, trades = _simular(eventos)
    if not trades.empty:
        tz = "UTC"
        rend.index = rend.index.tz_localize(tz)
        for k in ("entrada", "salida"):
            trades[k] = pd.to_datetime(trades[k]).dt.tz_localize(tz)
        primero = trades["entrada"].min()
        rend = rend[rend.index >= primero]

    def _placebo(semilla: int) -> pd.Series:
        rng = np.random.default_rng(semilla)
        ev = eventos.copy()
        desf = rng.integers(20, 250, len(ev)) * rng.choice([-1, 1], len(ev))
        ev["fecha"] = [idx[int(np.clip(idx.searchsorted(pd.Timestamp(f).tz_localize(None).normalize()) + d, 0, n - 2))]
                       for f, d in zip(ev["fecha"], desf)]
        r, _ = _simular(ev)
        r.index = r.index.tz_localize("UTC")
        return r[r.index >= rend.index[0]] if len(rend) else r

    return motor.Resultado(nombre, rend, trades, 252, list(notas or []), _placebo if placebo else None, dict(extra or {}))


def correr(velas=20, por_mes=5):
    notas = ["Sesgo de supervivencia: yfinance no tiene precio de muchas empresas deslistadas; los eventos sin precio "
             "se descartan, y suelen ser los peores.",
             "openinsider publica la hora del filing; se entra al cierre de la PRIMERA sesión posterior a la fecha del "
             "filing (sin mirar el futuro, pero se pierde parte de la reacción del día).",
             "Días sin posiciones abiertas cuentan como 0 % (efectivo).",
             "Placebo: los mismos tickers con la fecha de entrada desplazada ±20-250 sesiones al azar."]
    try:
        compras = _descargar()
    except Exception as e:
        import pandas as _pd
        vacio = _pd.Series([0.0], index=_pd.DatetimeIndex([_pd.Timestamp.now(tz="UTC").normalize()]))
        return motor.Resultado(FICHA["id"], vacio, _pd.DataFrame(), 252,
                               notas + [f"SIN DATOS: no se pudo descargar openinsider ({e}). Reintentar con red."], None)
    directivos = compras[~compras["cargo"].str.fullmatch(r"\s*10%\s*")]
    directivos = directivos.dropna(subset=["valor"])
    directivos = directivos[directivos["ticker"].str.fullmatch(r"[A-Z.]{1,6}", na=False)]
    top = (directivos.assign(mes=directivos["filing"].dt.to_period("M"))
           .sort_values("valor", ascending=False)
           .drop_duplicates(["mes", "ticker"])
           .groupby("mes").head(por_mes))
    tickers = sorted(top["ticker"].str.replace(".", "-", regex=False).unique())
    cierres = precios_lote(tickers, "b06_precios")
    ev = pd.DataFrame({"ticker": top["ticker"].str.replace(".", "-", regex=False),
                       "fecha": top["filing"].dt.normalize() + pd.Timedelta(days=1), "lado": 1})
    spy = datos.yf("SPY", "2014-06-01")["close"]
    res = cartera_eventos(ev, cierres, FICHA["id"], velas, 0.001, cupos=5, notas=notas + [
        "Tamaño: 5 cupos (cada compra pesa 1/5 de la cuenta, o menos si hay más de 5 abiertas).",
        f"Eventos: {len(ev)} compras (top {por_mes}/mes); tickers con precio: {cierres.shape[1]}/{len(tickers)}."])
    spy_r = spy.pct_change().reindex(res.rend.index).fillna(0)
    res.extra["exceso_anual_vs_spy"] = float((res.rend - spy_r).mean() * 252)
    return res
