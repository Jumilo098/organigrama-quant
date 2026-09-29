"""01 · Trend following sobre XAUUSD — el ancla de la cartera.

Pierde poquito muchas veces y gana grande pocas: sigue la dirección del oro y
deja correr la ganancia con trailing stop. Es la familia del XAU M15 Runner
(que nació del desarrollo de un alumno del Instituto y que auditamos juntos en
clase), pero NO es su código: es una regla genérica de ruptura + trailing para
que sirva de vara de medir. Todo lo demás de la cartera debería elegirse por lo
poco que se parezca a este.
"""
from nucleo import datos, motor

FICHA = {
    "id": "b01_tendencia_oro",
    "nombre": "Tendencia en oro (XAUUSD M15)",
    "concepto": "Seguir la dirección del oro y dejar correr la ganancia con trailing stop. "
                "Acierta 20-35 % de las veces; las ganadoras pagan a las perdedoras.",
    "regla": "Largo si el cierre M15 rompe el máximo de las últimas 96 velas (un día) con la EMA de 800 velas "
             "(~8 días) subiendo; corto al revés. Stop inicial 2 ATR(14), trailing 3 ATR. Riesgo 1 % por operación.",
    "para_quien": "Latinoamérica con CFD desde 1.300-1.500 USD (Monte Carlo de la sesión 20: por debajo, el lote "
                  "mínimo 0,01 sube el riesgo real por encima del plan). EE. UU. con microfuturos de oro (MGC) desde ~10.000 USD.",
    "datos": "MT5 Exness XAUUSD M15 (velas BID + spread real desde 2024-04-16)",
    "potencial": "Alto. Ya hay ~2.700 operaciones de backtest del Runner y telemetría en vivo: es el ANCLA.",
    "siguiente": "Comparar contra el Runner real en operacionesreales.com; medir correlación de cada bot nuevo contra este.",
}


def correr(sl_atr=2.0, trail_atr=3.0, canal=96, ema=800):
    df = datos.mt5("XAUUSD", "M15")
    c = df["close"]
    tendencia = c.ewm(span=ema).mean()
    sube = tendencia > tendencia.shift(96)
    maximo, minimo = df["high"].rolling(canal).max().shift(1), df["low"].rolling(canal).min().shift(1)
    entradas = ((c > maximo) & sube).astype(int) - ((c < minimo) & ~sube).astype(int)
    return motor.por_stops(
        df, entradas, FICHA["id"], sl_atr=sl_atr, trail_atr=trail_atr,
        notas=["Swap no modelado: en XAUUSD el largo paga ~55 USD/lote/noche en Exness; las operaciones de "
               "varios días sobrestiman el resultado de los largos.",
               "Spread anterior a 2024-04-16 modelado con la mediana (el terminal guarda 0).",
               "Equity con riesgo fijo del 1 % sin lote mínimo: ver cartera/lote_minimo.py para la cuenta real."],
    )
