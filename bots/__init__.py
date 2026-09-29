"""Los 15 bots de la sesión 20. Cada módulo expone FICHA (dict) y correr() -> Resultado."""
import importlib
import pkgutil


def todos() -> list[str]:
    import bots
    return sorted(m.name for m in pkgutil.iter_modules(bots.__path__) if m.name[:1] == "b" and m.name[1:3].isdigit())


def cargar(nombre: str):
    return importlib.import_module(f"bots.{nombre}")
