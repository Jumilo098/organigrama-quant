"""Métricas, controles y veredicto. La misma vara para los 15 bots.

Controles obligatorios (método del almacén `donde-esta-el-edge`):
  1. Partición dentro/fuera de la muestra (por defecto corte en 2022-01-01).
  2. Resultado SIN el mejor 3 % de las operaciones.
  3. Placebo: la misma gestión con entradas al azar (o la posición desplazada
     en el tiempo). Si el placebo gana igual, la señal no aporta.
  4. Muestra mínima: 80 operaciones antes de hablar de escalar.
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd

from .motor import Resultado

CORTE = "2022-01-01"
MIN_TRADES = 80


def _stats(rend: pd.Series, anual: int) -> dict:
    rend = rend.dropna()
    if len(rend) < 20 or rend.std() == 0:
        return {"sharpe": float("nan"), "cagr": float("nan"), "vol": float("nan"), "max_dd": float("nan"), "dias": len(rend)}
    eq = (1 + rend).cumprod()
    años = max((rend.index[-1] - rend.index[0]).days / 365.25, 1e-9)
    return {
        "sharpe": float(rend.mean() / rend.std() * math.sqrt(anual)),
        "cagr": float(eq.iloc[-1] ** (1 / años) - 1),
        "vol": float(rend.std() * math.sqrt(anual)),
        "max_dd": float((eq / eq.cummax() - 1).min()),
        "dias": len(rend),
    }


def _trades(tr: pd.DataFrame) -> dict:
    if tr is None or tr.empty:
        return {"n_trades": 0}
    r = tr["ret"]
    ganan, pierden = r[r > 0].sum(), -r[r < 0].sum()
    orden = r.sort_values(ascending=False)
    k = max(1, int(round(len(r) * 0.03)))
    out = {
        "n_trades": int(len(r)),
        "win_rate": float((r > 0).mean()),
        "ret_medio_trade": float(r.mean()),
        "profit_factor": float(ganan / pierden) if pierden > 0 else float("inf"),
        "suma_sin_top3pct": float(orden.iloc[k:].sum()),
        "suma_total": float(r.sum()),
    }
    if "R" in tr:
        out["R_medio"] = float(tr["R"].mean())
        out["R_medio_sin_top3pct"] = float(tr["R"].sort_values(ascending=False).iloc[k:].mean())
    return out


def placebo(res: Resultado, n: int = 100) -> dict:
    if res.placebo is None:
        return {"placebo_n": 0}
    real = _stats(res.rend, res.anual)["sharpe"]
    sh = []
    for s in range(n):
        try:
            sh.append(_stats(res.placebo(s), res.anual)["sharpe"])
        except Exception:
            continue
    sh = np.array([x for x in sh if np.isfinite(x)])
    if len(sh) == 0 or not np.isfinite(real):
        return {"placebo_n": 0}
    return {
        "placebo_n": int(len(sh)),
        "placebo_sharpe_mediana": float(np.median(sh)),
        "placebo_percentil": float((sh < real).mean() * 100),
    }


def resumen(res: Resultado, corte: str = CORTE, n_placebo: int = 100) -> dict:
    c = pd.Timestamp(corte, tz=res.rend.index.tz)
    tr = res.trades
    col = "salida" if tr is not None and not tr.empty else None
    tr_is = tr[tr[col] < c] if col else tr
    tr_oos = tr[tr[col] >= c] if col else tr
    out = {
        "bot": res.nombre,
        "desde": str(res.rend.index[0].date()) if len(res.rend) else None,
        "hasta": str(res.rend.index[-1].date()) if len(res.rend) else None,
        "total": {**_stats(res.rend, res.anual), **_trades(tr)},
        "dentro_muestra": {**_stats(res.rend[res.rend.index < c], res.anual), **_trades(tr_is)},
        "fuera_muestra": {**_stats(res.rend[res.rend.index >= c], res.anual), **_trades(tr_oos)},
        **placebo(res, n_placebo),
        **res.extra,
        "notas": res.notas,
    }
    out["veredicto"], out["motivos"] = veredicto(out)
    return out


def veredicto(r: dict) -> tuple[str, list[str]]:
    motivos = []
    is_, oos, tot = r["dentro_muestra"], r["fuera_muestra"], r["total"]
    ok_is = (is_.get("sharpe") or 0) > 0.3
    ok_oos = (oos.get("sharpe") or 0) > 0.3
    ok_pl = r.get("placebo_percentil", 0) >= 95
    ok_n = tot.get("n_trades", 0) >= MIN_TRADES
    ok_top = tot.get("suma_sin_top3pct", -1) > 0
    for ok, txt in [(ok_is, "Sharpe dentro de muestra > 0,3"), (ok_oos, "Sharpe fuera de muestra > 0,3"),
                    (ok_pl, "supera al 95 % de los placebos"), (ok_n, f"≥ {MIN_TRADES} operaciones"),
                    (ok_top, "sigue positivo sin el mejor 3 %")]:
        motivos.append(("✅ " if ok else "❌ ") + txt)
    if tot.get("n_trades", 0) < 30:
        return "MUESTRA INSUFICIENTE", motivos
    if all([ok_is, ok_oos, ok_pl, ok_n, ok_top]):
        return "CANDIDATO A FORWARD", motivos
    if ok_oos and (ok_pl or ok_top):
        return "PROMETEDOR, NO VALIDADO", motivos
    if (oos.get("sharpe") or 0) > 0:
        return "DÉBIL", motivos
    return "REPROBADO v1", motivos
