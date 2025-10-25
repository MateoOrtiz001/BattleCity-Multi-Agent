
class Wall():
    """Clase que representa una pared en el juego Battle City."""
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
                self.is_destroyed = True
                
    def getState(self):
        return {
            'position': self.position,
            'wall_type': self.wall_type,
            'is_destroyed': self.is_destroyed,
            'health': self.health
        }