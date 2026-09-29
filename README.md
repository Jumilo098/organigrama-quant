# Organigrama Quant · 15 bots v1 + los agentes que los acompañan

Instituto Quant · **sesión 20** (24-sep-2026). Lo prometido en clase: *«un prototipo de cada uno de estos,
con su respectivo backtest, entregado en un repositorio, para que de esta lista puedan escoger los que tengan
más sentido para ustedes»*.

> ⚠️ **Todo aquí es investigación.** Son prototipos v1 con parámetros de manual, no sistemas para dinero
> real ni recomendaciones de inversión. Un veredicto «candidato» significa «merece forward en demo», nada más.

## La idea en una línea

No pienses en un bot: piensa en una **organización**. Bots deterministas y descorrelacionados (las semillas)
+ agentes que los vigilan y reparten el capital (la niñera, el analista, el mayordomo). El porqué está en
[`docs/CONCEPTO.md`](docs/CONCEPTO.md).

## Qué hay dentro

| Carpeta | Qué es |
|---|---|
| [`bots/`](bots/) | Los 15 prototipos v1. Cada módulo trae su `FICHA` (concepto, para quién, potencial) y `correr()` |
| [`nucleo/`](nucleo/) | Motor de backtest común, datos con caché y la vara de medir (misma para todos) |
| [`resultados/`](resultados/) | Ficha, curva de equity, operaciones y retornos diarios de cada bot + [`TABLA.md`](resultados/TABLA.md) |
| [`cartera/`](cartera/) | Matemática de la cartera descorrelacionada, lote mínimo y el **mayordomo** que reasigna pesos |
| [`agentes/`](agentes/) | Roles del organigrama: niñera de IBKR (solo lectura, paper), prompts del analista y del árbitro |
| [`fabrica/`](fabrica/) | La fábrica de bots desechables, con la corrección por número de pruebas |
| [`docs/`](docs/) | El concepto de la sesión |

## Los 15 bots y su veredicto v1

| Bot | Idea | Operaciones | Sharpe total | Sharpe fuera de muestra | DD máx. | Placebo (percentil) | Veredicto v1 |
|---|---|---|---|---|---|---|---|
| [b01_tendencia_oro](resultados/b01_tendencia_oro/FICHA.md) | Tendencia en oro (XAUUSD M15) | 1979 | 0.52 | 1.05 | -46.1 % | 98.00 | **PROMETEDOR, NO VALIDADO** |
| [b02_reversion_eurgbp](resultados/b02_reversion_eurgbp/FICHA.md) | Reversión a la media en EURGBP (H1) | 1180 | 0.04 | -0.06 | -32.4 % | 100.00 | **REPROBADO v1** |
| [b03_tokio_jpy](resultados/b03_tokio_jpy/FICHA.md) | Tokio empuja, Londres devuelve (USDJPY M15) | 372 | -0.12 | 0.15 | -13.3 % | 54.00 | **DÉBIL** |
| [b04_momentum_acciones](resultados/b04_momentum_acciones/FICHA.md) | Momentum mensual (ETFs de sectores, países y activos) | 239 | 0.57 | 0.84 | -28.9 % | 97.00 | **CANDIDATO A FORWARD** |
| [b05_value_fundamental](resultados/b05_value_fundamental/FICHA.md) | Value fundamental (proxy con ETFs value/growth + escáner forward) | 14 | 0.51 | 0.77 | -60.3 % | 42.00 | **MUESTRA INSUFICIENTE** |
| [b06_insiders](resultados/b06_insiders/FICHA.md) | Compras de insiders con dinero propio (formulario 4) | 452 | -0.17 | -0.41 | -75.2 % | 19.00 | **REPROBADO v1** |
| [b07_eventos_resultados](resultados/b07_eventos_resultados/FICHA.md) | Deriva post-resultados (8-K de la SEC, 40 large caps) | 562 | 0.36 | 0.22 | -39.4 % | 99.00 | **DÉBIL** |
| [b08_volatilidad](resultados/b08_volatilidad/FICHA.md) | Vender / comprar miedo (proxy VIX sobre SPY, barbell 90/10) | 363 | 0.49 | 0.49 | -31.3 % | 77.00 | **DÉBIL** |
| [b09_cripto_momentum](resultados/b09_cripto_momentum/FICHA.md) | Momentum en cripto (BTC + ETH H4) | 476 | 1.48 | 1.04 | -7.7 % | 99.00 | **CANDIDATO A FORWARD** |
| [b10_estacionalidad_commodities](resultados/b10_estacionalidad_commodities/FICHA.md) | Estacionalidad en materias primas (futuros) | 307 | 0.26 | 0.13 | -28.7 % | 62.00 | **DÉBIL** |
| [b11_pares](resultados/b11_pares/FICHA.md) | Arbitraje estadístico de pares | 310 | -0.48 | -0.96 | -27.5 % | 4.00 | **REPROBADO v1** |
| [b12_overnight](resultados/b12_overnight/FICHA.md) | Efecto overnight (SPY + QQQ) | 6724 | 0.17 | 0.06 | -41.3 % | 98.00 | **DÉBIL** |
| [b13_ruptura_apertura](resultados/b13_ruptura_apertura/FICHA.md) | Ruptura del rango de apertura (USTEC M15) | 1774 | 0.10 | 0.61 | -33.7 % | 78.00 | **DÉBIL** |
| [b14_cross_asset](resultados/b14_cross_asset/FICHA.md) | Señal cruzada: dólar y tasas → oro; Nikkei → yen (D1) | 589 | 0.10 | 0.39 | -16.3 % | 81.00 | **DÉBIL** |
| [b15_datos_alternativos](resultados/b15_datos_alternativos/FICHA.md) | Datos alternativos (Polymarket → BTC) | 0 | — | — | — | — | **MUESTRA INSUFICIENTE** |

