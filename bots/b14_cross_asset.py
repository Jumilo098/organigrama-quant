"""14 · Cross-asset signal — mirar un mercado para operar otro.

Usa la información de un activo para decidir en otro: el dólar y las tasas de
los bonos para el oro, el Nikkei para el dólar frente al yen. Es exactamente el
trabajo de analista de la sesión 20 (Impulse Detector ya usa las opciones para
calibrar el stop del USDJPY).
"""
import numpy as np
import pandas as pd

from nucleo import datos, motor

FICHA = {
    "id": "b14_cross_asset",
    "nombre": "Señal cruzada: dólar y tasas → oro; Nikkei → yen (D1)",
    "concepto": "Usar la información de un activo para decidir en otro: tasas de bonos o el índice dólar para el oro, "
                "el Nikkei para el dólar frente al yen.",
    "regla": "Pata oro (50 %): largo XAUUSD si el DXY y la tasa a 10 años (^TNX) cayeron en los últimos 20 días; "
             "corto si ambos subieron; fuera en otro caso. Pata yen (50 %): largo USDJPY si el Nikkei (^N225) subió en "
             "20 días (apetito de riesgo), corto si bajó. Señales con datos del día anterior.",
    "para_quien": "Perfil intermedio, con cualquier capital y desde cualquier país (CFD o futuros).",
    "datos": "MT5 Exness XAUUSD y USDJPY D1 + yfinance DX-Y.NYB, ^TNX y ^N225",
    "potencial": "Medio-alto. Es exactamente el trabajo de analista de la sesión; Impulse Detector ya lo hace al usar "
                 "opciones para calibrar el stop del dólar frente al yen.",
    "siguiente": "Sustituir la regla fija por un analista (agente) que pondere varias señales cruzadas; medir cada "
                 "señal por separado antes de combinarlas.",
}


def _pata_oro(n):
    oro = datos.mt5("XAUUSD", "D1")
    dxy = datos.yf("DX-Y.NYB", "2016-01-01")["close"]
    tnx = datos.yf("^TNX", "2016-01-01")["close"]
    idx = oro.index.normalize()
    dxy = pd.Series(dxy.to_numpy(), index=dxy.index.normalize()).groupby(level=0).last().reindex(idx).ffill()
    tnx = pd.Series(tnx.to_numpy(), index=tnx.index.normalize()).groupby(level=0).last().reindex(idx).ffill()
    d_dxy, d_tnx = dxy.diff(n).shift(1), tnx.diff(n).shift(1)   # datos del día anterior
    pos = pd.Series(np.where((d_dxy < 0) & (d_tnx < 0), 1, np.where((d_dxy > 0) & (d_tnx > 0), -1, 0)), index=idx)
    precio = pd.Series(oro["close"].to_numpy(), index=idx)
    costo = pd.Series((oro["spread_pts"] * oro["point"] / oro["close"] / 2).to_numpy(), index=idx)
    return motor.por_posicion(precio, pos, "oro", costo_lado=costo, swap_largo=0.00016, anual=252)


def _pata_yen(n):
    fx = datos.mt5("USDJPY", "D1")
    nk = datos.yf("^N225", "2016-01-01")["close"]
    idx = fx.index.normalize()
    nk = pd.Series(nk.to_numpy(), index=nk.index.normalize()).groupby(level=0).last().reindex(idx).ffill()
    d = nk.pct_change(n).shift(1)
    pos = pd.Series(np.sign(d).fillna(0).to_numpy(), index=idx)
    precio = pd.Series(fx["close"].to_numpy(), index=idx)
    costo = pd.Series((fx["spread_pts"] * fx["point"] / fx["close"] / 2).to_numpy(), index=idx)
    return motor.por_posicion(precio, pos, "yen", costo_lado=costo, anual=252)


def correr(n=20):
    oro, yen = _pata_oro(n), _pata_yen(n)
    res = motor.combinar([oro, yen], FICHA["id"])
    res.placebo = lambda s: pd.concat([oro.placebo(s), yen.placebo(s + 1000)], axis=1).fillna(0).mean(axis=1)
    res.notas = [
        "Swap del oro aproximado (1,6 pb por noche al largo, 0 al corto); el swap de USDJPY no está modelado "
        "(el largo USDJPY suele COBRAR swap, así que la pata yen está subestimada en largos y sobreestimada en cortos).",
        "La tasa ^TNX de yfinance cierra en hora de EE. UU. y las velas D1 de MT5 a las 00:00 UTC: por eso todas "
        "las señales van desplazadas un día.",
        "Spread anterior a 2024-04-16 modelado con la mediana (el terminal guarda 0).",
        "Cada pata es una posición 0/±1 al 50 %: el riesgo no está normalizado por volatilidad.",
    ]
    return res
