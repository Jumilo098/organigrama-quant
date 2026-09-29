"""Carga de datos con caché local.

Dos fuentes:
  - MT5 (Exness): velas BID con spread real por vela. El spread solo viene
    informado desde 2024-04-16; antes el terminal guarda 0 y aquí se rellena con
    la mediana de lo observado (queda marcado como `spread_modelado`).
  - yfinance: acciones, ETFs, futuros continuos, índices y cripto diarios.

Todo se guarda en datos/cache/ (fuera de git) para no descargar dos veces.
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
CACHE = RAIZ / "datos" / "cache"
CACHE.mkdir(parents=True, exist_ok=True)

MT5_TERMINAL = r"C:\Program Files\MetaTrader 5 EXNESS\terminal64.exe"
_TF = {"M1": 1, "M5": 5, "M15": 15, "M30": 30, "H1": 16385, "H4": 16388, "D1": 16408}


def _cache(nombre: str) -> Path:
    return CACHE / f"{nombre}.parquet"


def mt5(simbolo: str, tf: str = "M15", desde: str = "2017-01-01", refrescar: bool = False) -> pd.DataFrame:
    """Velas de MT5 en UTC: open high low close spread_pts point spread_modelado."""
    ruta = _cache(f"mt5_{simbolo}_{tf}")
    if ruta.exists() and not refrescar:
        return pd.read_parquet(ruta)
    try:
        import MetaTrader5 as m
    except ImportError as e:  # pragma: no cover
        raise RuntimeError("Instala MetaTrader5 (pip install MetaTrader5) y abre el terminal") from e
    if not m.initialize(MT5_TERMINAL):
        raise RuntimeError(f"MT5 no inicializa: {m.last_error()}")
    try:
        m.symbol_select(simbolo, True)
        info = m.symbol_info(simbolo)
        r = m.copy_rates_range(simbolo, _TF[tf], dt.datetime.fromisoformat(desde), dt.datetime.now())
        if r is None or len(r) == 0:
            raise RuntimeError(f"Sin datos para {simbolo} {tf}: {m.last_error()}")
    finally:
        m.shutdown()
    df = pd.DataFrame(r)
    df.index = pd.to_datetime(df["time"], unit="s", utc=True)
    df = df.rename(columns={"spread": "spread_pts"})[["open", "high", "low", "close", "spread_pts"]]
    df["spread_pts"] = df["spread_pts"].astype(float)
    df["point"] = info.point
    df["spread_modelado"] = df["spread_pts"] <= 0
    reales = df.loc[~df["spread_modelado"], "spread_pts"]
    df.loc[df["spread_modelado"], "spread_pts"] = float(reales.median()) if len(reales) else 0.0
    df.to_parquet(ruta)
    return df


def yf(ticker: str, desde: str = "2005-01-01", intervalo: str = "1d", refrescar: bool = False) -> pd.DataFrame:
    """OHLC ajustado por dividendos y splits (auto_adjust)."""
    limpio = ticker.replace("^", "IDX_").replace("=", "_").replace("/", "_")
    ruta = _cache(f"yf_{limpio}_{intervalo}")
    if ruta.exists() and not refrescar:
        return pd.read_parquet(ruta)
    import yfinance

    import time

    df = None
    for intento in range(4):  # Yahoo responde 429 si se le pide mucho a la vez
        df = yfinance.download(ticker, start=desde, interval=intervalo, auto_adjust=True, progress=False)
        if df is not None and not df.empty:
            break
        time.sleep(5 * (intento + 1))
    if df is None or df.empty:
        raise RuntimeError(f"yfinance no devolvió datos para {ticker}")
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df.columns = [c.lower() for c in df.columns]
    df = df[["open", "high", "low", "close"] + (["volume"] if "volume" in df.columns else [])].dropna()
    df.index = pd.to_datetime(df.index)
    if df.index.tz is None:
        df.index = df.index.tz_localize("UTC")
    df.to_parquet(ruta)
    return df


def yf_cierres(tickers: list[str], desde: str = "2005-01-01") -> pd.DataFrame:
    """Tabla de cierres ajustados, una columna por ticker (fechas alineadas)."""
    cols = {}
    for t in tickers:
        try:
            cols[t] = yf(t, desde)["close"]
        except Exception as e:  # un ticker caído no tumba el universo entero
            print(f"  [aviso] {t}: {e}")
    tabla = pd.DataFrame(cols)
    tabla.index = tabla.index.normalize()
    return tabla.groupby(level=0).last().sort_index()


def a_diario(serie: pd.Series) -> pd.Series:
    """Colapsa retornos intradía a retornos diarios compuestos."""
    return (1 + serie).groupby(serie.index.normalize()).prod() - 1


def atr(df: pd.DataFrame, n: int = 14) -> pd.Series:
    prev = df["close"].shift()
    tr = np.maximum(df["high"] - df["low"], np.maximum((df["high"] - prev).abs(), (df["low"] - prev).abs()))
    return tr.rolling(n).mean()
