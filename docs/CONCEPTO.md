# El concepto de la sesión 20: de un bot a una organización

Instituto Quant · sesión 20 (24-sep-2026). Resumen de la propuesta que este repositorio convierte en código.

## 1. Las cuatro fuerzas

Lo que cambió no es un modelo concreto, sino cuatro tendencias que se suman:

1. **Menos costo** por token (y flujos optimizados: «el torno que mejora el torno»).
2. **Más inteligencia**, sobre todo en programación y matemáticas.
3. **Menos latencia**: responder en 20 minutos y no en 72 horas cambia qué vale la pena delegar.
4. **Ventanas de contexto más grandes** y agentes que documentan su propio trabajo en un repo.

Consecuencia (paradoja de Jevons): cuanto más barata la IA, en **más** procesos la usamos. Una
jornada de 8 horas deja de ser una ley física: ya hay flujos que corren 24/7 (en la sesión, uno de
más de 48 horas seguidas).

## 2. De bot a organigrama

> «Deja de operar como un retail, opera como un institucional.»

El trader retail se ha visto como el llanero solitario. Un fondo tiene **analistas, gestores y
auditores**. Hoy una sola persona (una *One Person Company*) puede tener ese organigrama con agentes:

- **Visionario**: tú, con la idea.
- **Operario**: los bots (reglas fijas) y la fábrica que produce variantes.
- **Manager**: niñera, analista, mayordomo y auditor, que vigilan y reasignan.

Ver [`agentes/ROLES.md`](../agentes/ROLES.md).

## 3. Telemetría: separar sensación de señal

El sismógrafo de operacionesreales.com sobre el Runner mostró que un drawdown tiene tres dueños:

- **Estrategia**: la racha mala que el backtest da por normal.
- **Ejecución**: VPS apagada, aperturas fantasma, órdenes rechazadas.
- **Contexto**: broker y tamaño de cuenta. Con ~626 USD y lote mínimo 0,01, el riesgo real era 1,5-3 %
  por operación y no el 1 % del plan. Con 1.300-1.500 USD la ruina a dos años baja 5-8 veces.

Moraleja: antes de tirar el acueducto, busca la fuga. → [`cartera/lote_minimo.py`](../cartera/lote_minimo.py)

## 4. No tengas un bot: ten una cartera descorrelacionada

Dalio: «encuentra 15 buenos flujos de retorno no correlacionados». La matemática
(`cartera/matematica.py`) matiza el número:

- Con correlación media ρ, nunca tendrás más de **1/ρ** apuestas independientes.
- Con ρ = 0,3 (típico de una cartera retail de tendencia + momentum + reversión) el techo es 3,3.
- **Bajar la correlación rinde más que agregar bots**: con 8 bots, pasar de ρ 0,3 a 0,1 lleva el
  multiplicador de ×1,61 a ×2,17; pasar de 8 a 15 bots con ρ 0,3 apenas lo lleva a ×1,70.
- Regla de entrada: un bot nuevo entra solo si `Sharpe_nuevo > ρ(nuevo, cartera) × Sharpe_cartera`.

Veredicto para el Instituto: **empezar con 1-2 bots** (validar edge y ejecución), **punto dulce 5-8**
con 3.000-5.000 USD mezclando instrumentos de lote fino, **15** solo con más de 5.000-7.000 USD y
monitoreo automatizado.

**Taleb + Dalio no se contradicen**: Dalio dice qué hacer con el 90 % (cartera descorrelacionada que
compra supervivencia); Taleb, con el 10 % (apuestas con pérdida acotada y techo abierto: cripto,
volatilidad comprada, bots desechables).

## 5. El mayordomo que abre y cierra llaves

Un bot es una semilla. El **mayordomo** reparte el agua (capital) entre cultivos (bots) según el
clima (régimen), con un reglamento: ninguna llave se cierra del todo, ningún cultivo pasa de un tope.
La estrategia es una cosa; el **tamaño de la asignación** es otra, y puede ser dinámico.
→ [`cartera/mayordomo.py`](../cartera/mayordomo.py)

## 6. La hipótesis nueva: forward con niñera y bots desechables

El método clásico (datos → estrategia → prototipo → backtest dentro y fuera de muestra → forward)
sigue siendo correcto. La pregunta que abre la sesión:

> ¿Qué pasa con sistemas cuyo backtest no es alentador pero el forward sí funciona, si un agente los
> acompaña en tiempo real para acotar el riesgo de ruina?

Y si programar un bot ya no toma un mes sino minutos, un **bot desechable** que explota una ventana
temporal puede ser una pata del 10 % especulativo. Eso es hipótesis, no resultado: la fábrica
(`fabrica/fabrica.py`) viene con la corrección por número de pruebas incorporada.

## 7. La tarea dominó (7 días)

Delega un proceso repetitivo a un agente de la terminal en una máquina o cuenta aislada, pídele que
lo revise en ciclos y que registre cada caso con tu decisión. Al día 7: un flujo que corrió solo al
menos 8 horas y un dataset con 20 casos o más.
