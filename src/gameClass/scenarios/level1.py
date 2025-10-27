def get_level1():
    """
    Retorna un layout simple de 24x24 para Battle City
    'A': Tanque equipo A
    'B': Tanque equipo B
    'a': Base equipo A
    'b': Base equipo B
    'X': Pared de ladrillo
    'S': Pared de acero
    ' ': Espacio vacío
    """
    layout = [
        "B           B",  # 13
        " X X X X X X ",  # 12
        " X X X X X X ",  # 11
        " X X XSX X X ",  # 10
        " X X     X X ",  # 9
        "     X X     ",  # 8
        "S XX     XX S",  # 7
        "     X X     ",  # 6
        " X X XXX X X ",  # 5
        " X X X X X X ",  # 4
        " X X     X X ",  # 3
        " X X XXX X X ",  # 2
        "    AXbX     ",  # 1
    ]
    return layout
