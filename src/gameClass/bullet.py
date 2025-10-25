
class Bullet:
    """Clase que representa una bala en Battle City."""
    def __init__(self, position, direction, team, owner_id=None):
        self.position = position          # (x, y)
        self.direction = direction        # 'UP', 'DOWN', 'LEFT', 'RIGHT'
        self.team = team                  # 'A' o 'B'
        self.owner_id = owner_id          # índice del tanque que la disparó
        self.is_active = True             # Si la bala sigue en vuelo

    def move(self):
        """Avanza una celda en su dirección."""
        dx, dy = 0, 0
        if self.direction == 'UP': dy = 1
        elif self.direction == 'DOWN': dy = -1
        elif self.direction == 'LEFT': dx = -1
        elif self.direction == 'RIGHT': dx = 1
        self.position = (self.position[0] + dx, self.position[1] + dy)

    def getState(self):
        """Devuelve un diccionario representando el estado de la bala."""
        return {
            'position': self.position,
            'direction': self.direction,
            'team': self.team,
            'is_active': self.is_active
        }
