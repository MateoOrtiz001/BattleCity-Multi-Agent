
class Tank():
    """Clase que representa un tanque en el juego Battle City."""
    def __init__(self, position, team):
        self.position = position        # Posición del tanque
        self.spawn_position = position  # Posición donde reaparecerá tras ser destruido
        self.direction = None           # Dirección del tanque ('UP','DOWN','LEFT','RIGHT')
        self.team = team                # Equipo al que pertenece el tanque ('A' o 'B')
        self.is_alive = True            # Estado del tanque (vivo o destruido)
        self.health = 3                 # Salud del tanque}
        self.respawn_timer = 0.0
        
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
        # Configurar un tiempo de respawn (segundos). Valor por defecto 5s.
        try:
            # intentar leer una constante global si existe
            RESPAWN_DELAY = 5
        except Exception:
            RESPAWN_DELAY = 5
        self.respawn_timer = RESPAWN_DELAY
        
    def takeDamage(self, damage):
        self.health -= damage
        if self.health <= 0:
            self.destroy()

    def respawn(self):
        """Reaparecer el tanque en su posición de spawn y resetear su salud."""
        self.position = self.spawn_position
        self.health = 3
        self.is_alive = True
        self.respawn_timer = 0.0