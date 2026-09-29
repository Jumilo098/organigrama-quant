"""09 · Cripto momentum — tendencia en un mercado que nunca duerme.

La misma lógica del bot 01 aplicada a Bitcoin (y Ethereum como segunda pata)
en velas de 4 horas, 24/7. Pertenece al 10 % especulativo de la barra de Taleb,
no al 90 % que compra supervivencia.
"""
from nucleo import datos, motor

FICHA = {
    "id": "b09_cripto_momentum",
    "nombre": "Momentum en cripto (BTC + ETH H4)",
    "concepto": "Tendencia en un mercado 24/7: entrar cuando BTC o ETH rompen su rango con la tendencia de fondo a favor "
                "y dejar correr con trailing stop. Pocas ganadoras muy grandes pagan muchas pérdidas pequeñas.",
    "regla": "Velas H4. Largo si el cierre rompe el máximo de las últimas 30 velas (5 días) con la EMA de 300 velas "
             "(~50 días) subiendo; corto al revés. Stop inicial 2,5 ATR(14), trailing 4 ATR. Riesgo 1 % por operación. "
             "Cartera 50/50 BTC y ETH.",
    "para_quien": "Cualquiera, desde cualquier país con acceso a cripto, incluso con 250 USD por la volatilidad — "
                  "pero solo con el capital que se pueda perder.",
    "datos": "MT5 Exness BTCUSD y ETHUSD H4 (velas BID + spread real desde 2024-04-16)",
    "potencial": "Alto en retorno y alto en ruina. Encaja en el 10 % especulativo, no en el 90 %. "
                 "En crisis tiende a correlacionarse con los otros bots de tendencia.",
    "siguiente": "Medir su correlación con b01 en días de tormenta (no solo la media) antes de sumarlo a la cartera.",
}


def _una(simbolo, canal, ema, sl_atr, trail_atr):
    df = datos.mt5(simbolo, "H4")
    c = df["close"]
    tendencia = c.ewm(span=ema).mean()
    sube = tendencia > tendencia.shift(canal)
    maximo, minimo = df["high"].rolling(canal).max().shift(1), df["low"].rolling(canal).min().shift(1)
    entradas = ((c > maximo) & sube).astype(int) - ((c < minimo) & ~sube).astype(int)
    return motor.por_stops(df, entradas, f"b09_{simbolo}", sl_atr=sl_atr, trail_atr=trail_atr, anual=365)


def correr(canal=30, ema=300, sl_atr=2.5, trail_atr=4.0):
    patas = [_una(s, canal, ema, sl_atr, trail_atr) for s in ("BTCUSD", "ETHUSD")]
    res = motor.combinar(patas, FICHA["id"])
    res.anual = 365
    res.placebo = (lambda s: (patas[0].placebo(s).add(patas[1].placebo(s), fill_value=0) / 2))
    res.extra = {"R_medio_BTC": patas[0].extra["R_medio"], "R_medio_ETH": patas[1].extra["R_medio"]}
    res.notas = [
        "Contexto de la sesión 20 (NO es resultado de este bot): el caso azar hizo +434 % en 72 días con un "
        "drawdown del 64 %. Ese es el perfil de riesgo de la familia.",
        "Swap/financiación de los CFD cripto no modelado: en posiciones de varios días resta.",
        "Spread anterior a 2024-04-16 modelado con la mediana (el terminal guarda 0).",
        "ETH empieza en 2018-02; antes de esa fecha la pata ETH suma 0 (la cartera va al 50 % invertida).",
        "En crisis la correlación con b01 y otros bots de tendencia sube: medirla en los peores días.",
        "ANTES de creerse el veredicto: el laboratorio BTC del proyecto ORO (18 familias, arnés con comisión Raw "
        "3,5 USD/lote/lado y slippage 0,05 % en cada fill) encontró que en su mejor candidato el placebo ganaba más "
        "que la señal. Este v1 corre sin comisión ni slippage extra: repetirlo en ese arnés es el siguiente paso.",
    ]
    return res
