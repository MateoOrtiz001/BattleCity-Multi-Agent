
class Wall():
    """Clase que representa una pared en el juego Battle City."""
    __slots__ = ("position", "wall_type", "is_destroyed", "health")
    def __init__(self, position, wall_type):
        self.position = position      # (x, y) Coordenadas de la pared
        self.wall_type = wall_type    # Si es 'brick' o 'steel'
        self.is_destroyed = False
        self.health = 5

    def destroy(self):
        if self.wall_type != 'steel':
            self.is_destroyed = True

    def takeDamage(self, damage):
        if self.wall_type == 'brick':
            self.health -= damage
            if self.health <= 0:
                self.destroy()
                
    def getPosition(self):
        return self.position
    
    def getType(self):
        return self.wall_type
    
    def isDestroyed(self):
        return self.is_destroyed
    
    def getHealth(self):
        return self.health