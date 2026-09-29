# Empieza aquí (30-45 minutos)

Bienvenido al laboratorio de la sesión 20. Esta guía te lleva de cero a tener tu primer bot corriendo en tu
computadora y tu primera versión propia (v2) lista para compartir.

> No necesitas saber programar. Necesitas saber pedir. Cada paso trae el comando exacto y, si algo falla, el
> prompt para que Claude (u otro modelo) lo arregle por ti. Ver [`docs/PROMPTS.md`](docs/PROMPTS.md).

---

## Paso 0 · Cuenta de GitHub

Necesitas una cuenta de GitHub (gratis en https://github.com/signup, idealmente con el **mismo correo** con el que
te inscribiste al Instituto). Si te llegó una invitación al repositorio, acéptala en
https://github.com/Jumilo098/organigrama-quant/invitations.

## Paso 1 · Instala lo necesario (una sola vez)

| Qué | Windows | Mac |
|---|---|---|
| **Python 3.11 o 3.12** | https://www.python.org/downloads/ (marca *Add Python to PATH*) | `brew install python@3.12` |
| **Git** | https://git-scm.com/download/win | viene con las *Command Line Tools* (`xcode-select --install`) |
| **GitHub CLI** (recomendado) | `winget install GitHub.cli` | `brew install gh` |
| **Claude Code** (recomendado) | https://claude.com/claude-code | igual |
| **MetaTrader 5** (solo para los bots de CFD) | tu broker (Exness u otro) | ⚠️ el paquete de Python de MT5 **solo funciona en Windows** |

Comprueba en una terminal:

```bash
python --version      # 3.11 o 3.12
git --version
gh auth login         # inicia sesión en GitHub desde la terminal
```

## Paso 2 · Descarga el repositorio

Como **no tienes permiso de escritura** en el repositorio original, trabajas sobre **tu propia copia** (fork):

```bash
gh repo fork Jumilo098/organigrama-quant --clone
cd organigrama-quant
```

(Sin `gh`: botón **Fork** en GitHub y luego `git clone https://github.com/<tu-usuario>/organigrama-quant.git`.)

## Paso 3 · Crea tu entorno e instala dependencias

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Mac:
source .venv/bin/activate

pip install -r requirements.txt
```

En Windows, si ves errores de caracteres raros en la consola: `set PYTHONUTF8=1` (o `$env:PYTHONUTF8=1` en PowerShell).

## Paso 4 · Corre tu primer bot

Empieza por uno que **no necesita MetaTrader** (usa datos gratuitos de Yahoo Finance):

```bash
python correr.py b04 --placebo 20
```

Tarda uno o dos minutos la primera vez (descarga datos a `datos/cache/`). Al terminar abre
`resultados/b04_momentum_acciones/FICHA.md`: ahí está el veredicto, la tabla dentro/fuera de muestra y la curva.

**Bots que funcionan sin MT5 (cualquier sistema):** b04, b05, b06, b07, b08, b10, b11, b12 y b14 (parte).
**Bots que necesitan MT5 abierto (Windows):** b01, b02, b03, b09, b13 y b14 (pata oro/yen).

Para los de MT5: abre tu terminal, inicia sesión (una **demo** sirve) y corre `python correr.py b01`.
Si tu terminal no está en la ruta por defecto:

```bash
set MT5_TERMINAL=C:\Ruta\a\tu\terminal64.exe      # Windows cmd
```

Los símbolos con sufijo (`XAUUSDm`, `EURGBP.` …) se detectan solos.

> Si no puedes correr un bot de MT5, **igual puedes estudiarlo**: sus resultados ya están en `resultados/`.

## Paso 5 · Escoge TU bot

Lee [`docs/ELEGIR_BOT.md`](docs/ELEGIR_BOT.md): una tabla por capital, país y broker. La regla de la sesión:
**uno a la vez**, el que encaje con tu contexto real, no el que tenga el Sharpe más alto.

## Paso 6 · Haz tu v2

1. Crea una rama: `git checkout -b v2-b04-mi-idea`
2. Copia la plantilla de pre-registro [`docs/PLANTILLA_V2.md`](docs/PLANTILLA_V2.md) y **escribe tu hipótesis
   ANTES de correr nada** (qué cambias, por qué, qué resultado la refutaría).
3. Cambia **una sola cosa** en el bot.
4. Córrelo: `python correr.py b04` y compara tu nueva `FICHA.md` contra la v1.
5. Sube tu rama y abre un Pull Request al repositorio original (ver [`CONTRIBUIR.md`](CONTRIBUIR.md)).

Que tu v2 **repruebe también es un aporte**: evita que otro compañero pierda semanas en la misma pared.

## Paso 7 · (Opcional) Monta tu niñera

Si tienes Interactive Brokers (basta una cuenta paper), deja a la niñera registrando precios y spreads de tu
activo mientras duermes. Ver [`agentes/ROLES.md`](agentes/ROLES.md) y:

```bash
python -m agentes.ninera_ibkr --simbolos SPY --cada 20
```

Es **solo lectura** y se niega a correr si detecta una cuenta real.

---

## Mapa del repositorio

```
EMPEZAR.md            ← estás aquí
README.md             ← la tabla de los 15 bots y el resultado de la cartera
CONTRIBUIR.md         ← cómo proponer tu v2
docs/CONCEPTO.md      ← el porqué: de un bot a una organización (sesión 20)
docs/ELEGIR_BOT.md    ← qué bot encaja con tu capital, país y broker
docs/PLANTILLA_V2.md  ← pre-registro de tu hipótesis
docs/PROMPTS.md       ← prompts listos para trabajar con Claude Code
docs/PREGUNTAS.md     ← problemas frecuentes
bots/                 ← los 15 prototipos (uno por archivo)
nucleo/               ← motor de backtest y vara de medir (no tocar sin avisar)
resultados/           ← ficha, curva y operaciones de cada bot
cartera/              ← matemática de la cartera, lote mínimo, mayordomo
agentes/              ← niñera IBKR, prompts del analista y del árbitro
fabrica/              ← variantes en lote con corrección por azar
```

## Reglas de convivencia (cortas)

1. **Nunca empujes a `main` del repositorio original**: trabaja en tu fork y entra por Pull Request.
1. **Nada de dinero real** con estos prototipos. Demo o paper primero; siempre.
2. **No subas** claves, contraseñas, números de cuenta, capturas con saldos ni datos de otras personas.
3. **No toques `nucleo/`** en tu v2: si crees que tiene un error, abre un *issue*. Así todos medimos con la misma vara.
4. **Pre-registra** antes de probar. Sin pre-registro, un buen resultado no cuenta.
5. **Comparte lo que no funciona.** Es la mitad del valor del laboratorio.
