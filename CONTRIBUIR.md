# Cómo contribuir

El valor de este repositorio crece si cada uno empuja una línea distinta en vez de dar vueltas en círculo
sobre la misma. Este es el flujo.

## 1. Tu copia y tu rama

> **Nunca empujes a `main` del repositorio original**, aunque GitHub te lo permita. Todo entra por Pull Request.

```bash
gh repo fork Jumilo098/organigrama-quant --clone     # una sola vez
cd organigrama-quant
git remote -v                                        # 'upstream' = original, 'origin' = tu copia
git checkout -b v2-b02-filtro-volatilidad            # una rama por hipótesis
```

Antes de empezar cada semana, trae lo último del original:

```bash
git fetch upstream && git merge upstream/main
```

## 2. Pre-registro (obligatorio)

Copia `docs/PLANTILLA_V2.md` a `investigacion/<tu-usuario>/<bot>-v2.md` y llénala **antes** de correr el
backtest. Si la escribes después, el resultado no cuenta como evidencia: si ya viste los datos, cualquier hipótesis
se puede acomodar a ellos.

## 3. Un solo cambio por versión

- Cambia **un** parámetro, filtro o regla. Si cambias tres cosas y mejora, no sabrás cuál fue.
- Si quieres probar muchas variantes, usa la fábrica: `python -m fabrica.fabrica b02 --rejilla '{...}'`. Te dirá
  qué Sharpe sacaría el azar con ese número de pruebas.
- **No modifiques `nucleo/`.** Si encuentras un error en el motor, abre un *issue* con el ejemplo mínimo.

## 4. Córrelo y compara

```bash
python correr.py b02 --placebo 100
```

En tu Pull Request pega la tabla de tu `FICHA.md` junto a la de la v1. Lo que importa, en este orden:

1. ¿Mejora **fuera de muestra** (2022+)? Lo de dentro de muestra se puede fabricar.
2. ¿Le gana a los **placebos** (percentil ≥ 95)?
3. ¿Sigue positivo **sin el mejor 3 %** de las operaciones?
4. ¿Tiene al menos **80 operaciones**?

## 5. Pull Request

```bash
git add bots/b02_reversion_eurgbp.py investigacion/
git commit -m "b02 v2: filtro de volatilidad (pre-registro en investigacion/...)"
git push -u origin v2-b02-filtro-volatilidad
gh pr create --repo Jumilo098/organigrama-quant --fill
```

**No subas** `resultados/` en tu PR (se regeneran al integrar), ni nada de `datos/`.

## 6. Nuevo bot (idea número 16)

Crea `bots/b16_<nombre>.py` copiando la estructura de cualquier bot existente: un diccionario `FICHA` con las
claves `id, nombre, concepto, regla, para_quien, datos, potencial, siguiente` y una función `correr()` que
devuelva un `motor.Resultado`. Usa `motor.por_posicion` (rotaciones, pares, horarios) o `motor.por_stops`
(entradas con stop y trailing). Antes de pedir que entre a la cartera, responde la pregunta de la sesión:
**¿baja la correlación media?**

## 7. Forward y sismógrafo

Si tu v2 pasa la vara, el siguiente paso es forward en demo con la niñera al lado. Escribe a
**contacto@juancamilorico.com** con el asunto «Instituto Quant sesión 20 · sismógrafo» y el enlace a tu PR
para que se incluya en el seguimiento de operacionesreales.com.

## Qué nunca va en el repositorio

- Claves de API, tokens, contraseñas, archivos `.env`.
- Números de cuenta, capturas con saldos o datos personales (tuyos o de otros).
- Transcripciones de las sesiones o mensajes de compañeros.
- Datos descargados (`datos/cache/`) — cada uno los baja con el código.
