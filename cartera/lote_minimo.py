"""La restricción que Dalio no tiene: el lote mínimo.

Si repartes el riesgo entre N bots para que la cartera completa arriesgue lo
mismo que un solo bot, cada bot arriesga menos por operación... pero el lote no
baja de 0,01. La cuenta mínima para que cada bot respete su plan es:

    riesgo_por_bot = riesgo_cartera / sqrt(N * (1 + (N - 1) * rho))
    cuenta_minima  = pérdida_con_lote_mínimo / riesgo_por_bot

Referencia de la sesión 20: el Runner perdió 18,51 USD con 0,01 lotes en su
peor operación (ATR alto). Con 2 % de riesgo de cartera y ρ = 0,2 salen los
números que mostró la terminal en clase (1 bot ≈ 925 USD, 15 bots ≈ 7.000 USD).

    python -m cartera.lote_minimo --perdida 18.51 --riesgo 0.02 --rho 0.2
"""
from __future__ import annotations

import sys

import argparse
import math


def riesgo_por_bot(n: int, riesgo_cartera: float = 0.02, rho: float = 0.2) -> float:
    return riesgo_cartera / math.sqrt(n * (1 + (n - 1) * rho))


def cuenta_minima(perdida_lote_min: float, n: int, riesgo_cartera: float = 0.02, rho: float = 0.2) -> float:
    return perdida_lote_min / riesgo_por_bot(n, riesgo_cartera, rho)


def riesgo_real(perdida_lote_min: float, cuenta: float) -> float:
    """Riesgo efectivo por operación cuando el lote ya está en el mínimo."""
    return perdida_lote_min / cuenta


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("--perdida", type=float, default=18.51, help="pérdida en USD de una operación con el lote mínimo")
    ap.add_argument("--riesgo", type=float, default=0.02, help="riesgo total de la cartera por operación")
    ap.add_argument("--rho", type=float, default=0.2)
    a = ap.parse_args()
    print(f"Pérdida con lote mínimo: {a.perdida} USD · riesgo de cartera {a.riesgo*100:.1f} % · ρ {a.rho}\n")
    print("| Bots | Riesgo por bot | Cuenta mínima |\n|---|---|---|")
    for n in (1, 3, 5, 8, 15):
        print(f"| {n} | {riesgo_por_bot(n, a.riesgo, a.rho)*100:.2f} % | {cuenta_minima(a.perdida, n, a.riesgo, a.rho):,.0f} USD |")
    print(f"\nCuenta real del Runner (626 USD): riesgo efectivo {riesgo_real(a.perdida, 626)*100:.1f} % por operación en la peor.")
