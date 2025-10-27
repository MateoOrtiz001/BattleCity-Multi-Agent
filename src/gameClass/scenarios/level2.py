def get_level2():
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
        "   XXX XXX   ",  # 12
        "             ",  # 11
        "  XX X X XX  ",  # 10
        "S XX X X XX S",  # 9
        "             ",  # 8
        "   S XXX S   ",  # 7
        " X X X X X X ",  # 6
        "   X XXX X   ",  # 5
        "S XX     XX S",  # 4
        "             ",  # 3
        "   S XXX S   ",  # 2
        "    AXbX     ",  # 1
    ]
    return layout