"""05 · Value fundamental — comprar negocios buenos cuando están baratos.

Busca empresas que crean valor y cotizan con descuento, que es justamente lo que
hace el escáner de Profeta. El problema honesto: no hay fundamentales
point-in-time gratis (lo que la empresa reportaba EN ESA FECHA, no lo que dice
hoy el histórico corregido), así que la v1 tiene dos piezas separadas:

  (a) `correr()`: backtest PROXY del factor value con ETFs (value vs. growth del
      S&P 500). NO prueba el escáner; prueba si "lo barato" pagó como factor.
  (b) `escanear(tickers)`: el filtro sencillo para usar en FORWARD, con los
      fundamentales actuales de yfinance. Profeta ya tiene estos datos más
      limpios y Juan Camilo puede abrirlos por MCP a los alumnos que lo pidan.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from nucleo import datos
from bots.b04_momentum_acciones import cartera_pesos, fin_de_mes

FICHA = {
    "id": "b05_value_fundamental",
    "nombre": "Value fundamental (proxy con ETFs value/growth + escáner forward)",
    "concepto": "Comprar negocios buenos cuando están baratos: empresas que crean valor (rentabilidad alta) y "
                "cotizan con descuento frente a sus pares.",
    "regla": "PROXY, no el escáner: cada fin de mes, si la razón IVE/IVW (S&P 500 Value / Growth) está por debajo de su "
             "mediana de 3 años (value relativamente barato), se tiene IVE; si no, SPY. Costo 5 pb por lado. "
             "El escáner real (`escanear`) filtra ROE > 15 %, margen > 10 % y PER y EV/EBITDA por debajo de la mediana del universo.",
    "para_quien": "Inversionista paciente, con horizonte de años y cualquier capital.",
    "datos": "yfinance: IVE, IVW, SPY diarios (proxy); fundamentales actuales vía yfinance .info (escáner)",
    "potencial": "Bajo para encontrarlo en semanas: el edge se mide en años. Aun así aporta descorrelación frente a los "
                 "bots de trading, y Profeta ya tiene los datos y se pueden abrir por MCP.",
    "siguiente": "Correr `escanear()` cada mes sobre el universo de Profeta y guardar la foto (fecha, métricas, precio) "
                 "para construir el dataset point-in-time propio; en 12-24 meses ya hay backtest honesto.",
}


def correr(ventana=756):
    c = datos.yf_cierres(["IVE", "IVW", "SPY"], desde="2001-01-01").dropna()
    razon = c["IVE"] / c["IVW"]
    mediana = razon.rolling(ventana).median()
    pesos = {}
    for f in fin_de_mes(c.index):
        if not np.isfinite(mediana.loc[f]):
            continue
        w = pd.Series(0.0, index=c.columns)
        w["IVE" if razon.loc[f] < mediana.loc[f] else "SPY"] = 1.0
        pesos[f] = w
    pesos = pd.DataFrame(pesos).T

    def placebo(semilla: int) -> pd.Series:
        rng = np.random.default_rng(semilla)
        p = pesos.copy()
        elige = rng.random(len(p)) < (pesos["IVE"] > 0).mean()
        p["IVE"], p["SPY"] = elige.astype(float), (~elige).astype(float)
        return cartera_pesos(c, p, "placebo").rend

    return cartera_pesos(
        c, pesos, FICHA["id"], 0.0005, placebo=placebo,
        notas=["ES UN PROXY: mide si inclinarse a value cuando está barato frente a growth pagó. No valida el escáner "
               "de empresas individuales (para eso hacen falta fundamentales point-in-time).",
               "Está casi siempre invertido en renta variable EE. UU.: su correlación con el S&P 500 es alta, no con b01.",
               "Placebo: misma proporción de meses en IVE, pero elegidos al azar.",
               "Los fundamentales de yfinance .info son de HOY; usarlos en el pasado sería mirar el futuro."],
    )


def escanear(tickers: list[str]) -> pd.DataFrame:
    """Filtro forward: 'crea valor' y 'cotiza con descuento' frente a la mediana del propio universo."""
    import yfinance

    filas = []
    for t in tickers:
        try:
            i = yfinance.Ticker(t).info
        except Exception as e:
            print(f"  [aviso] {t}: {e}")
            continue
        filas.append({"ticker": t, "roe": i.get("returnOnEquity"), "margen": i.get("profitMargins"),
                      "per": i.get("trailingPE"), "ev_ebitda": i.get("enterpriseToEbitda"),
                      "precio": i.get("currentPrice"), "fecha": pd.Timestamp.now(tz="UTC").date()})
    df = pd.DataFrame(filas).set_index("ticker")
    for k in ("roe", "margen", "per", "ev_ebitda"):
        df[k] = pd.to_numeric(df[k], errors="coerce")
    df["crea_valor"] = (df["roe"] > 0.15) & (df["margen"] > 0.10)
    df["descuento"] = (df["per"].between(0, df["per"].median())) & (df["ev_ebitda"].between(0, df["ev_ebitda"].median()))
    df["candidata"] = df["crea_valor"] & df["descuento"]
    return df.sort_values(["candidata", "roe"], ascending=False)
