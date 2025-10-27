def get_level3():
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
        "  X  S       ",  # 12
        "X X  X    X X",  # 11
        "X X XX    X X",  # 10
        "X    XXXX XXX",  # 9
        "XXXX X    X  ",  # 8
        "     X SS    ",  # 7
        " XXXXX XXX XX",  # 6
        "       XXX XX",  # 5
        " X XXXXXXX   ",  # 4
        "XX         S ",  # 3
        " XXX XXX XXX ",  # 2
        "    AXbX   X ",  # 1
    ]
    return layout