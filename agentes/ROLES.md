# Los roles del organigrama (agentes sobre los bots)

> «Un bot de trading es una pieza fija. Un agente dedicado a monitorear tu cartera, tus operaciones u
> oportunidades es un analista.» — sesión 20

Los bots de `bots/` son **deterministas**: reglas fijas, backtest, forward. Los agentes de esta carpeta
**no reemplazan** esas reglas; las acompañan. Cada uno es un puesto que antes solo tenía un fondo.

| Rol | Qué hace | Qué NO hace | Prototipo v1 |
|---|---|---|---|
| **Niñera / monitor** | Se conecta cada X minutos (a IBKR paper u otro broker) y registra bid, ask, spread, vol. implícita y cada llenado. Separa el drawdown en **estrategia / ejecución / contexto**. | No valida el edge: más horas del mismo código no añaden muestra. | `ninera_ibkr.py` (solo lectura) |
| **Analista de mercados** | Lee los datos que dejan la niñera, Impulse Detector y Profeta, y escribe un informe corto con lo que cambió desde la última revisión. | No ejecuta órdenes. | `PROMPT_ANALISTA.md` (para Claude Code en bucle) |
| **Mayordomo / árbitro** | Reasigna el capital entre bots según el régimen, **dentro de un reglamento** (piso, techo, autonomía). | No cambia las reglas de ningún bot. | `cartera/mayordomo.py` (reglas) + `PROMPT_ARBITRO.md` |
| **Fábrica (operario)** | Programa variantes baratas de una idea ya montada por un modelo frontera. | No decide qué variante sobrevive: eso lo decide la vara (placebo, fuera de muestra). | `fabrica/fabrica.py` |
| **Auditor (manager)** | Revisa el trabajo de los demás y busca ineficiencias («el torno que mejora el torno»). | — | Tú + un modelo frontera revisando los repos |

## Reglas de la casa para cualquier agente

1. **Cortafuegos.** Máquina o cuenta aislada (la Mac Mini de la sesión, un PC viejo, una VPS). Nada de
   agentes en la computadora donde está tu banco.
2. **Paper primero.** Ningún agente toca dinero real sin autorización explícita en ese momento.
3. **Todo queda escrito.** Cada ciclo deja un registro (CSV, repo en GitHub). Lo que no se registra no
   construye dataset.
4. **Tokens con cabeza.** Lo que se repite igual cada vez va a un script de Python; el modelo solo
   entra donde hay que interpretar.
5. **Veredicto por reglas.** Un bot se escala o se apaga a las 80 operaciones de forward, no por la
   racha de la semana. Un corte extraordinario solo si el drawdown pasa el umbral **escrito antes**.
