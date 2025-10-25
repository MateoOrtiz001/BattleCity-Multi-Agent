
class Base:
    """Clase que representa una base en el juego Battle City."""
    def __init__(self, position, team):
        self.position = position    # Posición de la base
        self.is_destroyed = False   # Estado de la base
        self.team = team            # Equipo al que pertenece la base ('A' o 'B')
        
    def getState(self):
        return {
            'position': self.position,
            'is_destroyed': self.is_destroyed,
            'team': self.team
        }
    
    def isDestroyed(self):
        return self.is_destroyed
    
    def takeDamage(self):
        self.is_destroyed = True