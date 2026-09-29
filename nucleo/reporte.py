"""Guarda el resultado de un bot en resultados/<id>/ y genera su ficha."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from .metricas import resumen
from .motor import Resultado

RAIZ = Path(__file__).resolve().parents[1]
RES = RAIZ / "resultados"


def _pct(x):
    return "—" if x is None or x != x else f"{x*100:,.1f} %"


def _num(x, d=2):
    return "—" if x is None or x != x else f"{x:,.{d}f}"


def guardar(res: Resultado, ficha: dict, n_placebo: int = 100) -> dict:
    carpeta = RES / ficha["id"]
    carpeta.mkdir(parents=True, exist_ok=True)
    r = resumen(res, n_placebo=n_placebo)
    r["ficha"] = ficha
    (carpeta / "resumen.json").write_text(json.dumps(r, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    res.rend.rename("ret").to_csv(carpeta / "rend_diario.csv")
    if res.trades is not None and not res.trades.empty:
        res.trades.to_csv(carpeta / "operaciones.csv", index=False)
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        eq = (1 + res.rend).cumprod()
        fig, ax = plt.subplots(figsize=(9, 3.2))
        ax.plot(eq.index, eq.values, lw=1.2, color="#1f5aa6")
        ax.axvline(pd.Timestamp("2022-01-01", tz=eq.index.tz), color="#999", ls="--", lw=0.8)
        ax.set_title(f"{ficha['id']} · {ficha['nombre']} (línea = corte dentro/fuera de muestra)", fontsize=9)
        ax.grid(alpha=0.3)
        fig.tight_layout()
        fig.savefig(carpeta / "equity.png", dpi=110)
        plt.close(fig)
    except Exception as e:  # el gráfico es opcional
        print(f"  [aviso] sin gráfico: {e}")
    (carpeta / "FICHA.md").write_text(ficha_md(r), encoding="utf-8")
    return r


def ficha_md(r: dict) -> str:
    f = r["ficha"]
    t, i, o = r["total"], r["dentro_muestra"], r["fuera_muestra"]
    filas = [
        ("Sharpe", _num(i.get("sharpe")), _num(o.get("sharpe")), _num(t.get("sharpe"))),
        ("CAGR", _pct(i.get("cagr")), _pct(o.get("cagr")), _pct(t.get("cagr"))),
        ("Drawdown máx.", _pct(i.get("max_dd")), _pct(o.get("max_dd")), _pct(t.get("max_dd"))),
        ("Operaciones", str(i.get("n_trades", 0)), str(o.get("n_trades", 0)), str(t.get("n_trades", 0))),
        ("Win rate", _pct(i.get("win_rate")), _pct(o.get("win_rate")), _pct(t.get("win_rate"))),
        ("Profit factor", _num(i.get("profit_factor")), _num(o.get("profit_factor")), _num(t.get("profit_factor"))),
    ]
    tabla = "| Métrica | Dentro de muestra | Fuera de muestra | Total |\n|---|---|---|---|\n"
    tabla += "\n".join(f"| {a} | {b} | {c} | {d} |" for a, b, c, d in filas)
    pl = (f"Placebo ({r['placebo_n']} corridas): mediana Sharpe {_num(r.get('placebo_sharpe_mediana'))}, "
          f"la señal supera al **{_num(r.get('placebo_percentil'), 0)} %**.") if r.get("placebo_n") else "Placebo: no aplica."
    notas = "\n".join(f"- {n}" for n in r.get("notas", [])) or "- —"
    return f"""# {f['id']} · {f['nombre']}

> **Veredicto v1: {r['veredicto']}** — prototipo de investigación, no es una recomendación ni un sistema para dinero real.

**Concepto.** {f['concepto']}

**Regla v1.** {f['regla']}

**Para quién.** {f['para_quien']}

**Datos e instrumento.** {f['datos']} · Periodo {r['desde']} → {r['hasta']}

**Potencial (según la sesión 20).** {f['potencial']}

## Backtest

{tabla}

{pl}

Sin el mejor 3 % de las operaciones, la suma de retornos queda en {_pct(t.get('suma_sin_top3pct'))} (total {_pct(t.get('suma_total'))}).

**Controles:**
{chr(10).join('- ' + m for m in r['motivos'])}

![equity](equity.png)

## Notas y trampas conocidas
{notas}

## Siguiente paso sugerido
{f.get('siguiente', '—')}
"""
