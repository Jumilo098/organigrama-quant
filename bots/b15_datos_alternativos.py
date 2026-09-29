"""15 · Datos alternativos — el bot desechable de lo que casi nadie mira.

Probabilidades de mercados de predicción (Polymarket), sentimiento en X (vía
Grok, a futuro), patrones de insiders en mercados de predicción. Es el terreno
con mayor varianza: donde más posibilidad hay de un edge propio porque nadie
compite ahí, y también donde más probable es que sea ruido.

La v1 es sobre todo un COLECTOR: antes de backtestear hay que construir el
dataset (el trabajo de la niñera). Si hay historial suficiente, corre un
backtest mínimo; si no, lo dice y devuelve un resultado vacío.
"""
from __future__ import annotations

import datetime as dt
import json

import numpy as np
import pandas as pd

from nucleo import datos, motor

FICHA = {
    "id": "b15_datos_alternativos",
    "nombre": "Datos alternativos (Polymarket → BTC)",
    "concepto": "Usar fuentes poco exploradas — probabilidades de Polymarket, sentimiento en X, insiders en mercados de "
                "predicción — como disparador. Nadie compite ahí; por eso también puede ser puro ruido.",
    "regla": "v1: registrar cada día las probabilidades de los mercados más líquidos de Polymarket (colector). "
             "Backtest mínimo si hay historial: si la probabilidad de un mercado cripto sube más de 5 puntos en 7 días, "
             "largo BTC los 5 días siguientes.",
    "para_quien": "Exploradores con capital pequeño, dentro del 10 % especulativo.",
    "datos": "API pública de Polymarket (gamma-api / clob prices-history) + yfinance BTC-USD. Grok (sentimiento en X) queda como fuente futura.",
    "potencial": "El de mayor varianza. Donde más posibilidad hay de un edge propio (nadie compite ahí) y donde más "
                 "probable es que sea ruido. Terreno natural del bot desechable.",
    "siguiente": "Dejar el colector corriendo (niñera) varias semanas y solo entonces formular hipótesis pre-registradas.",
}

GAMMA = "https://gamma-api.polymarket.com/markets"
CLOB = "https://clob.polymarket.com/prices-history"
RUTA_SNAP = datos.CACHE / "polymarket_snapshots.csv"


def _get(url: str, params: dict) -> object:
    import requests

    r = requests.get(url, params=params, timeout=20, headers={"User-Agent": "organigrama-quant/1.0"})
    r.raise_for_status()
    return r.json()


def registrar(limite: int = 50) -> pd.DataFrame:
    """Colector forward: foto de las probabilidades de los mercados más líquidos. Correr 1 vez al día."""
    mercados = _get(GAMMA, {"limit": limite, "closed": "false", "order": "volumeNum", "ascending": "false"})
    ahora = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    filas = []
    for m in mercados:
        precios = m.get("outcomePrices")
        precios = json.loads(precios) if isinstance(precios, str) else precios
        filas.append({"ts": ahora, "id": m.get("id"), "slug": m.get("slug"), "pregunta": m.get("question"),
                      "prob_si": float(precios[0]) if precios else np.nan,
                      "volumen": m.get("volumeNum"), "liquidez": m.get("liquidityNum")})
    df = pd.DataFrame(filas)
    df.to_csv(RUTA_SNAP, mode="a", header=not RUTA_SNAP.exists(), index=False)
    return df


def historial(token_id: str) -> pd.Series:
    """Serie diaria de probabilidad de un token (resultado) de Polymarket."""
    d = _get(CLOB, {"market": token_id, "interval": "max", "fidelity": 1440})
    h = d.get("history", []) if isinstance(d, dict) else []
    s = pd.Series({pd.Timestamp(x["t"], unit="s", tz="UTC").normalize(): float(x["p"]) for x in h})
    if len(s):
        s.to_csv(datos.CACHE / f"polymarket_{token_id[:16]}.csv")
    return s.sort_index()


def _vacio(motivo: str) -> motor.Resultado:
    hoy = pd.Timestamp.now(tz="UTC").normalize()
    rend = pd.Series(0.0, index=pd.date_range(hoy - pd.Timedelta(days=29), hoy, freq="D"))
    return motor.Resultado(FICHA["id"], rend, pd.DataFrame(columns=["entrada", "salida", "lado", "ret", "velas"]),
                           365, [f"Sin muestra: primero se construye el dataset (niñera). {motivo}",
                                 "Grok (sentimiento en X) queda como segunda fuente para el colector."], None)


def correr(umbral=0.05, ventana=7, sostener=5, min_dias=120):
    try:
        mercados = _get(GAMMA, {"limit": 200, "closed": "false", "order": "volumeNum", "ascending": "false"})
    except Exception as e:
        return _vacio(f"La API de Polymarket no respondió desde esta máquina ({type(e).__name__}); en Colombia "
                      "el acceso suele estar bloqueado a nivel de red. Hay que correr el colector desde otra red/VPS.")
    cripto = [m for m in mercados if any(k in (m.get("question") or "").lower() for k in ("bitcoin", "btc", "crypto"))]
    series = []
    for m in cripto[:10]:
        tokens = m.get("clobTokenIds")
        tokens = json.loads(tokens) if isinstance(tokens, str) else tokens
        if not tokens:
            continue
        try:
            s = historial(tokens[0])
        except Exception:
            continue
        if len(s) >= min_dias:
            series.append(s)
    if not series:
        return _vacio(f"Ningún mercado cripto con ≥ {min_dias} días de historial diario.")

    btc = datos.yf("BTC-USD", "2020-01-01")["close"]
    btc.index = btc.index.normalize()
    senal = pd.Series(0.0, index=btc.index)
    for s in series:
        sube = (s - s.shift(ventana)) > umbral
        disparo = sube.reindex(btc.index).fillna(False).astype(float)
        senal = senal.add(disparo.rolling(sostener, min_periods=1).max(), fill_value=0)
    pos = (senal > 0).astype(float)
    return motor.por_posicion(btc, pos, FICHA["id"], costo_lado=0.001, anual=365,
                              notas=["Historial de mercados que siguen ABIERTOS hoy: sesgo de selección (los que "
                                     "cerraron no entran).", "Muestra muy corta; tratar cualquier resultado como ruido."])