### La cartera: el punto de la sesión, en números

`python -m cartera.mayordomo` junta los 10 bots que no reprobaron ni tienen muestra insuficiente, cada uno llevado a
la misma volatilidad, en el periodo común (jul-2019 → sep-2026):

| Cartera | Sharpe | CAGR | DD máx. | Ruina (−50 % en 2 años) |
|---|---|---|---|---|
| Temporizador (pesos fijos) | 1,20 | 25,7 % | −29,6 % | 0,0 % |
| Mayordomo de reglas v1 | 1,04 | 21,5 % | −33,7 % | 0,0 % |

*(las dos escaladas a 20 % de volatilidad anual para compararlas a igual riesgo)*

- **Bots mediocres por separado, cartera sólida junta.** Casi ninguno pasa de Sharpe 0,5 solo; con correlación media
  **0,03** equivalen a **7,7 apuestas independientes de 10** y la cartera sube a Sharpe 1,20. Es exactamente lo de Dalio.
- **Ojo con el sesgo de selección:** la cartera se armó con los bots que no reprobaron *en este mismo backtest*. El
  número honesto llegará con el forward.
- **El mayordomo de reglas v1 NO se gana el sueldo:** mover las llaves con este reglamento le resta a los pesos fijos.
  Ese es el listón para la versión con agente (`agentes/PROMPT_ARBITRO.md`): si no le gana al temporizador después de
  costos, no aporta.


**Cómo leer la tabla.** Cada bot pasa por la misma vara ([`nucleo/metricas.py`](nucleo/metricas.py)):
Sharpe dentro de muestra (antes de 2022) y fuera de muestra (2022 en adelante), **placebo** (la misma
gestión con entradas al azar o la posición desplazada en el tiempo: si el placebo gana igual, la señal no
aporta), resultado **sin el mejor 3 %** de las operaciones y **muestra mínima de 80 operaciones**.

- **CANDIDATO A FORWARD**: pasa los cinco controles → merece demo con la niñera al lado.
- **PROMETEDOR, NO VALIDADO**: positivo fuera de muestra y pasa placebo o el recorte del 3 %, pero no todo.
- **DÉBIL**: positivo fuera de muestra sin más respaldo.
- **MUESTRA INSUFICIENTE**: menos de 30 operaciones; no se puede juzgar todavía.
- **REPROBADO v1**: esta versión no funciona. La idea puede seguir viva en una v2.

Recuerda la tasa del almacén de hallazgos: ~1 de cada 10 hipótesis sobrevive. Que la mayoría repruebe es
lo esperado, y es información.

## Cómo usarlo

```bash
pip install -r requirements.txt
python correr.py                    # los 15 (descarga datos la primera vez; MT5 abierto para los de CFD)
python correr.py b02 b11            # solo algunos
python correr.py --placebo 30       # más rápido
python -m cartera.matematica        # tabla de Dalio: N bots × correlación
python -m cartera.lote_minimo --perdida 18.51 --riesgo 0.02
python -m cartera.mayordomo         # temporizador vs. mayordomo sobre los bots no reprobados
python -m fabrica.fabrica b02 --rejilla '{"umbral_z":[1.5,2,2.5]}'
python -m agentes.ninera_ibkr --simbolos SPY GLD --cada 20   # TWS paper en el puerto 7497
```

En Windows, si la consola se queja de caracteres, antes: `set PYTHONUTF8=1`.

**Datos.** Los bots de CFD (oro, EURGBP, USDJPY, índices, cripto) leen velas de MetaTrader 5 (Exness): son
velas BID y el spread real solo viene informado desde el 16-abr-2024 (antes se modela con la mediana). Los de
acciones, ETFs y futuros usan yfinance. Todo se guarda en `datos/cache/` (fuera de git).

## Cómo contribuir (la línea de investigación)

1. Escoge **un** bot de la tabla que encaje con tu capital, tu país y tu broker (lo dice su ficha).
2. Primero infraestructura: que abra y cierre una posición en tu broker demo, aunque sea con entrada aleatoria.
3. Haz la v2 en una rama: cambia **una** cosa, córrela con `correr.py` y compara contra la v1.
4. Si pasa la vara, al forward en demo con la niñera registrando la ejecución, y escríbele a
   contacto@juancamilorico.com para incluirlo en el sismógrafo de operacionesreales.com.
5. Antes de sumar un bot a tu cartera, pregunta si **baja la correlación media**. Si no la baja, casi seguro
   no vale el capital ni la atención.

## Créditos y procedencia

- El **XAU M15 Runner**, que nació del desarrollo de un alumno del Instituto y que auditamos juntos en clase,
  es el ancla con la que se compara todo. El bot `b01` **no es su código**: es una regla genérica de la misma
  familia para usarla de vara.
- Ideas de cartera: Ray Dalio (flujos descorrelacionados) y Nassim Taleb (barra 90/10).
- Los números del lote mínimo y del Monte Carlo del Runner salen de la sesión 20.
