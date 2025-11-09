from src.agents.expectimax import ExpectimaxAgent as _ExpectimaxAgent


def make_agent(depth=3, time_limit=8, debug=False):
    """Factory que devuelve una instancia del ExpectimaxAgent existente en el proyecto.
    Esto evita duplicar la implementación y mantiene la interfaz simple para el notebook.
    """
    return _ExpectimaxAgent(depth=depth, time_limit=time_limit, debug=debug)
