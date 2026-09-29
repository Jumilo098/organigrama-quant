"""02 · Reversión a la media en EURGBP — el socio número uno de la tendencia del oro.

Euro y libra son dos vecinos que nunca se alejan mucho: economías muy atadas,
así que el par oscila en rango. El bot compra en el extremo bajo y vende en el
alto esperando el regreso al promedio. Gana seguido y poco; pierde raro pero
fuerte si cambia el régimen (Brexit). Tiende a ganar justo cuando la tendencia
pierde, en mercados laterales.
"""
from nucleo import datos, motor

FICHA = {
    "id": "b02_reversion_eurgbp",
    "nombre": "Reversión a la media en EURGBP (H1)",
    "concepto": "Euro y libra son economías muy atadas: el par oscila en rango. Comprar en el extremo bajo y vender "
                "en el alto esperando el regreso al promedio. Gana seguido y poco; pierde raro pero fuerte si cambia el régimen.",
    "regla": "Z-score del cierre H1 contra su media y desviación de 100 velas. Largo si z < -2, corto si z > 2. "
             "Sale cuando |z| < 0,25, a las 72 velas (3 días) o con stop de 3 ATR(14). Riesgo 1 % por operación.",
    "para_quien": "Cuentas pequeñas en Latinoamérica con CFD desde 500-1.000 USD (spread bajo, stops moderados). "
                  "En EE. UU., con un broker de forex regulado.",
    "datos": "MT5 Exness EURGBP H1 (velas BID + spread real desde 2024-04-16)",
    "potencial": "Alto como complemento: tiende a ganar justo cuando el trend following pierde en mercados laterales. "
                 "Es el socio número uno de seguir la tendencia del oro.",
    "siguiente": "Medir su correlación diaria contra b01; probar filtro de régimen (volatilidad o pendiente de la media "
                 "larga) que apague el bot cuando el par se pone en tendencia.",
}


def correr(n=100, z_in=2.0, z_out=0.25, sl_atr=3.0, max_velas=72):
    df = datos.mt5("EURGBP", "H1")
    c = df["close"]
    z = (c - c.rolling(n).mean()) / c.rolling(n).std()
    entradas = (z < -z_in).astype(int) - (z > z_in).astype(int)
    return motor.por_stops(
        df, entradas, FICHA["id"], sl_atr=sl_atr, trail_atr=None, max_velas=max_velas,
        salida=z.abs() < z_out,
        notas=["Cambio de régimen: el Brexit (2016) es justo el tipo de evento que rompe un par 'de vecinos'; "
               "los datos arrancan en 2017, así que el backtest no ve ese golpe.",
               "Swap no modelado (posiciones de hasta 3 días).",
               "Spread anterior a 2024-04-16 modelado con la mediana (el terminal guarda 0)."],
    )
