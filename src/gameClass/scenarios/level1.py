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
        "                     ",  # 21
        "    X   X a X   X    ",  # 20
        " A  X SSX   XSS X  A ",  # 19
        "    X   XXXXX   X    ",  # 18
        "      X       X      ",  # 17
        "SS  X    SSS    X  SS",  # 16
        "S     X       X     S",  # 15
        "S XXX X XX XX X XXX S",  # 14
        "S   S X  X X  X S   S",  # 13
        "S X   X  X X  X   X S",  # 12
        "S S  XX SS SS XX  S S",  # 11
        "S X   X  X X  X   X S",  # 10
        "S   S X  X X  X S   S",  # 9
        "S XXX X XX XX X XXX S",  # 8
        "S     X       X     S",  # 7
        "SS  X    SSS    X  SS",  # 6
        "      X       X      ",  # 5
        "    X   XXXXX   X    ",  # 4
        " B  X SSX   XSS X  B ",  # 3
        "    X   X b X   X     ",  # 2
        "                     ",  # 1
    ]
    return layout
