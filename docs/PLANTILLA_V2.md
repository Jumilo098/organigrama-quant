# Pre-registro de una v2

> Llena esto ANTES de correr el backtest. Guárdalo en `investigacion/<tu-usuario>/<bot>-v2.md`.

**Bot:** b__
**Autor (usuario de GitHub):**
**Fecha del pre-registro:**

## 1. Hipótesis (una frase)

«Si ______, entonces ______ porque ______.»

## 2. El único cambio frente a la v1

- Qué cambia (parámetro, filtro o regla):
- Valor v1 → valor v2:

## 3. Qué resultado me haría descartarla

(Escríbelo en números. Ej.: «si el Sharpe fuera de muestra no supera 0,3 o el placebo queda por debajo del
percentil 90, la descarto».)

## 4. Contexto de ejecución

- Broker e instrumento donde lo operaría:
- Capital con el que lo operaría:
- ¿Con ese capital el lote mínimo respeta mi riesgo por operación? (`python -m cartera.lote_minimo --perdida <X>`)

## 5. Resultado (llenar DESPUÉS)

| Métrica | v1 | v2 |
|---|---|---|
| Sharpe fuera de muestra | | |
| Placebo (percentil) | | |
| Suma sin el mejor 3 % | | |
| Operaciones | | |
| Veredicto | | |

**¿Se cumplió el criterio de descarte del punto 3?** Sí / No

**Qué aprendí (aunque haya reprobado):**
