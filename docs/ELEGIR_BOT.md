# ¿Qué bot encaja contigo?

Elige por tu **contexto real** (capital, país, broker, tiempo), no por el Sharpe de la tabla. Un bot bueno en
un broker que no puedes usar, o con un capital que no tienes, es un bot que no vas a poder operar bien: es lo
que enseñó el sismógrafo del Runner con el lote mínimo.

## Por perfil

| Si tú… | Mira primero | Por qué |
|---|---|---|
| Estás en Latinoamérica con CFD y **menos de 1.000 USD** | **b02** (EURGBP), **b03** (yen), **b09** (cripto, solo el 10 % especulativo) | Spread bajo o posiciones pequeñas; el oro exige más cuenta por el lote mínimo |
| Estás en Latinoamérica con CFD y **1.300-3.000 USD** | **b01** (oro) + un descorrelacionado (**b02** o **b03**) | El ancla más su socio natural: la reversión gana cuando la tendencia pierde |
| Tienes **Interactive Brokers desde 5.000 USD** | **b04** (momentum ETFs), **b06** (insiders), **b11** (pares) | Acciones y ETFs, rebalanceo lento, datos gratuitos |
| Estás en **EE. UU.** con capital pequeño | **b12** (overnight con ETF o nanofuturos), **b13** (ruptura con MES/MNQ) | Instrumentos finos sin CFD |
| Eres **inversionista de largo plazo** | **b04**, **b05** (value, con Profeta) | Operan una vez al mes o menos |
| Te interesan las **opciones** | **b08** (volatilidad) | El disparador sale de las opciones, aunque la entrada vaya a otro instrumento |
| Te gusta **explorar datos raros** | **b15** (Polymarket / sentimiento), **b07** (resultados) | Mayor varianza: donde más posibilidad hay de un edge propio… y de ruido |
| Operas **materias primas** | **b10** (estacionalidad) | Muy descorrelacionado, pocas operaciones: mejor como filtro de otro bot |
| No sabes todavía | Lee `docs/CONCEPTO.md` y escríbenos (abajo) | Primero la hoja de ruta, luego el bot |

## Los 15 en una línea

| Bot | Idea | Capital orientativo | Veredicto v1 |
|---|---|---|---|
| b01 | Tendencia en oro con trailing (familia del Runner) | CFD 1.300-1.500 USD · MGC ~10.000 | Prometedor |
| b02 | Reversión a la media EUR/GBP | CFD 500-1.000 | Reprobado |
| b03 | Tokio empuja, Londres devuelve (yen) | CFD pequeño + VPS | Débil |
| b04 | Momentum mensual en ETFs | IBKR ~5.000 | **Candidato** |
| b05 | Value: buenos negocios baratos | cualquiera | Muestra insuficiente (proxy) |
| b06 | Seguir compras de directivos (Form 4) | IBKR 2.000-5.000 | Reprobado |
| b07 | Deriva tras resultados trimestrales | intermedio | Débil |
| b08 | Comprar/vender miedo (VIX vs. realizada) | opciones 5.000-10.000 | Débil (proxy) |
| b09 | Tendencia en BTC + ETH | desde 250 (10 % especulativo) | **Candidato** (ver advertencias) |
| b10 | Estacionalidad en materias primas | microfuturos / CFD | Débil |
| b11 | Pares (oro/plata, KO/PEP…) | IBKR 5.000 con cortos | Reprobado |
| b12 | La bolsa gana de noche | ETF o nanofuturos, pequeño | Débil |
| b13 | Ruptura del rango de apertura (Nasdaq) | CFD pequeño · MNQ | Débil |
| b14 | Un mercado para operar otro (DXY/tasas → oro) | cualquiera | Débil |
| b15 | Datos que casi nadie mira (Polymarket) | pequeño, especulativo | Muestra insuficiente |

«Reprobado» es de **esta v1**, no de la idea. Muchas de las mejores líneas de investigación empiezan en un
reprobado bien documentado.

## Antes de sumar un segundo bot

Pregúntate si **baja la correlación media** de lo que ya tienes. Compruébalo con
`python -m cartera.mayordomo --bots b01 b02` (imprime la correlación y el N efectivo). Si no la baja, casi
seguro no vale el capital ni la atención.

## ¿Ninguno encaja?

Escribe a **contacto@juancamilorico.com** con el asunto «Instituto Quant sesión 20 · hoja de ruta», contando
tu capital, tu país, tu broker y tus objetivos. Se cruza con la sesión para diseñarte un plan a la medida.
