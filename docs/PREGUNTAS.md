# Preguntas y problemas frecuentes

**`UnicodeEncodeError` o caracteres raros en Windows.**
Antes de correr: `set PYTHONUTF8=1` (cmd) o `$env:PYTHONUTF8=1` (PowerShell).

**`yfinance no devolvió datos` / error 429.**
Yahoo limita las descargas. El código reintenta solo; si persiste, espera unos minutos y vuelve a correr. Si
usas una versión vieja de yfinance: `pip install -U yfinance`.

**`MT5 no inicializa`.**
Abre el terminal de MetaTrader 5 e inicia sesión (una demo sirve). Si está en otra ruta, define
`MT5_TERMINAL` con la ruta completa a `terminal64.exe`. El paquete de Python de MT5 solo existe para Windows:
en Mac, estudia esos bots con los resultados publicados o usa una máquina virtual/VPS con Windows.

**`Tu broker no tiene XAUUSD`.**
El código prueba los sufijos más comunes (`m`, `.`, `+`, `.r`, `_i`). Si tu broker usa otro nombre, pásalo
editando la línea `datos.mt5("...")` del bot en tu rama.

**Mis resultados no son idénticos a los publicados.**
Normal: cada broker tiene velas y spreads distintos, y los datos se actualizan cada día. Lo importante es que el
veredicto no cambie. Si cambia mucho, es un hallazgo: repórtalo en un *issue*.

**El backtest tarda mucho.**
Usa menos placebos para explorar (`--placebo 20`) y deja 100 para el resultado final.

**¿Puedo operar un bot «candidato» con dinero real?**
No. «Candidato» significa «merece forward en demo». El camino es: demo con la niñera registrando ejecución →
80 operaciones → decisión con los umbrales escritos antes.

**¿Por qué casi todos reprueban?**
Porque es lo esperado: en el almacén de hallazgos del Instituto sobrevive ~1 de cada 10 hipótesis. Una v1
reprobada y bien documentada ahorra semanas a los demás.

**Encontré un error en `nucleo/`.**
Abre un *issue* con el comando que lo reproduce. No lo cambies en tu v2: todos tenemos que medir con la misma vara.

**No sé por dónde empezar.**
Corre `b04`, lee su ficha y luego `docs/ELEGIR_BOT.md`. Si sigues sin ver tu camino, escribe a
contacto@juancamilorico.com con el asunto «Instituto Quant sesión 20 · hoja de ruta».
