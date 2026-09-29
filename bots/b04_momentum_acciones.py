"""04 · Momentum en acciones — lo que viene subiendo tiende a seguir subiendo.

Cada mes compra lo que más subió en los últimos 12 meses (saltando el último
mes, el clásico 12-1) y rota lo que se quedó atrás. Para no caer en el sesgo de
supervivencia (backtestear solo las acciones que HOY siguen vivas), la v1 usa un
universo de ETFs de sectores, países y activos, que no desaparecen del índice.

Aquí también vive `cartera_pesos`, el ayudante que convierte una tabla de pesos
mensuales en un Resultado del motor (lo reutilizan b05 y b08).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from nucleo import datos, motor

FICHA = {
    "id": "b04_momentum_acciones",
    "nombre": "Momentum mensual (ETFs de sectores, países y activos)",
    "concepto": "Lo que viene subiendo tiende a seguir subiendo: cada mes se compran los activos más fuertes "
                "de los últimos 6-12 meses y se rotan los que se quedan atrás.",
    "regla": "Último día hábil de cada mes: retorno 12-1 (de hace 252 a hace 21 sesiones) de 20 ETFs; se compran los 4 "
             "mejores a pesos iguales (solo si su 12-1 es positivo; si no, ese hueco queda en efectivo) y se mantienen "
             "un mes. Costo 5 pb por lado sobre el giro.",
    "para_quien": "Inversionistas con Interactive Brokers desde ~5.000 USD (más fácil con acciones o ETFs fraccionados). "
                  "Sirve desde cualquier país.",
    "datos": "yfinance, cierres diarios ajustados de ETFs (sectores SPDR, países y activos)",
    "potencial": "Medio-alto a largo plazo, bajo en semanas: opera una vez al mes, juntar 80 operaciones toma tiempo, "
                 "depende del mercado general y sufre caídas bruscas cuando el momentum se voltea.",
    "siguiente": "Pasarlo a acciones individuales con un universo point-in-time (sin supervivencia) y medir su "
                 "correlación contra b01; probar el filtro de tendencia 1h/4h/1d de la tabla de la sesión.",
}

UNIVERSO = ["XLK", "XLF", "XLE", "XLV", "XLY", "XLP", "XLI", "XLB", "XLU", "XLRE", "XLC",
            "EFA", "EEM", "EWJ", "EWZ", "EWW", "GLD", "TLT", "IWM", "QQQ"]


def fin_de_mes(indice: pd.DatetimeIndex) -> pd.DatetimeIndex:
    s = pd.Series(indice, index=indice)
    return pd.DatetimeIndex(s.groupby([indice.year, indice.month]).last().tolist())


def cartera_pesos(cierres: pd.DataFrame, pesos: pd.DataFrame, nombre: str, costo_lado: float = 0.0005,
                  notas: list[str] | None = None, placebo=None, extra: dict | None = None) -> motor.Resultado:
    """pesos: filas = fechas de decisión (al cierre); se aplican desde la sesión siguiente."""
    ret = cierres.pct_change().fillna(0)
    w = pesos.reindex(cierres.index).ffill().fillna(0)
    vig = w.shift(1).fillna(0)                          # peso vigente durante la sesión
    giro = (vig - vig.shift(1).fillna(0)).abs().sum(axis=1)
    rend = (vig * ret).sum(axis=1) - giro * costo_lado
    filas = []
    for t in vig.columns:
        s = vig[t]
        activo = s.ne(0)
        grupo = (s != s.shift()).cumsum()
        for _, idx in s[activo].groupby(grupo[activo]).groups.items():
            r = ret.loc[idx, t]
            lado = int(np.sign(s.loc[idx[0]]))
            filas.append({"entrada": idx[0], "salida": idx[-1], "lado": lado, "ticker": t,
                          "ret": float((1 + lado * r).prod() - 1 - 2 * costo_lado), "velas": len(idx)})
    trades = pd.DataFrame(filas)
    return motor.Resultado(nombre, rend, trades, 252, list(notas or []), placebo, dict(extra or {}))


def _pesos(cierres: pd.DataFrame, top: int, elegir=None) -> pd.DataFrame:
    fechas = fin_de_mes(cierres.index)
    mom = cierres.shift(21) / cierres.shift(252) - 1
    filas = {}
    for f in fechas:
        m = mom.loc[f].dropna()
        w = pd.Series(0.0, index=cierres.columns)
        if len(m) >= top:
            sel = elegir(m) if elegir else m.nlargest(top)
            sel = sel[sel > 0] if elegir is None else sel
            w[sel.index] = 1 / top
        filas[f] = w
    return pd.DataFrame(filas).T


def correr(top=4):
    cierres = datos.yf_cierres(UNIVERSO, desde="2005-01-01").dropna(how="all")
    pesos = _pesos(cierres, top)

    def placebo(semilla: int) -> pd.Series:
        rng = np.random.default_rng(semilla)
        p = _pesos(cierres, top, elegir=lambda m: m.iloc[rng.choice(len(m), top, replace=False)])
        return cartera_pesos(cierres, p, "placebo").rend

    return cartera_pesos(
        cierres, pesos, FICHA["id"], 0.0005, placebo=placebo,
        notas=["El placebo elige ETFs al azar y siempre está invertido; el bot real se queda en efectivo cuando el "
               "momentum es negativo. Parte de la ventaja frente al placebo viene de ese filtro, no solo del ranking.",
               "Universo de ETFs para evitar sesgo de supervivencia: con acciones individuales tomadas de la lista de "
               "HOY el backtest saldría inflado (las que quebraron no están).",
               "El universo lo elegí a mano en 2026: sigue habiendo un sesgo de selección leve (sé qué ETFs existen hoy). "
               "XLRE (2015) y XLC (2018) entran al universo cuando tienen 12 meses de historia.",
               "Placebo: la misma rotación mensual eligiendo 4 ETFs al azar entre los disponibles.",
               "Operaciones = tramos continuos de tenencia por ETF (un ETF que se queda 3 meses cuenta como una)."],
    )
