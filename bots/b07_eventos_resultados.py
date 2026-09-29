"""07 · Event-driven — operar la deriva después de los resultados trimestrales.

Contra el trading de alta frecuencia el retail pierde los primeros segundos de la
noticia, pero puede capturar la deriva de horas o días después (post-earnings
announcement drift). Aquí un agente con modelo de lenguaje brillaría leyendo y
clasificando la noticia; la v1 es la versión mecánica.

Fuente de fechas: formularios 8-K con ítem 2.02 ("resultados") de la SEC, con la
hora exacta de aceptación. La sorpresa de consenso no está disponible gratis de
forma fiable (el `get_earnings_dates` de yfinance falla en la versión instalada),
así que la v1 usa la REACCIÓN del precio como proxy de sorpresa (la variante
"earnings announcement return" de la literatura).
"""
from __future__ import annotations

import time

import numpy as np
import pandas as pd

from nucleo import datos
from bots.b06_insiders import cartera_eventos, precios_lote

FICHA = {
    "id": "b07_eventos_resultados",
    "nombre": "Deriva post-resultados (8-K de la SEC, 40 large caps)",
    "concepto": "Operar la reacción a los resultados: el retail no gana la carrera de los primeros segundos, pero sí "
                "puede capturar la deriva de los días siguientes.",
    "regla": "Día de reacción = sesión en la que el mercado ve el 8-K 2.02 (si se publicó tras las 16:00 de Nueva York, "
             "la sesión siguiente). Si ese día el precio sube > 3 %, largo al cierre; si cae > 3 %, corto. Salida a las "
             "20 sesiones. Cada posición pesa 1/max(abiertas, 3); costo 10 pb por lado.",
    "para_quien": "Perfil intermedio-avanzado con datos confiables, sin importar el país.",
    "datos": "SEC EDGAR (fechas y hora de los 8-K ítem 2.02) + precios diarios yfinance",
    "potencial": "Medio. Aquí un agente de lenguaje brilla porque lee y clasifica la noticia, pero el costo en tokens y "
                 "la latencia pesan más que en cualquier otra idea.",
    "siguiente": "Sustituir el proxy por la sorpresa real (consenso vs. reportado) y dejar que un agente clasifique el "
                 "tono de la guía; medir si esa capa añade algo sobre la reacción de precio.",
}

UNIVERSO = ["AAPL", "MSFT", "AMZN", "GOOGL", "META", "NVDA", "JPM", "V", "JNJ", "WMT", "PG", "XOM", "UNH", "HD", "MA",
            "BAC", "KO", "PEP", "CVX", "ABBV", "MRK", "COST", "ADBE", "CRM", "NFLX", "INTC", "CSCO", "ORCL", "AMD",
            "QCOM", "TXN", "NKE", "MCD", "DIS", "IBM", "CAT", "GS", "HON", "UPS", "LOW"]
UA = {"User-Agent": "organigrama-quant/0.1 investigacion"}


def _fechas_8k() -> pd.DataFrame:
    ruta = datos.CACHE / "b07_sec_8k.parquet"
    if ruta.exists():
        return pd.read_parquet(ruta)
    import requests

    filas = []
    for t in UNIVERSO:
        # CIK por el buscador de entidades de EDGAR (www.sec.gov rechaza clientes sin correo de contacto)
        hits = requests.get(f"https://efts.sec.gov/LATEST/search-index?keysTyped={t}", headers=UA, timeout=60).json()
        cik = next((int(h["_id"]) for h in hits["hits"]["hits"] if f"({t})" in h["_source"].get("entity", "")), None)
        time.sleep(0.3)
        if cik is None:
            print(f"  [aviso] sin CIK para {t}")
            continue
        d = requests.get(f"https://data.sec.gov/submissions/CIK{cik:010d}.json", headers=UA, timeout=60).json()
        r = d["filings"]["recent"]
        for i, f in enumerate(r["form"]):
            if f == "8-K" and "2.02" in r["items"][i]:
                filas.append({"ticker": t, "aceptado": r["acceptanceDateTime"][i]})
        time.sleep(0.3)
    df = pd.DataFrame(filas)
    df["aceptado"] = pd.to_datetime(df["aceptado"], utc=True)
    df.to_parquet(ruta)
    return df


def correr(umbral=0.03, velas=20):
    ev8k = _fechas_8k()
    nueva_york = ev8k["aceptado"].dt.tz_convert("America/New_York")
    fecha = nueva_york.dt.tz_localize(None).dt.normalize()
    tarde = nueva_york.dt.hour >= 16
    cierres = precios_lote(UNIVERSO, "b07_precios", desde="2008-01-01")
    idx = cierres.index
    filas = []
    for t, f, tr in zip(ev8k["ticker"], fecha, tarde):
        if t not in cierres.columns:
            continue
        i = idx.searchsorted(f + pd.Timedelta(days=1) if tr else f)   # sesión de reacción
        if i < 1 or i >= len(idx) - 1:
            continue
        r = cierres[t].iloc[i] / cierres[t].iloc[i - 1] - 1
        if np.isfinite(r) and abs(r) > umbral:
            filas.append({"ticker": t, "fecha": idx[i], "lado": int(np.sign(r))})
    ev = pd.DataFrame(filas)
    return cartera_eventos(ev, cierres, FICHA["id"], velas, 0.001, cupos=3, notas=[
        "Tamaño: 3 cupos (cada posición pesa 1/max(abiertas, 3)).",
        "Proxy de sorpresa = reacción del precio del día (no el consenso de analistas): la regla compra lo que ya subió; "
        "no es el PEAD clásico por sorpresa de BPA.",
        "Universo de 40 large caps elegidas HOY: sesgo de supervivencia fuerte (son las ganadoras de la década).",
        f"El historial 'recent' de la SEC trae ~1.000 filings por empresa; hay 8-K 2.02 de {len(ev8k)} anuncios, "
        f"{len(ev)} superan ±{umbral:.0%}.",
        "Días sin posiciones abiertas = 0 % (efectivo). Placebo: mismas acciones, fecha desplazada al azar.",
        "El buscador de EDGAR no resolvió el CIK de GOOGL, JPM, BAC, ORCL y GS: quedan fuera (35 de 40).",
    ])
