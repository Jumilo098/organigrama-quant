"""10 · Estacionalidad en materias primas — el calendario también mueve precios.

Gas natural antes del invierno, granos en siembra y cosecha. Para cada mes del
calendario se mira SOLO lo que pasó ese mismo mes en años anteriores (ventana
expansiva) y se opera el mes si el patrón es fuerte. Muy descorrelacionado,
pero con pocas operaciones al año: sirve más como filtro para otros bots.
"""
import numpy as np
import pandas as pd

from nucleo import datos, motor

FICHA = {
    "id": "b10_estacionalidad_commodities",
    "nombre": "Estacionalidad en materias primas (futuros)",
    "concepto": "Aprovechar patrones de temporada: el gas natural antes del invierno, los granos en siembra y cosecha, "
                "la gasolina de calefacción. El calendario es la señal.",
    "regla": "Para cada futuro y cada mes: media y t-estadístico del retorno de ese mes del calendario en TODOS los años "
             "anteriores (mínimo 5). Largo el mes completo si t > 1,5; corto si t < -1,5. Cartera equiponderada de "
             "NG, CL, HO, ZC, ZW, ZS.",
    "para_quien": "Microfuturos en EE. UU. y CFD de materias primas en Latinoamérica.",
    "datos": "yfinance futuros continuos diarios NG=F, CL=F, HO=F, ZC=F, ZW=F, ZS=F",
    "potencial": "Bajo a medio. Muy descorrelacionado, pero son pocas operaciones al año: validar 80 tomaría años. "
                 "Sirve más como filtro para otros bots que como aporte propio.",
    "siguiente": "Usarlo como filtro (no operar en contra de la temporada) sobre un bot de tendencia en gas o crudo.",
}

TICKERS = ["NG=F", "CL=F", "HO=F", "ZC=F", "ZW=F", "ZS=F"]


def _senal_mensual(close: pd.Series, umbral: float, min_años: int) -> pd.Series:
    mensual = close.resample("ME").last().pct_change().dropna()
    senal = pd.Series(0.0, index=mensual.index)
    for fecha in mensual.index:
        previos = mensual[(mensual.index.month == fecha.month) & (mensual.index.year < fecha.year)]
        if len(previos) < min_años or previos.std() == 0:
            continue
        t = previos.mean() / (previos.std() / np.sqrt(len(previos)))
        senal[fecha] = 1.0 if t > umbral else (-1.0 if t < -umbral else 0.0)
    return senal


def _una(ticker, umbral, min_años):
    df = datos.yf(ticker, "2000-01-01")
    close = df["close"]
    close = close[close > 0]  # los continuos de yfinance traen precios <= 0 (crudo abr-2020)
    senal = _senal_mensual(close, umbral, min_años)
    # pos al cierre del día t = señal del mes al que pertenece el día SIGUIENTE (el calendario se conoce)
    mes_siguiente = pd.Series(close.index.tz_localize(None), index=close.index).shift(-1).dt.to_period("M")
    mapa = {p.tz_localize(None).to_period("M"): v for p, v in senal.items()}
    pos = mes_siguiente.map(lambda p: mapa.get(p, 0.0) if pd.notna(p) else 0.0).astype(float)
    return motor.por_posicion(close, pos, f"b10_{ticker}", costo_lado=0.0005)


def correr(umbral=1.5, min_años=5):
    patas = [_una(t, umbral, min_años) for t in TICKERS]
    res = motor.combinar(patas, FICHA["id"])

    def _pl(s):
        return pd.concat([p.placebo(s + 97 * i) for i, p in enumerate(patas)], axis=1).fillna(0).mean(axis=1)

    res.placebo = _pl
    res.notas = [
        "TRAMPA: los futuros continuos de yfinance empalman contratos sin ajustar; cada roll mete un salto de "
        "precio que no es retorno real (sobre todo en NG y CL con contango fuerte).",
        "Se descartan cierres <= 0 (el crudo cotizó negativo en abr-2020).",
        "Pocas operaciones por año y por mercado: el t-estadístico con 5-20 años es frágil y hay 72 celdas "
        "mes×mercado probadas a la vez (múltiples comparaciones).",
        "Costo 5 pb por lado; no incluye roll ni margen de futuros.",
    ]
    return res
