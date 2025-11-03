
class Bullet:
    """Clase que representa una bala en Battle City."""
    def __init__(self, position, direction, team, owner_id=None):
        self.position = position          # (x, y)
        self.direction = direction        # 'UP', 'DOWN', 'LEFT', 'RIGHT'
        self.team = team                  # 'A' o 'B'
        self.owner_id = owner_id          # índice del tanque que la disparó
        self.is_active = True             # Si la bala sigue en vuelo
        self.prev_position = None         # posición previa (útil para detectar choques cabeza-a-cabeza)

    def move(self):
        """Avanza una celda en su dirección."""
        # Guardar la posición previa antes de mover (útil para detección de colisiones entre balas)
        self.prev_position = self.position
        dx, dy = 0, 0
        if self.direction == 'UP': dy = 1
        elif self.direction == 'DOWN': dy = -1
        elif self.direction == 'LEFT': dx = -1
        elif self.direction == 'RIGHT': dx = 1
        self.position = (self.position[0] + dx, self.position[1] + dy)

    def getPosition(self):
        return self.position
    
    def getDirection(self):
        return self.direction
    
    def getTeam(self):
        return self.team
    
    def getOwnerID(self):
        return self.owner_id
    
    def isActive(self):
        return self.is_active
    
    def getPrevPosition(self):
        return self.prev_position
    
    def setActive(self, active):
        self.is_active = active
