# Prompts para trabajar con Claude Code (u otro modelo en la terminal)

Abre la terminal **dentro de la carpeta del repositorio** y lanza `claude`. El archivo `CLAUDE.md` del repo le
explica a Claude cómo está organizado todo y qué reglas respetar, así que no tienes que repetírselo.

## Para arrancar

**Instalar y correr el primero**
> Acabo de clonar este repositorio. Ayúdame a crear el entorno virtual, instalar `requirements.txt` y correr
> `python correr.py b04 --placebo 20`. Si algo falla, arréglalo y explícame qué pasó en una frase.

**Entender un bot**
> Léeme `bots/b02_reversion_eurgbp.py` y su `resultados/b02_reversion_eurgbp/FICHA.md`. Explícame en lenguaje
> sencillo qué hace la regla, por qué reprobó la v1 y cuáles serían tres hipótesis razonables para una v2.

**Elegir bot según mi caso**
> Tengo ___ USD, vivo en ___, mi broker es ___ y puedo dedicarle ___ horas a la semana. Con `docs/ELEGIR_BOT.md`
> y las fichas de `resultados/`, recomiéndame UN bot para empezar y dime qué necesito para operarlo en demo.

## Para hacer tu v2

**Pre-registro**
> Quiero probar esta idea en el bot b__: ______. Llena conmigo `docs/PLANTILLA_V2.md` y guárdala en
> `investigacion/<mi-usuario>/b__-v2.md`. No corras ningún backtest todavía.

**Implementar el cambio**
> Implementa en `bots/b__....py` solo el cambio descrito en mi pre-registro, sin tocar `nucleo/`. Añade una nota
> en `notas` explicando el cambio. Luego corre `python correr.py b__ --placebo 100` y compara la nueva FICHA
> contra la v1 (está en git: `git show main:resultados/b__.../FICHA.md`).

**Auditar que no mire el futuro**
> Revisa mi versión de `bots/b__....py` buscando sesgo de anticipación: indicadores sin `shift`, datos del
> mismo día usados para decidir ese día, universos elegidos con información de hoy. Dame la lista de riesgos.

**Probar muchas variantes sin engañarme**
> Usa `python -m fabrica.fabrica b__ --rejilla '{"param": [..]}'` con estas variantes y explícame el umbral de
> Sharpe por azar que reporta y si alguna lo supera de verdad fuera de muestra.

## Para la cartera

> Con `python -m cartera.mayordomo --bots b01 b__ b__`, dime la correlación media, el N efectivo y si agregar
> b__ a mi cartera la mejora según la regla de la sesión (Sharpe nuevo > correlación × Sharpe cartera).

> Tengo una cuenta de ___ USD y mi peor pérdida con el lote mínimo fue de ___ USD. Con
> `python -m cartera.lote_minimo`, ¿cuántos bots puedo sostener respetando un 2 % de riesgo de cartera?

## Para la tarea dominó (7 días)

> Quiero delegar este proceso que repito cada semana: ______. Diséñame un flujo para que un agente lo revise
> cada ___ minutos en una máquina aislada y registre cada caso con mi decisión en un CSV. Al día 7 quiero un
> dataset de al menos 20 casos. Empieza por lo mínimo que funcione.

## Para ahorrar tokens (el torno que mejora el torno)

> Este flujo ya funciona pero consume muchos tokens: ______. Audítalo y propón qué partes pueden pasar a un
> script de Python que se escribe una vez, dejando al modelo solo lo que requiere interpretar.
