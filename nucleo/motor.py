"""Motor de backtest común a los 15 bots.

Dos modos, los dos con costos:

1. `por_posicion`: la estrategia entrega una posición objetivo en [-1, 1]
   decidida al CIERRE de cada vela. Se mantiene durante la vela siguiente.
   Costo = |cambio de posición| x costo por lado. Swap por noche opcional.
   Sirve para reglas de rotación, pares, estacionalidad, overnight...

2. `por_stops`: la estrategia entrega señales de entrada (+1 / -1) al cierre.
   Se entra a la APERTURA de la vela siguiente (largo al ASK = bid + spread),
   con stop inicial y trailing en múltiplos de ATR. Dentro de cada vela se
   supone el recorrido ADVERSO primero (primero se mira el stop, luego el
   objetivo). Resultado en R y en equity con riesgo fijo por operación,
   marcada a mercado al cierre de cada día.
   Sirve para tendencia, rupturas y reversión con stop.

Ninguno de los dos modos modela el lote mínimo: eso lo mide aparte
`cartera/lote_minimo.py`, porque es una restricción de la CUENTA y no de la
estrategia (lección del sismógrafo del Runner, sesión 20).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

import numpy as np
import pandas as pd

from .datos import a_diario, atr as _atr


@dataclass
class Resultado:
    nombre: str
    rend: pd.Series                 # retornos DIARIOS de la equity
    trades: pd.DataFrame            # una fila por operación; columna 'ret' (fracción de equity)
    anual: int = 252                # 365 para cripto
    notas: list[str] = field(default_factory=list)
    placebo: Callable[[int], pd.Series] | None = None  # semilla -> retornos diarios del placebo
    extra: dict = field(default_factory=dict)


# ---------------------------------------------------------------- modo posición
def _segmentos(p: pd.Series, r: pd.Series) -> pd.DataFrame:
    signo = np.sign(p).fillna(0)
    cambio = signo.ne(signo.shift()).cumsum()
    filas = []
    for _, idx in signo.groupby(cambio).groups.items():
        s = signo.loc[idx]
        if s.iloc[0] == 0:
            continue
        rr = r.loc[idx]
        filas.append({
            "entrada": idx[0], "salida": idx[-1], "lado": int(s.iloc[0]),
            "ret": float((1 + rr).prod() - 1), "velas": len(idx),
        })
    return pd.DataFrame(filas)


def por_posicion(
    precio: pd.Series,
    pos: pd.Series,
    nombre: str,
    costo_lado: float | pd.Series = 0.0005,
    swap_largo: float = 0.0,
    swap_corto: float = 0.0,
    anual: int = 252,
    intradia: bool = False,
    notas: list[str] | None = None,
    placebo: bool = True,
) -> Resultado:
    """precio: cierres; pos: posición decidida al cierre de cada vela (sin mirar el futuro)."""
    precio = precio.astype(float)
    pos = pos.reindex(precio.index).ffill().fillna(0).clip(-1, 1)

    def _simular(pos_: pd.Series) -> tuple[pd.Series, pd.Series]:
        ret = precio.pct_change().fillna(0)
        p = pos_.shift(1).fillna(0)                      # posición vigente durante la vela
        giro = (p - p.shift(1).fillna(0)).abs()
        costo = giro * (costo_lado if np.isscalar(costo_lado) else costo_lado.reindex(p.index).ffill())
        r = p * ret - costo
        if swap_largo or swap_corto:
            if intradia:
                noche = pd.Series(precio.index.normalize(), index=precio.index).diff().dt.days.fillna(0).clip(lower=0)
            else:
                noche = pd.Series(1.0, index=precio.index)
            r = r - noche * (p.clip(lower=0) * swap_largo + (-p).clip(lower=0) * swap_corto)
        return r, p

    r, p = _simular(pos)
    diario = a_diario(r) if intradia else r
    trades = _segmentos(p, r)

    def _placebo(semilla: int) -> pd.Series:
        rng = np.random.default_rng(semilla)
        n = len(pos)
        k = int(rng.integers(int(n * 0.05), int(n * 0.95)))
        rolado = pd.Series(np.roll(pos.values, k), index=pos.index)
        rp, _ = _simular(rolado)
        return a_diario(rp) if intradia else rp

    return Resultado(nombre, diario, trades, anual, list(notas or []), _placebo if placebo else None,
                     {"exposicion": float((p != 0).mean())})


# ------------------------------------------------------------------ modo stops
def por_stops(
    df: pd.DataFrame,
    entradas: pd.Series,
    nombre: str,
    sl_atr: float = 2.0,
    trail_atr: float | None = 3.0,
    tp_atr: float | None = None,
    atr_n: int = 14,
    max_velas: int | None = None,
    salida: pd.Series | None = None,
    riesgo: float = 0.01,
    costo_lado: float | None = None,
    anual: int = 252,
    notas: list[str] | None = None,
    placebo: bool = True,
) -> Resultado:
    """df con open/high/low/close (BID) y opcionalmente spread_pts + point.

    entradas: +1 largo / -1 corto / 0 nada, decidido al cierre de la vela.
    salida: True al cierre = cerrar en la apertura siguiente (opcional).
    costo_lado: fracción del precio por lado si no hay spread en df (acciones, cripto).
    """
    o, h, l, c = (df[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    if "spread_pts" in df:
        spr = (df["spread_pts"] * df["point"]).to_numpy(float)
    else:
        spr = c * 2 * (costo_lado if costo_lado is not None else 0.0005)  # spread equivalente
    a = _atr(df, atr_n).to_numpy(float)
    idx = df.index
    sal = salida.reindex(idx).fillna(False).to_numpy(bool) if salida is not None else np.zeros(len(df), bool)

    def _correr(ent: np.ndarray) -> pd.DataFrame:
        filas = []
        i, n = 0, len(df)
        while i < n - 1:
            d = ent[i]
            if d == 0 or not np.isfinite(a[i]) or a[i] <= 0:
                i += 1
                continue
            j = i + 1
            precio_in = o[j] + (spr[j] if d > 0 else 0.0)     # largo compra al ask
            riesgo_px = sl_atr * a[i]
            stop = precio_in - d * riesgo_px
            objetivo = precio_in + d * tp_atr * a[i] if tp_atr else None
            extremo = precio_in
            precio_out, k = None, j
            while k < n:
                # precios que disparan: largo sale al BID; corto sale al ASK (bid + spread)
                bajo = l[k] if d > 0 else l[k] + spr[k]
                alto = h[k] if d > 0 else h[k] + spr[k]
                apertura = o[k] if d > 0 else o[k] + spr[k]
                if d > 0 and bajo <= stop:
                    precio_out = min(apertura, stop); break
                if d < 0 and alto >= stop:
                    precio_out = max(apertura, stop); break
                if objetivo is not None:
                    if d > 0 and alto >= objetivo:
                        precio_out = max(apertura, objetivo); break
                    if d < 0 and bajo <= objetivo:
                        precio_out = min(apertura, objetivo); break
                # fin de vela: trailing, salida por regla o por tiempo
                extremo = max(extremo, h[k]) if d > 0 else min(extremo, l[k])
                if trail_atr and np.isfinite(a[k]):
                    nuevo = extremo - d * trail_atr * a[k]
                    stop = max(stop, nuevo) if d > 0 else min(stop, nuevo)
                por_tiempo = max_velas is not None and (k - j + 1) >= max_velas
                if (sal[k] or por_tiempo) and k + 1 < n:
                    k += 1
                    precio_out = o[k] if d > 0 else o[k] + spr[k]
                    break
                k += 1
            if precio_out is None:
                k = n - 1
                precio_out = c[k] if d > 0 else c[k] + spr[k]
            R = d * (precio_out - precio_in) / riesgo_px
            filas.append({"entrada": idx[j], "salida": idx[k], "lado": int(d), "R": float(R),
                          "ret": float(riesgo * R), "velas": k - j + 1,
                          "i_ent": j, "i_sal": k, "p_ent": precio_in, "r_px": riesgo_px})
            i = k  # no se reentra en la misma vela de salida
        return pd.DataFrame(filas)

    dia = idx.normalize()
    ultima_del_dia = np.r_[dia[1:] != dia[:-1], True]           # última vela de cada día

    def _a_diario(tr: pd.DataFrame) -> pd.Series:
        """Equity marcada a mercado al cierre de cada día (las pérdidas flotantes cuentan)."""
        dias = pd.Series(0.0, index=pd.DatetimeIndex(dia.unique()))
        if tr.empty:
            return dias
        fechas, aportes = [], []
        for t in tr.itertuples():
            m = np.arange(t.i_ent, t.i_sal + 1)
            marca = c[m] if t.lado > 0 else c[m] + spr[m]           # largo se valora al bid, corto al ask
            R_m = t.lado * (marca - t.p_ent) / t.r_px
            R_m[-1] = t.R                                            # la última vela cierra al precio real
            corte = ultima_del_dia[m].copy(); corte[-1] = True
            R_dia = R_m[corte]
            fechas.append(dia[m[corte]])
            aportes.append(riesgo * np.diff(np.r_[0.0, R_dia]))
        s = pd.Series(np.concatenate(aportes), index=pd.DatetimeIndex(np.concatenate(fechas)))
        return dias.add(s.groupby(level=0).sum(), fill_value=0.0)

    ent = np.sign(entradas.reindex(idx).fillna(0).to_numpy(float))
    trades = _correr(ent)

    def _placebo(semilla: int) -> pd.Series:
        rng = np.random.default_rng(semilla)
        nent = int((ent != 0).sum())
        falso = np.zeros_like(ent)
        # misma hora del día que las entradas reales (el spread y la volatilidad dependen de la hora)
        horas = np.asarray(idx.hour)
        reales = horas[:-1][ent[:-1] != 0]
        candidatos = {h: np.flatnonzero(horas[:-1] == h) for h in np.unique(reales)}
        pos = np.unique([rng.choice(candidatos[h]) for h in reales]) if nent else np.array([], int)
        # misma proporción de largos/cortos que la señal: el placebo no hereda ni pierde la deriva
        p_largo = float((ent > 0).sum() / max(nent, 1))
        falso[pos] = np.where(rng.random(len(pos)) < p_largo, 1.0, -1.0)
        return _a_diario(_correr(falso))

    extra = {"R_medio": float(trades["R"].mean()) if len(trades) else float("nan")}
    diario = _a_diario(trades)
    trades = trades.drop(columns=[x for x in ("i_ent", "i_sal", "p_ent", "r_px") if x in trades])
    return Resultado(nombre, diario, trades, anual, list(notas or []),
                     _placebo if placebo else None, extra)


# ----------------------------------------------------------- utilidades varias
def combinar(resultados: list[Resultado], nombre: str, pesos: list[float] | None = None) -> Resultado:
    """Suma ponderada de retornos diarios (sub-carteras dentro de un mismo bot)."""
    pesos = pesos or [1 / len(resultados)] * len(resultados)
    tabla = pd.concat([r.rend for r in resultados], axis=1).fillna(0)
    rend = (tabla * pesos).sum(axis=1)
    trades = pd.concat([r.trades for r in resultados], ignore_index=True)
    placebo = None
    if all(r.placebo for r in resultados):
        def placebo(semilla: int) -> pd.Series:
            t = pd.concat([r.placebo(semilla + 1000 * i) for i, r in enumerate(resultados)], axis=1).fillna(0)
            return (t * pesos).sum(axis=1)
    return Resultado(nombre, rend, trades, resultados[0].anual, sum((r.notas for r in resultados), []), placebo)
