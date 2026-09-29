# Instrucciones para Claude Code en este repositorio

Este es el laboratorio de la **sesión 20 del Instituto Quant**: 15 bots de trading como prototipos v1 de
investigación, un motor de backtest común y la capa de cartera/agentes. Quien te habla es un alumno del
Instituto; muchos no son programadores. Responde en español, en lenguaje sencillo, y explica en una frase lo
que hiciste.

## Reglas que no se rompen

1. **Nada de dinero real.** No escribas código que envíe órdenes a una cuenta real. La niñera de IBKR es de
   solo lectura y solo acepta cuentas paper (prefijo `D`, puerto 7497); no quites esas protecciones.
2. **No modifiques `nucleo/`** salvo que el alumno lo pida explícitamente para reportar un error. Es la vara
   común: si cambia, los resultados dejan de ser comparables.
3. **Un cambio por versión.** Si el alumno pide varios cambios a la vez, propón separarlos en versiones.
4. **Pre-registro primero.** Antes de correr el backtest de una v2, asegúrate de que exista su pre-registro en
   `investigacion/<usuario>/` (plantilla en `docs/PLANTILLA_V2.md`).
5. **Cero sesgo de anticipación.** Toda señal se decide con datos hasta el cierre de la vela y se ejecuta en la
   siguiente. Revisa `shift`, universos y fechas antes de dar un resultado por bueno.
6. **Nunca subas** claves, tokens, `.env`, números de cuenta ni datos personales. `datos/` está en `.gitignore`.
7. **Honestidad con los números.** No optimices parámetros para que el resultado salga bonito. Si un bot
   reprueba, dilo. Reporta siempre fuera de muestra, placebo y el recorte del mejor 3 %.

## Cómo está organizado

- `bots/bNN_*.py`: cada bot expone `FICHA` (dict con id, nombre, concepto, regla, para_quien, datos,
  potencial, siguiente) y `correr(**params) -> nucleo.motor.Resultado`.
- `nucleo/motor.py`: `por_posicion` (posición objetivo en [-1, 1] al cierre) y `por_stops` (entradas con stop
  y trailing ATR, recorrido intrabarra adverso primero, equity marcada a mercado diaria).
- `nucleo/metricas.py`: corte dentro/fuera de muestra en 2022-01-01, placebo, sin top 3 %, mínimo 80
  operaciones y el veredicto.
- `correr.py`: `python correr.py [prefijos] [--placebo N]` regenera `resultados/`.
- `cartera/`: `matematica.py` (N efectivo), `lote_minimo.py`, `mayordomo.py` (reasignación de pesos).
- `agentes/`: `ninera_ibkr.py` y los prompts del analista y del árbitro.
- `fabrica/fabrica.py`: rejilla de variantes con umbral de Sharpe por azar.

## Datos

- MT5 (solo Windows): velas BID con spread real desde 2024-04-16 (antes, mediana modelada). Ruta del terminal
  en la variable `MT5_TERMINAL`; los sufijos de símbolo se detectan solos.
- yfinance: acciones, ETFs, futuros continuos, índices y cripto diarios.
- Todo se cachea en `datos/cache/`.

## Créditos

El XAU M15 Runner nació del desarrollo de un alumno del Instituto y se auditó en clase; `b01` NO es su
código. No atribuyas su autoría a nadie en concreto.
