"""El mayordomo que abre y cierra llaves (metáfora de la sesión 20).

Un bot es una semilla: hace siempre lo mismo. El mayordomo no siembra ni cambia
las semillas; reparte el AGUA (el capital) entre los CULTIVOS (los bots) según
el CLIMA que ve (el régimen de mercado), pero obedece un REGLAMENTO:
ninguna llave se cierra del todo (piso) y ningún cultivo se lleva más de un
tope (techo). El TEMPORIZADOR riega igual llueva o haga sol (pesos fijos).

Este v1 es un mayordomo de reglas, no un LLM: sirve para medir si mover las
llaves aporta algo ANTES de ponerle un agente encima. Las perillas son las
fuerzas de la sesión: cada cuánto revisa (costo de tokens), con qué retraso se
entera (latencia), cuánto se aparta de los pesos fijos (autonomía) y cuánto
cuesta mover una llave.

    python -m cartera.mayordomo                     # bots no reprobados
    python -m cartera.mayordomo --bots b01 b02 b09  # los que tú elijas
"""
from __future__ import annotations

import sys

import argparse
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

RES = Path(__file__).resolve().parents[1] / "resultados"


def cargar(prefijos: list[str] | None = None) -> pd.DataFrame:
    cols = {}
    for p in sorted(RES.glob("b*/resumen.json")):
        r = json.loads(p.read_text(encoding="utf-8"))
        nombre = p.parent.name
        if prefijos and not any(nombre.startswith(x) for x in prefijos):
            continue
        if not prefijos and r["veredicto"] in ("REPROBADO v1", "MUESTRA INSUFICIENTE"):
            continue
        s = pd.read_csv(p.parent / "rend_diario.csv", index_col=0, parse_dates=True)["ret"]
        s.index = pd.to_datetime(s.index, utc=True).normalize()
        cols[nombre] = s.groupby(level=0).sum()
    tabla = pd.DataFrame(cols).sort_index()
    tabla = tabla[tabla.index.dayofweek < 5].fillna(0.0)  # días hábiles; lo del finde se pierde (cripto)
    tabla = tabla.loc[:, tabla.std() > 0]
    inicio = max(tabla[c].ne(0).idxmax() for c in tabla)      # periodo común: todos los bots ya existen
    return tabla.loc[inicio:]


def igualar_riesgo(tabla: pd.DataFrame, vol_obj: float = 0.10, ventana: int = 60) -> pd.DataFrame:
    """Lleva cada bot a la misma volatilidad objetivo con su vol PASADA (sin mirar el futuro)."""
    vol = tabla.rolling(ventana, min_periods=20).std().shift(1) * math.sqrt(252)
    escala = (vol_obj / vol).clip(upper=5).fillna(0)
    return tabla * escala


def temporizador(tabla: pd.DataFrame) -> pd.Series:
    return tabla.mean(axis=1)


def mayordomo(
    tabla: pd.DataFrame,
    cada: int = 5,
    latencia: int = 1,
    autonomia: float = 0.5,
    piso: float = 0.05,
    techo: float = 0.40,
    costo_giro: float = 0.0005,
    ventana: int = 60,
    umbral_tormenta: float = 0.35,
) -> tuple[pd.Series, pd.DataFrame]:
    n = tabla.shape[1]
    fijo = np.full(n, 1 / n)
    pesos = pd.DataFrame(np.nan, index=tabla.index, columns=tabla.columns)
    actual = fijo.copy()
    for i in range(ventana + latencia, len(tabla)):
        if (i - ventana - latencia) % cada == 0:
            hist = tabla.iloc[i - ventana - latencia: i - latencia]      # lo que ve, con retraso
            vol = hist.std().replace(0, np.nan)
            tend = hist.sum()
            score = (1 / vol).fillna(0) * (1 + 0.5 * np.sign(tend))    # sol: premia al que va bien
            corr = hist.corr().values
            media_corr = (corr.sum() - n) / (n * (n - 1)) if n > 1 else 0
            if media_corr > umbral_tormenta:                          # tormenta: todo se mueve junto
                aislado = 1 - np.nanmean(np.where(np.eye(n) == 1, np.nan, corr), axis=0)
                score = score * np.clip(aislado, 0.05, None)          # agua a lo descorrelacionado
            dinamico = score.values / score.values.sum() if score.values.sum() > 0 else fijo
            objetivo = (1 - autonomia) * fijo + autonomia * dinamico
            objetivo = np.clip(objetivo, piso, techo)
            actual = objetivo / objetivo.sum()
        pesos.iloc[i] = actual
    pesos = pesos.fillna(pd.Series(fijo, index=tabla.columns))
    giro = pesos.diff().abs().sum(axis=1).fillna(0)
    return (pesos * tabla).sum(axis=1) - giro * costo_giro, pesos


