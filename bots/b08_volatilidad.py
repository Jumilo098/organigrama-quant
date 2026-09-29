"""08 · Estrategia de volatilidad — vender o comprar miedo.

Compara la volatilidad que las opciones descuentan (implícita) con la que
realmente ocurre. Vender volatilidad gana seguido y luego puede sufrir un golpe
fuerte; comprarla pierde poco a poco y gana mucho en las crisis: es la versión
operable del 90/10 de Taleb.

No hay histórico gratis de cadenas de opciones, así que la v1 es un PROXY con el
VIX: el disparador sale de opciones (VIX vs. volatilidad realizada) y la
ejecución va al instrumento más simple (SPY). En vivo el disparador saldría de la
cadena de opciones vía IBKR / Impulse Detector, con spreads de riesgo definido.
Nunca opciones vendidas descubiertas.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from nucleo import datos, motor

FICHA = {
    "id": "b08_volatilidad",
    "nombre": "Vender / comprar miedo (proxy VIX sobre SPY, barbell 90/10)",
    "concepto": "Comparar la volatilidad que descuentan las opciones con la que realmente ocurre. Pata 90 %: cobrar la "
                "prima del miedo cuando está cara. Pata 10 %: comprar protección barata antes de la tormenta.",
    "regla": "PROXY. Pata 'vender prima' (90 %): largo SPY mientras VIX − volatilidad realizada 20d del SPY > 3 puntos y "
             "VIX < VIX3M (curva en contango). Pata 'comprar miedo' (10 %): corto SPY 10 sesiones cuando el VIX está por "
             "debajo de su percentil 20 de un año y cruza por encima de su media de 10 días. Costo 5 pb por lado.",
    "para_quien": "Cuentas con opciones en Interactive Brokers desde 5.000-10.000 USD, siempre con spreads de riesgo "
                  "definido y nunca vendiendo opciones descubiertas.",
    "datos": "yfinance: ^VIX, ^VIX3M, SPY diarios",
    "potencial": "Medio. Impulse Detector ya trae el contexto de opciones (la materia prima existe) y la volatilidad "
                 "comprada es la mejor candidata para el 10 % del barbell de Taleb.",
    "siguiente": "Montar la niñera de IBKR (agentes/ninera_ibkr.py) para registrar la implícita real por vencimiento y "
                 "rehacer el disparador con la cadena, no con el VIX.",
}


def correr(prima_min=3.0, peso_barbell=0.10):
    spy = datos.yf("SPY", "2006-01-01")["close"]
    vix = datos.yf("^VIX", "2006-01-01")["close"]
    vix3m = datos.yf("^VIX3M", "2006-01-01")["close"]
    for s in (spy, vix, vix3m):
        s.index = s.index.normalize()
    df = pd.concat({"spy": spy, "vix": vix, "vix3m": vix3m}, axis=1).dropna()
    rv = df["spy"].pct_change().rolling(20).std() * np.sqrt(252) * 100

    pos_prima = ((df["vix"] - rv > prima_min) & (df["vix"] < df["vix3m"])).astype(float)

    bajo = df["vix"] < df["vix"].rolling(252).quantile(0.20)
    cruce = (df["vix"] > df["vix"].rolling(10).mean()) & (df["vix"].shift() <= df["vix"].rolling(10).mean().shift())
    disparo = (bajo & cruce).astype(float)
    pos_miedo = -disparo.replace(0, np.nan).ffill(limit=9).fillna(0)     # corto 10 sesiones

    comunes = ["VIX al cierre (16:15 NY) vs SPY al cierre (16:00): 15 min de desfase, sin efecto práctico en diario.",
               "ES UN PROXY: la pata de prima vendida se expresa como largo SPY, no como venta de opciones; el perfil de "
               "cola real de vender puts/spreads es peor que el de este proxy."]
    a = motor.por_posicion(df["spy"], pos_prima, "prima", costo_lado=0.0005, notas=comunes)
    b = motor.por_posicion(df["spy"], pos_miedo, "miedo", costo_lado=0.0005)
    res = motor.combinar([a, b], FICHA["id"], [1 - peso_barbell, peso_barbell])
    res.placebo = lambda s: (1 - peso_barbell) * a.placebo(s) + peso_barbell * b.placebo(1000 + s)
    res.notas += [f"Pata miedo: {int(disparo.sum())} disparos en todo el periodo (muestra pequeña).",
                  "Operaciones = las de las dos patas juntas; su 'ret' no está ponderado por el 90/10.",
                  "Placebo: cada pata con su posición desplazada en el tiempo al azar."]
    res.extra = {"exposicion_prima": float(pos_prima.mean())}
    return res
