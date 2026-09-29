"""11 · Arbitraje estadístico de pares — apostar a que dos gemelos vuelven a juntarse.

Toma dos activos que se mueven juntos y, cuando el diferencial se abre, compra
el rezagado y vende el adelantado. El resultado casi no depende de si el
mercado sube o baja. Ideal para la fábrica de bots: la IA puede escanear
cientos de pares. El riesgo es que la relación se rompa para siempre.
"""
import numpy as np
import pandas as pd

from nucleo import datos, motor

FICHA = {
    "id": "b11_pares",
    "nombre": "Arbitraje estadístico de pares",
    "concepto": "Dos gemelos (oro y plata, Coca-Cola y Pepsi...) que se separan tienden a volver a juntarse: "
                "comprar el rezagado y vender el adelantado, neutral al mercado.",
    "regla": "Beta por regresión rodante de 120 días entre log-precios (solo datos pasados). Diferencial = logA - beta·logB; "
             "z-score de 60 días. Entra si |z| > 2 (largo el barato, corto el caro), sale cuando z cruza 0, "
             "stop si |z| > 4 o a los 30 días. Pares: GLD/SLV, KO/PEP, XOM/CVX, EWA/EWC.",
    "para_quien": "Desde 5.000 USD en Interactive Brokers con ventas en corto, o cuentas pequeñas con CFD en "
                  "Latinoamérica que permitan operar ambos lados.",
    "datos": "yfinance diarios ajustados GLD, SLV, KO, PEP, XOM, CVX, EWA, EWC",
    "potencial": "Medio-alto como descorrelacionador. Ideal para la fábrica de bots (la IA puede escanear cientos de "
                 "pares). El riesgo: que la relación entre los gemelos se rompa para siempre.",
    "siguiente": "Escanear pares con la fábrica y exigir que sobrevivan fuera de muestra con corrección por múltiples pruebas.",
}

PARES = [("GLD", "SLV"), ("KO", "PEP"), ("XOM", "CVX"), ("EWA", "EWC")]


def _par(a, b, ventana_beta, ventana_z, entrada, stop, max_dias, costo):
    tabla = datos.yf_cierres([a, b], "2006-01-01").dropna()
    la, lb = np.log(tabla[a]), np.log(tabla[b])
    beta = la.rolling(ventana_beta).cov(lb) / lb.rolling(ventana_beta).var()
    dif = la - beta * lb
    z = (dif - dif.rolling(ventana_z).mean()) / dif.rolling(ventana_z).std()

    # máquina de estados al cierre: +1 = largo A / corto B ; -1 = corto A / largo B
    pos = np.zeros(len(z))
    estado, dias = 0.0, 0
    for i, zi in enumerate(z.to_numpy()):
        if not np.isfinite(zi):
            estado, dias = 0.0, 0
        elif estado == 0:
            if zi > entrada:
                estado, dias = -1.0, 0
            elif zi < -entrada:
                estado, dias = 1.0, 0
        else:
            dias += 1
            cruzo = (estado > 0 and zi >= 0) or (estado < 0 and zi <= 0)
            if cruzo or abs(zi) > stop or dias >= max_dias:
                estado, dias = 0.0, 0
        pos[i] = estado
    pos = pd.Series(pos, index=z.index)

    # "precio" sintético del diferencial con la beta de AYER (conocida), bruto normalizado a 1
    ra, rb = tabla[a].pct_change(), tabla[b].pct_change()
    b_ayer = beta.shift(1)
    r_dif = ((ra - b_ayer * rb) / (1 + b_ayer.abs())).fillna(0)
    sintetico = (1 + r_dif).cumprod()
    return motor.por_posicion(sintetico, pos, f"b11_{a}_{b}", costo_lado=costo)


def correr(ventana_beta=120, ventana_z=60, entrada=2.0, stop=4.0, max_dias=30):
    # 2 patas x ~3 pb = ~6 pb por lado del diferencial
    patas = [_par(a, b, ventana_beta, ventana_z, entrada, stop, max_dias, 0.0006) for a, b in PARES]
    res = motor.combinar(patas, FICHA["id"])

    def _pl(s):
        return pd.concat([p.placebo(s + 31 * i) for i, p in enumerate(patas)], axis=1).fillna(0).mean(axis=1)

    res.placebo = _pl
    res.notas = [
        "Costo del corto (préstamo de acciones) no modelado; en ETFs líquidos suele ser bajo, en pares exóticos no.",
        "Beta variable día a día: el rebalanceo diario de la cobertura real costaría algo más que lo modelado.",
        "Los pares se eligieron a mano por intuición económica, no por escaneo; aun así hay sesgo de "
        "supervivencia (sabemos hoy que siguen existiendo y relacionados).",
        "Riesgo de ruptura de régimen: si la relación se rompe, el stop a |z| > 4 corta pero no evita la pérdida.",
    ]
    return res