def stats(r: pd.Series) -> dict:
    eq = (1 + r).cumprod()
    años = (r.index[-1] - r.index[0]).days / 365.25
    return {"sharpe": r.mean() / r.std() * math.sqrt(252), "cagr": eq.iloc[-1] ** (1 / años) - 1,
            "max_dd": (eq / eq.cummax() - 1).min()}


def ruina(r: pd.Series, umbral: float = 0.5, horizonte: int = 504, n: int = 2000, bloque: int = 20, semilla: int = 0) -> float:
    """Probabilidad de perder el 50 % en 2 años (bootstrap por bloques de 20 días)."""
    rng = np.random.default_rng(semilla)
    x = r.to_numpy()
    quiebras = 0
    for _ in range(n):
        idx = np.concatenate([np.arange(s, s + bloque) for s in rng.integers(0, len(x) - bloque, horizonte // bloque + 1)])[:horizonte]
        eq = np.cumprod(1 + x[idx])
        quiebras += (eq / np.maximum.accumulate(eq)).min() <= 1 - umbral
    return quiebras / n


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("--bots", nargs="*")
    ap.add_argument("--cada", type=int, default=5)
    ap.add_argument("--latencia", type=int, default=1)
    ap.add_argument("--autonomia", type=float, default=0.5)
    ap.add_argument("--vol", type=float, default=0.20, help="volatilidad anual a la que se llevan ambas carteras para comparar ruina")
    a = ap.parse_args()
    t = igualar_riesgo(cargar(a.bots))
    print(f"Cultivos: {', '.join(t.columns)}  ({t.index[0].date()} → {t.index[-1].date()})")
    c = t.corr().values
    rho = (c.sum() - len(c)) / (len(c) * (len(c) - 1)) if len(c) > 1 else 0
    print(f"Correlación media entre bots: {rho:.2f} → N efectivo {len(c)/(1+(len(c)-1)*rho):.1f} de {len(c)}\n")
    fijo = temporizador(t)
    may, pesos = mayordomo(t, a.cada, a.latencia, a.autonomia)
    # misma volatilidad para las dos (escala constante ex post: solo para comparar ruina a igual riesgo)
    fijo = fijo * a.vol / (fijo.std() * math.sqrt(252))
    may = may * a.vol / (may.std() * math.sqrt(252))
    print(f"Ambas carteras escaladas a {a.vol*100:.0f} % de volatilidad anual.\n")
    print("| Cartera | Sharpe | CAGR | DD máx. | Ruina (−50 % en 2 años) |\n|---|---|---|---|---|")
    for nombre, r in [("Temporizador (pesos fijos)", fijo), ("Mayordomo (reglamento)", may)]:
        s = stats(r)
        print(f"| {nombre} | {s['sharpe']:.2f} | {s['cagr']*100:.1f} % | {s['max_dd']*100:.1f} % | {ruina(r)*100:.1f} % |")
    print("\nPeso medio que asignó el mayordomo:")
    print((pesos.mean() * 100).round(1).astype(str).add(" %").to_string())
