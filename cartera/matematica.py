"""La matemática de la cartera descorrelacionada (Dalio, sesión 20).

Con N bots de riesgo parecido y correlación media rho:
    N_efectivo   = N / (1 + (N - 1) * rho)        # apuestas realmente independientes
    multiplicador = sqrt(N_efectivo)               # cuánto mejora retorno/riesgo
    reducción de riesgo = 1 - 1 / sqrt(N_efectivo) # a igual retorno esperado

Si N crece sin límite, N_efectivo -> 1 / rho: con rho = 0,3 nunca pasarás de
3,3 apuestas independientes aunque corras 50 bots. Por eso BAJAR LA CORRELACIÓN
rinde más que AGREGAR bots.

Regla de entrada de un bot nuevo:
    entra solo si  Sharpe_nuevo > rho(nuevo, cartera) * Sharpe_cartera

    python -m cartera.matematica
"""
from __future__ import annotations

import sys

import math


def n_efectivo(n: int, rho: float) -> float:
    return n / (1 + (n - 1) * rho)


def multiplicador(n: int, rho: float) -> float:
    return math.sqrt(n_efectivo(n, rho))


def reduccion_riesgo(n: int, rho: float) -> float:
    return 1 - 1 / multiplicador(n, rho)


def entra_a_la_cartera(sharpe_nuevo: float, rho_con_cartera: float, sharpe_cartera: float) -> bool:
    return sharpe_nuevo > rho_con_cartera * sharpe_cartera


def tabla(ns=(1, 2, 3, 5, 8, 10, 15, 25, 50), rhos=(0.0, 0.1, 0.2, 0.3, 0.5)) -> str:
    cab = "| N bots | " + " | ".join(f"ρ = {r:.1f}" for r in rhos) + " |\n|---|" + "---|" * len(rhos) + "\n"
    filas = [f"| {n} | " + " | ".join(f"×{multiplicador(n, r):.2f} ({reduccion_riesgo(n, r)*100:.0f} %)" for r in rhos) + " |"
             for n in ns]
    return cab + "\n".join(filas)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print("Multiplicador de retorno/riesgo (y reducción de riesgo) según N y correlación media ρ\n")
    print(tabla())
    print(f"\nDalio, 15 flujos con ρ≈0: ×{multiplicador(15, 0):.2f}, riesgo −{reduccion_riesgo(15, 0)*100:.0f} %")
    print(f"8 bots: pasar de ρ 0,3 a 0,1 → ×{multiplicador(8, .3):.2f} a ×{multiplicador(8, .1):.2f}; "
          f"pasar de 8 a 15 bots con ρ 0,3 → ×{multiplicador(8, .3):.2f} a ×{multiplicador(15, .3):.2f}")
