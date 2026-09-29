"""La niñera: un monitor persistente sobre Interactive Brokers (cuenta PAPER).

Idea de la sesión 20: la niñera NO valida el edge (más horas del mismo código
no añaden muestra). Mide la EJECUCIÓN y el CONTEXTO: para cada ciclo deja
registro de bid, ask, spread, último precio y volatilidad implícita, y de cada
orden llenada (a qué precio salió vs. qué precio había). Con eso se puede
separar un drawdown en tres partes: estrategia, ejecución y contexto.

También sirve para construir el dataset propio de lo que nadie cubre (penny
stocks, litio, mercados emergentes): el trabajo del becario, sin becario.

SOLO LECTURA: este script jamás llama a placeOrder. Se niega a correr si ve una
cuenta que no empiece por "D" o si el puerto no es el 7497 (paper).

    pip install ib_async
    python -m agentes.ninera_ibkr --simbolos SPY GLD --cada 20
    python -m agentes.ninera_ibkr --simbolos MGC:FUT:COMEX --cada 15 --una-vez
"""
from __future__ import annotations

import sys

import argparse
import csv
import datetime as dt
import math
import time
from pathlib import Path

CARPETA = Path(__file__).resolve().parents[1] / "datos" / "ninera"
PUERTO_PAPER = 7497


def conectar(client_id: int = 21):
    from ib_async import IB

    ib = IB()
    ib.connect("127.0.0.1", PUERTO_PAPER, clientId=client_id, timeout=15)
    cuentas = ib.managedAccounts()
    if not cuentas or any(not c.startswith("D") for c in cuentas):
        ib.disconnect()
        raise RuntimeError(f"La niñera solo trabaja en paper. Cuentas visibles: {cuentas}")
    return ib


def contrato(texto: str):
    """SPY -> acción SMART/USD · MGC:FUT:COMEX -> futuro continuo · EURUSD:CASH -> forex."""
    from ib_async import ContFuture, Forex, Stock

    partes = texto.split(":")
    if len(partes) >= 2 and partes[1] == "FUT":
        return ContFuture(partes[0], exchange=partes[2] if len(partes) > 2 else "")
    if len(partes) >= 2 and partes[1] == "CASH":
        return Forex(partes[0])
    return Stock(partes[0], "SMART", "USD")


def _escribir(ruta: Path, fila: dict):
    nuevo = not ruta.exists()
    with ruta.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(fila))
        if nuevo:
            w.writeheader()
        w.writerow(fila)


def ciclo(ib, simbolos: list[str]):
    ahora = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    for s in simbolos:
        c = contrato(s)
        ib.qualifyContracts(c)
        t = ib.reqMktData(c, genericTickList="106", snapshot=False)  # 106 = vol. implícita
        ib.sleep(3)
        bid, ask = t.bid, t.ask
        spread = ask - bid if (bid and ask and bid > 0 and ask > 0) else math.nan
        _escribir(CARPETA / f"cotizaciones_{s.replace(':', '_')}.csv", {
            "ts_utc": ahora, "simbolo": s, "bid": bid, "ask": ask, "ultimo": t.last,
            "spread": spread, "spread_bps": spread / ((bid + ask) / 2) * 1e4 if spread == spread else math.nan,
            "vol_implicita": getattr(t, "impliedVolatility", math.nan),
        })
        ib.cancelMktData(c)
    for f in ib.fills():  # ejecuciones del día: precio de llenado vs. referencia
        _escribir(CARPETA / "llenados.csv", {
            "ts_utc": f.time.isoformat() if f.time else ahora, "simbolo": f.contract.symbol,
            "lado": f.execution.side, "cantidad": f.execution.shares, "precio": f.execution.price,
            "comision": f.commissionReport.commission if f.commissionReport else math.nan,
            "exec_id": f.execution.execId,
        })


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--simbolos", nargs="+", default=["SPY"])
    ap.add_argument("--cada", type=int, default=20, help="minutos entre ciclos")
    ap.add_argument("--una-vez", action="store_true")
    a = ap.parse_args()
    CARPETA.mkdir(parents=True, exist_ok=True)
    while True:
        # reconecta en cada ciclo: la sesión del API de TWS caduca y así nunca se queda colgada
        ib = conectar()
        try:
            ciclo(ib, a.simbolos)
            print(f"{dt.datetime.now():%H:%M} ciclo ok → {CARPETA}")
        finally:
            ib.disconnect()
        if a.una_vez:
            break
        time.sleep(a.cada * 60)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
