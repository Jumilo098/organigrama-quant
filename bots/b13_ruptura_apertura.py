"""13 · Short-term breakout — entrar cuando el precio rompe la caja.

Opera rupturas del rango de apertura de la sesión de Nueva York en el Nasdaq.
Muchas rupturas son falsas y la lógica se parece bastante a la del bot 01
(tendencia): si ya tienes el Runner, aporta poca descorrelación.
"""
import pandas as pd

from nucleo import datos, motor

FICHA = {
    "id": "b13_ruptura_apertura",
    "nombre": "Ruptura del rango de apertura (USTEC M15)",
    "concepto": "Operar rupturas de rango de corto plazo, como el rango de apertura de la sesión en índices.",
    "regla": "Rango = máximo y mínimo de 9:30 a 10:00 de Nueva York (horario de verano respetado). Primera vela M15 "
             "que cierra fuera del rango antes de las 15:00 NY: entra a favor. Sale a las 15:45 NY o con stop de "
             "4 ATR(14) M15. Una operación por día como máximo. Riesgo 1 %.",
    "para_quien": "Cuentas pequeñas con CFD en Latinoamérica o microfuturos (MNQ/MES) en EE. UU.",
    "datos": "MT5 Exness USTEC M15 (velas BID + spread real desde 2024-04-16)",
    "potencial": "Medio, con advertencia: muchas rupturas son falsas y la estrategia se parece bastante a la número 1; "
                 "no aporta descorrelación si ya tienes el Runner.",
    "siguiente": "Medir correlación contra b01 y probar filtro de volatilidad del rango (rangos estrechos vs anchos).",
}


def correr(sl_atr=4.0, simbolo="USTEC"):
    df = datos.mt5(simbolo, "M15")
    ny = df.index.tz_convert("America/New_York")
    hora = pd.Series(ny.hour + ny.minute / 60, index=df.index)
    dia = pd.Series(ny.normalize(), index=df.index)

    en_rango = (hora >= 9.5) & (hora < 10.0)                     # velas 9:30 y 9:45
    techo = df["high"].where(en_rango).groupby(dia).transform("max")
    piso = df["low"].where(en_rango).groupby(dia).transform("min")
    ventana = (hora >= 10.0) & (hora < 15.0)
    señal = ((df["close"] > techo) & ventana).astype(int) - ((df["close"] < piso) & ventana).astype(int)
    primera = señal.ne(0) & (señal.ne(0).astype(int).groupby(dia).cumsum() == 1)
    entradas = señal.where(primera, 0)
    salida = hora == 15.5                                        # la vela 15:30 cierra a las 15:45
    return motor.por_stops(
        df, entradas, FICHA["id"], sl_atr=sl_atr, trail_atr=None, salida=salida,
        notas=["Stop por ATR en vez de 'al otro lado del rango': el motor v1 solo admite stops en múltiplos de ATR.",
               "Se parece al bot 01 (ruptura + tendencia): revisar la correlación antes de sumarlo a la cartera.",
               "Spread anterior a 2024-04-16 modelado con la mediana (el terminal guarda 0)."],
    )
