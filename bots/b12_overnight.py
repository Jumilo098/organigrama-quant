"""12 · Efecto overnight — la bolsa gana de noche.

Históricamente gran parte de la rentabilidad de los índices de EE. UU. ha
ocurrido entre el cierre y la apertura, no durante la sesión. El bot compra al
cierre y vende en la apertura. Es el caso de estudio perfecto de cambio de
régimen: si el Nasdaq pasa a operar 23x5, la "noche" deja de existir como la
conocemos.
"""
import numpy as np
import pandas as pd

from nucleo import datos, motor

FICHA = {
    "id": "b12_overnight",
    "nombre": "Efecto overnight (SPY + QQQ)",
    "concepto": "La bolsa gana de noche: comprar al cierre y vender en la apertura del día siguiente, "
                "sin exposición durante la sesión.",
    "regla": "Cada día hábil: compra al cierre, vende en la apertura siguiente. Cartera 50/50 SPY y QQQ. "
             "Costo 1,5 pb por lado (dos lados por noche).",
    "para_quien": "EE. UU. con ETF de índices o micro y nano futuros, desde capital pequeño.",
    "datos": "yfinance diarios SPY y QQQ (open y close ajustados)",
    "potencial": "Medio. Es el caso de estudio perfecto de cambio de régimen: con el Nasdaq 23x5 desde diciembre de "
                 "2026, medir qué le pasa a este efecto antes y después será una contribución única de la comunidad.",
    "siguiente": "Congelar hoy la medición pre-régimen y repetirla mes a mes después del cambio de horario del Nasdaq.",
}

TICKERS = ["SPY", "QQQ"]


def _partes(ticker):
    df = datos.yf(ticker, "2000-01-01")
    noche = (df["open"] / df["close"].shift(1) - 1).dropna()
    dia = (df["close"] / df["open"] - 1).loc[noche.index]
    return noche, dia


def _sharpe(r):
    return float(r.mean() / r.std() * np.sqrt(252)) if r.std() > 0 else float("nan")


def correr(costo_lado=0.00015):
    noches, dias = zip(*(_partes(t) for t in TICKERS))
    noche = pd.concat(noches, axis=1).dropna().mean(axis=1)
    dia = pd.concat(dias, axis=1).dropna().mean(axis=1)
    idx = noche.index.intersection(dia.index)
    noche, dia = noche.loc[idx], dia.loc[idx]
    costo = 2 * costo_lado
    rend = noche - costo

    trades = pd.DataFrame({
        "entrada": idx, "salida": idx, "lado": 1, "ret": rend.to_numpy(), "velas": 1,
    })

    def _placebo(semilla):
        # misma cantidad de "sesiones" y mismo costo, pero cada día se toma al azar la noche o el día
        rng = np.random.default_rng(semilla)
        elige = rng.random(len(idx)) < 0.5
        return pd.Series(np.where(elige, noche, dia), index=idx) - costo

    bh = (1 + noche) * (1 + dia) - 1
    extra = {
        "sharpe_noche_neto": _sharpe(rend),
        "sharpe_intradia_bruto": _sharpe(dia),
        "sharpe_buy_hold": _sharpe(bh),
        "ret_anual_noche_bruto": float(noche.mean() * 252),
        "ret_anual_intradia_bruto": float(dia.mean() * 252),
    }
    notas = [
        f"Comparación bruta (sin costos), 50/50 SPY+QQQ: retorno anual medio de la noche "
        f"{extra['ret_anual_noche_bruto']*100:.1f} % vs intradía {extra['ret_anual_intradia_bruto']*100:.1f} %; "
        f"Sharpe noche neto {extra['sharpe_noche_neto']:.2f}, intradía bruto {extra['sharpe_intradia_bruto']:.2f}, "
        f"buy & hold {extra['sharpe_buy_hold']:.2f}.",
        "Cada noche cuenta como una operación: la muestra es enorme, pero están autocorrelacionadas por régimen.",
        "El costo decide todo: 2 lados por día. Con 5 pb por lado (acciones sueltas, CFD) el efecto desaparece.",
        "Los open de yfinance son la primera cotización oficial; ejecutar en la subasta de apertura/cierre "
        "(MOO/MOC) es lo que hace realista el costo modelado.",
        "Cambio de régimen: Nasdaq 23x5 aprobado desde el 6-dic-2026 (según la sesión 20). Medir antes/después.",
    ]
    return motor.Resultado(FICHA["id"], rend, trades, 252, notas, _placebo, extra)
