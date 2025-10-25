def get_layout():
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
        "   x   x             ",  # 21
        " a X A S             ",  # 20
        "            XXXXS    ",  # 19
        "XX                   ",  # 18
        "    XXXXXX  X X      ",  # 17
        " A  X  S X  X X      ",  # 16
        "    X  S X  X X      ",  # 15
        "XS  XXXXXX  X X   XXX",  # 14
        "            X X      ",  # 13
        "                     ",  # 12
        "  XXXS    S    SXXX  ",  # 11
        "                     ",  # 10
        "      X X            ",  # 9
        "XXX   X X  XXXXXX  SX",  # 8
        "      X X  X S  X    ",  # 7
        "      X X  X S  X  B ",  # 6
        "      X X  XXXXXX    ",  # 5
        "                   XX",  # 4
        "     SXXX            ",  # 3
        "             S B X b ",  # 2
        "             X   X   ",  # 1
    ]
    return layout