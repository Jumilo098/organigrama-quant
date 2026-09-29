"""03 · Tokyo Reversal en USDJPY — lo que Tokio empuja, Londres lo devuelve.

Aprovecha un patrón de horario: los movimientos del yen en la sesión asiática
tienden a revertirse cuando abre Europa. Opera de noche para América, mientras
uno duerme. Anomalía estrecha, que se degrada y que el Banco de Japón puede
romper; a cambio, muy poco relacionada con el oro.
"""
import pandas as pd

from nucleo import datos, motor

FICHA = {
    "id": "b03_tokio_jpy",
    "nombre": "Tokio empuja, Londres devuelve (USDJPY M15)",
    "concepto": "Los movimientos del yen en la sesión asiática tienden a revertirse al abrir Europa. "
                "El bot opera en contra del empuje de Tokio cuando entra Londres.",
    "regla": "Movimiento asiático = cierre 06:45 − apertura 00:00 UTC. Si supera 0,5 ATR diario (14 días, del día "
             "anterior), a las 07:00 UTC entra en contra. Sale a las 12:00 UTC o con stop de 8 ATR(14) M15. Riesgo 1 %.",
    "para_quien": "Cuentas pequeñas con CFD en Latinoamérica, con VPS: la sesión cae de noche en América y el bot "
                  "opera mientras duermes.",
    "datos": "MT5 Exness USDJPY M15 (hora del servidor = UTC; velas BID + spread real desde 2024-04-16)",
    "potencial": "Medio. Las anomalías de horario son estrechas, se degradan y las intervenciones del Banco de Japón "
                 "pueden romperlas. A cambio, es muy poco correlacionado con el oro.",
    "siguiente": "Cruzar con el caso del fixing gotobi (repo tokio-reversal-caso) y separar días gotobi / no gotobi.",
}


def correr(umbral_atr=0.5, sl_atr=8.0):
    df = datos.mt5("USDJPY", "M15")
    hora = df.index.hour + df.index.minute / 60
    dia = df.index.normalize()

    diario = df.resample("1D").agg({"open": "first", "high": "max", "low": "min", "close": "last"}).dropna()
    atr_d = datos.atr(diario, 14).shift(1)                       # solo días completos anteriores
    apertura_asia = df["open"].where(hora == 0).groupby(dia).transform("first")
    movimiento = df["close"] - apertura_asia
    atr_hoy = pd.Series(atr_d.reindex(dia).to_numpy(), index=df.index)

    en_hora = hora == 6.75                                       # la vela 06:45 cierra a las 07:00
    fuerte = movimiento.abs() > umbral_atr * atr_hoy
    entradas = (-(movimiento.apply(lambda x: 1 if x > 0 else -1)) * (en_hora & fuerte)).astype(int)
    salida = pd.Series(hora == 11.75, index=df.index)            # cierra en la apertura de las 12:00
    return motor.por_stops(
        df, entradas, FICHA["id"], sl_atr=sl_atr, trail_atr=None, salida=salida,
        notas=["Versión genérica: el caso del fixing de Tokio (09:55 JST, días gotobi) vive en el repo "
               "tokio-reversal-caso con su propia auditoría; este v1 no distingue días gotobi.",
               "Horario fijo en UTC: Londres abre a las 07:00 UTC en verano y 08:00 UTC en invierno; el v1 no "
               "ajusta el horario de verano británico.",
               "Spread anterior a 2024-04-16 modelado con la mediana; el spread asiático real suele ser más ancho."],
    )
