"""Corre uno, varios o todos los bots y regenera la tabla de resultados.

    python correr.py                 # todos
    python correr.py b01 b09         # solo esos (prefijo)
    python correr.py --placebo 30    # menos placebos = más rápido
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import bots  # noqa: E402
from nucleo import reporte  # noqa: E402

RES = Path(__file__).resolve().parent / "resultados"


def tabla() -> str:
    filas = []
    for p in sorted(RES.glob("b*/resumen.json")):
        r = json.loads(p.read_text(encoding="utf-8"))
        t, o = r["total"], r["fuera_muestra"]
        f = lambda x, pct=False: "—" if x is None or x != x else (f"{x*100:.1f} %" if pct else f"{x:.2f}")
        filas.append(
            f"| [{r['ficha']['id']}]({p.parent.name}/FICHA.md) | {r['ficha']['nombre']} | {t.get('n_trades', 0)} | "
            f"{f(t.get('sharpe'))} | {f(o.get('sharpe'))} | {f(t.get('max_dd'), True)} | "
            f"{f(r.get('placebo_percentil'))} | **{r['veredicto']}** |"
        )
    cab = ("| Bot | Idea | Operaciones | Sharpe total | Sharpe fuera de muestra | DD máx. | Placebo (percentil) | Veredicto v1 |\n"
           "|---|---|---|---|---|---|---|---|\n")
    return cab + "\n".join(filas)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("filtro", nargs="*")
    ap.add_argument("--placebo", type=int, default=100)
    a = ap.parse_args()
    nombres = [n for n in bots.todos() if not a.filtro or any(n.startswith(f) for f in a.filtro)]
    for n in nombres:
        t0 = time.time()
        print(f"▶ {n}", flush=True)
        try:
            m = bots.cargar(n)
            r = reporte.guardar(m.correr(), m.FICHA, n_placebo=a.placebo)
            print(f"  {r['veredicto']} · Sharpe {r['total'].get('sharpe', float('nan')):.2f} · "
                  f"{r['total'].get('n_trades', 0)} ops · {time.time()-t0:.0f}s")
        except Exception:
            traceback.print_exc(file=sys.stdout)
    (RES / "TABLA.md").write_text("# Resultados v1 (prototipos)\n\n" + tabla() + "\n", encoding="utf-8")
    print(f"\nTabla: {RES / 'TABLA.md'}")


if __name__ == "__main__":
    main()
