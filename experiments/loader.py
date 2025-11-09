from pathlib import Path


def get_map(base_path: Path, index: int = 0):
    """Devuelve el layout (lista de strings) del mapa solicitado.
    Actualmente solo soporta index==0 -> level1.
    """
    base = Path(base_path)
    try:
        # importar desde src.gameClass.scenarios
        from src.gameClass.scenarios.level1 import get_level1
    except Exception as e:
        raise ImportError("No se pudo importar level1 desde src.gameClass.scenarios: " + str(e))

    if index == 0:
        return get_level1()
    else:
        raise IndexError("Sólo existe el mapa índice 0 en este helper (level1)")


def load_game_assets(base_path: Path):
    """Placeholder para preparar recursos adicionales si es necesario.
    Actualmente no hace nada pero mantiene la interfaz esperada.
    """
    return True
