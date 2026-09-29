"""La fábrica de bots desechables (hipótesis de la sesión 20).

Una vez que un modelo frontera montó la idea, un modelo barato (o este script)
puede producir cientos de variantes. El peligro es obvio: si pruebas 500
variantes, alguna sale bonita por pura suerte. Por eso la fábrica no premia al
mejor, lo castiga:

  - Umbral de Sharpe corregido por número de pruebas: sqrt(2 * ln N) / sqrt(años)
    (el máximo esperado de N Sharpes nulos). Solo pasa lo que lo supere.
  - Lo que pasa, pasa a forward como "bot desechable": pequeño, dentro del 10 %
    especulativo de la barra de Taleb, con fecha de caducidad.

    python -m fabrica.fabrica b02 --rejilla '{"umbral_z":[1.5,2,2.5],"ventana":[50,100,200]}'
"""
from __future__ import annotations

import argparse
import itertools
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import bots  # noqa: E402
from nucleo import metricas  # noqa: E402


def umbral_sharpe(n_pruebas: int, años: float) -> float:
    """Sharpe anual que esperarías como MÁXIMO entre n estrategias sin edge."""
    return math.sqrt(2 * math.log(max(n_pruebas, 2))) / math.sqrt(max(años, 0.5))


def fabricar(prefijo: str, rejilla: dict) -> list[dict]:
    nombre = next(n for n in bots.todos() if n.startswith(prefijo))
    modulo = bots.cargar(nombre)
    claves = list(rejilla)
    combinaciones = list(itertools.product(*rejilla.values()))
    salida = []
    for valores in combinaciones:
        params = dict(zip(claves, valores))
        try:
            res = modulo.correr(**params)
        except TypeError as e:
            raise SystemExit(f"{nombre}.correr() no acepta {params}: {e}")
        c = metricas.pd.Timestamp(metricas.CORTE, tz=res.rend.index.tz)
        s_is = metricas._stats(res.rend[res.rend.index < c], res.anual)["sharpe"]
        s_oos = metricas._stats(res.rend[res.rend.index >= c], res.anual)["sharpe"]
        años_is = (min(res.rend.index[-1], c) - res.rend.index[0]).days / 365.25
        salida.append({"params": params, "sharpe_is": s_is, "sharpe_oos": s_oos, "años_is": años_is,
                       "n_trades": len(res.trades)})
        print(f"  {params} → IS {s_is:.2f} · OOS {s_oos:.2f}")
    umbral = umbral_sharpe(len(salida), salida[0]["años_is"])
    elegidas = sorted(salida, key=lambda x: -(x["sharpe_is"] or -9))
    print(f"\n{len(salida)} variantes. Umbral por azar dentro de muestra: Sharpe {umbral:.2f}")
    for v in elegidas[:5]:
        pasa = v["sharpe_is"] > umbral
        print(f"  {'PASA' if pasa else 'azar'} {v['params']} IS {v['sharpe_is']:.2f} → OOS {v['sharpe_oos']:.2f}")
    print("\nLa prueba de verdad es la columna OOS de la mejor variante dentro de muestra, no la mejor OOS.")
    return salida


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("bot")
    ap.add_argument("--rejilla", required=True, help='JSON: {"param": [valores]}')
    a = ap.parse_args()
    fabricar(a.bot, json.loads(a.rejilla))
