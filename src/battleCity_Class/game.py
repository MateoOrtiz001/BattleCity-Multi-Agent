from utils import *
import time
import os
import traceback
import sys

class BattleCityGame:
    def __init__(self):
        self.teamA_tanks = []   # Estado de los tanques del equipo A
        self.teamB_tanks = []   # Estado de los tanques del equipo B
        self.walls = []         # Estado de las paredes
        self.baseA = None       # Estado de la base del equipo A
        self.baseB = None       # Estado de la base del equipo B
        self.bullets = []       # Estado de las balas
        self.time_limit = 500   # pasos o turnos
        self.current_time = 0

    def initialize(self, layout):
        # Inicializar el estado del juego basado en el diseño proporcionado
        pass
    
    def getState(self):
        """Retorna el estado completo del juego"""
        return {
            'teamA_tanks': [tank.getState() for tank in self.teamA_tanks],
            'teamB_tanks': [tank.getState() for tank in self.teamB_tanks],
            'walls': [wall.getState() for wall in self.walls],
            'baseA': self.baseA.getState(),
            'baseB': self.baseB.getState(),
            'bullets': [bullet.getState() for bullet in self.bullets],
            'current_time': self.current_time,
            'time_limit': self.time_limit
        }
    
    def is_terminal(self):
        """Verifica si el juego terminó."""
        if self.baseA.isDestroyed() or self.baseB.isDestroyed():
            return True
        if self.current_time >= self.time_limit:
            return True
        return False

    def getLegalActions(self, tankIndex):
        """Obtener acciones legales para un tanque específico"""
        actions = []
        
        # Primero verificamos si el tanque está vivo
        tank = None
        if tankIndex < len(self.teamA_tanks):
            tank = self.teamA_tanks[tankIndex]
        elif tankIndex < len(self.teamA_tanks) + len(self.teamB_tanks):
            tank = self.teamB_tanks[tankIndex - len(self.teamA_tanks)]
            
        if not tank or not tank.is_alive:
            return []
            
        # STOP y FIRE siempre son acciones válidas para un tanque vivo
        actions.extend(['STOP', 'FIRE'])
        
        # Obtenemos la posición actual del tanque
        x, y = tank.position
        
        # Verificamos movimientos posibles
        possible_moves = {
            'MOVE_UP': (x, y + 1),
            'MOVE_DOWN': (x, y - 1),
            'MOVE_LEFT': (x - 1, y),
            'MOVE_RIGHT': (x + 1, y)
        }
        
        # Verificamos cada movimiento posible
        for move, new_pos in possible_moves.items():
            can_move = True
            # Verificar colisiones con paredes
            for wall in self.walls:
                if wall.position == new_pos and not wall.is_destroyed:
                    can_move = False
                    break
            # Verificar colisiones con otros tanques
            for other_tank in self.teamA_tanks + self.teamB_tanks:
                if other_tank != tank and other_tank.is_alive and other_tank.position == new_pos:
                    can_move = False
                    break
            # Verificar colisiones con bases
            if self.baseA and self.baseA.position == new_pos and not self.baseA.isDestroyed():
                can_move = False
            if self.baseB and self.baseB.position == new_pos and not self.baseB.isDestroyed():
                can_move = False
                
            if can_move:
                actions.append(move)
        
        return actions
        
    def generateSuccessor(self, tankIndex, action):
        # Generar el estado sucesor después de que un tanque tome una acción
        pass
    
    def evaluate_state(self, state, team='A'):
        """Función de evaluación para el estado del juego."""
        # Determinar equipo enemigo
        enemy = 'B' if team == 'A' else 'A'
        
        # Factor de tiempo (más importante conforme se acerca al límite)
        time_factor = (state['time_limit'] - state['current_time']) / state['time_limit']
        
        # Estado de las bases (salud y estado)
        my_base = state['base' + team]
        enemy_base = state['base' + enemy]
        
        # Si alguna base está destruida, retornar valor terminal
        if my_base['is_destroyed']:
            return float('-inf')  # Pérdida
        if enemy_base['is_destroyed']:
            return float('inf')   # Victoria
            
        # Factor de salud de las bases
        base_health_factor = (my_base['health'] - enemy_base['health']) * 5.0
        
        # Tanques vivos y su posicionamiento
        my_tanks = [t for t in state['team' + team + '_tanks'] if t['is_alive']]
        enemy_tanks = [t for t in state['team' + enemy + '_tanks'] if t['is_alive']]
        
        # Diferencia de tanques vivos
        tanks_advantage = (len(my_tanks) - len(enemy_tanks)) * 10.0
        
        # Distancias a la base enemiga (considerando ambos tanques)
        tank_distances = [
            manhattanDistance(tank['position'], enemy_base['position'])
            for tank in my_tanks
        ]
        avg_distance = sum(tank_distances) / len(tank_distances) if tank_distances else float('inf')
        
        # Distancia entre tanques aliados (para mantenerlos separados pero no demasiado)
        tank_separation = 0
        if len(my_tanks) == 2:
            separation = manhattanDistance(my_tanks[0]['position'], my_tanks[1]['position'])
            # Penalizar si están muy juntos o muy separados (queremos una separación óptima de ~5 unidades)
            tank_separation = -abs(separation - 5) * 2
        
        # Distancia del enemigo a nuestra base (factor defensivo)
        enemy_closest_distance = min([
            manhattanDistance(tank['position'], my_base['position'])
            for tank in enemy_tanks
        ]) if enemy_tanks else float('inf')
        defensive_factor = enemy_closest_distance * 2.0
        
        # Combinación ponderada de factores
        score = (
            -0.8 * avg_distance +           # Distancia a base enemiga
            tanks_advantage +               # Ventaja en número de tanques
            base_health_factor +            # Diferencia en salud de las bases
            tank_separation +               # Separación entre tanques aliados
            defensive_factor * time_factor  # Factor defensivo (más importante al final)
        )
        
        # Invertir el score si somos el equipo B (minimizador)
        return score if team == 'A' else -score
