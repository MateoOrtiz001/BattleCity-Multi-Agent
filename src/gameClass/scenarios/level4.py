"""
Level 4: Un nivel más pequeño (8x8) para pruebas rápidas
"""
def get_level4():
    """
    Retorna un layout simple de 8x8 para Battle City
    'A': Tanque equipo A
    'B': Tanque equipo B
    'a': Base equipo A
    'b': Base equipo B
    'X': Pared de ladrillo
    'S': Pared de acero
    ' ': Espacio vacío
    """
    layout = [
        "a X A   S",  # 0
        "         ",  # 1
        "         ",  # 2
        "A   X    ",  # 3
        "X  XXX  X",  # 4
        "    X   B",  # 5
        "         ",  # 6
        "         ",  # 7
        "S   B X b",  # 8
    ]
    return layout
