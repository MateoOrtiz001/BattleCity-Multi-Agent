
class Tank():
    """Clase que representa un tanque en el juego Battle City."""
    def __init__(self, position, team):
        self.position = position        # Posición del tanque
        self.direction = None            # Dirección del tanque (0: arriba, 1: derecha, 2: abajo, 3: izquierda)
        self.team = team                # Equipo al que pertenece el tanque ('A' o 'B')
        self.is_alive = True            # Estado del tanque (vivo o destruido)
        self.health = 3                  # Salud del tanque
        
    def getState(self):
        return {
            'position': self.position,
            'direction': self.direction,
            'team': self.team,
            'health': self.health,
            'is_alive': self.is_alive
        }
    
    def move(self, new_position):
        self.position = new_position
        
    def destroy(self):
        self.is_alive = False
        
    def takeDamage(self, damage):
        self.health -= damage
        if self.health <= 0:
            self.destroy()