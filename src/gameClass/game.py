from ..utils import *
import time
import os
import traceback
import sys
import copy
from .bullet import Bullet
from .tank import Tank
from .walls import Wall
from .base import Base

class BattleCityGame:
    def __init__(self):
        self.teamA_tanks = []   # Estado de los tanques del equipo A
        self.teamB_tanks = []   # Estado de los tanques del equipo B
        self.walls = []         # Estado de las paredes
        self.baseA = None       # Estado de la base del equipo A
        self.baseB = None       # Estado de la base del equipo B
        self.bullets = []       # Estado de las balas
        # Límites de tiempo: soportamos tiempo en segundos para sincronizar con
        # el reloj real y también mantenemos el contador de pasos (current_time)
        self.time_limit = 500   # pasos o turnos (retrocompatibilidad)
        self.current_time = 0
        self.time_limit_seconds = 120.0  # tiempo límite en segundos (por defecto 2 minutos)
        self.elapsed_time = 0.0  # tiempo real transcurrido en segundos

    def initialize(self, layout):
        """Inicializa el juego con un layout dado."""
        for y in range(len(layout)):
            for x in range(len(layout[y])):
                cell = layout[y][x]
                pos = (x, len(layout) - 1 - y)  # Invertir coordenada Y para que (0,0) esté en la esquina inferior izquierda
                if cell == 'A':
                    tank = Tank(position=pos, team='A')
                    tank.spawn_position = pos
                    self.teamA_tanks.append(tank)
                elif cell == 'B':
                    tank = Tank(position=pos, team='B')
                    tank.spawn_position = pos
                    self.teamB_tanks.append(tank)
                elif cell == 'a':
                    self.baseA = Base(position=pos, team='A')
                elif cell == 'b':
                    self.baseB = Base(position=pos, team='B')
                elif cell == 'X':
                    wall = Wall(position=pos, wall_type='brick')
                    self.walls.append(wall)
                elif cell == 'S':
                    wall = Wall(position=pos, wall_type='steel')
                    self.walls.append(wall)
    
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
            'time_limit': self.time_limit,
            'elapsed_time': self.elapsed_time,
            'time_limit_seconds': self.time_limit_seconds
        }
    
    def is_terminal(self):
        """Verifica si el juego terminó."""
        if self.baseA.isDestroyed() or self.baseB.isDestroyed():
            return True
        # También verificar tiempo real en segundos
        if self.elapsed_time >= self.time_limit_seconds:
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
        """
        Genera un nuevo estado del juego tras aplicar la acción del tanque dado.
        Avanza un paso de simulación (acciones + movimiento de balas).
        """
        # Clonar el estado actual del juego
        next_game = copy.deepcopy(self)

        # Identificar tanque
        all_tanks = next_game.teamA_tanks + next_game.teamB_tanks
        tank = all_tanks[tankIndex]
        if not tank.is_alive:
            return next_game  # tanque muerto => no hace nada

        # Movimiento por dirección
        DIR_DELTA = {
            'UP': (0, 1),
            'DOWN': (0, -1),
            'LEFT': (-1, 0),
            'RIGHT': (1, 0)
        }

        # Acción: mover
        if action.startswith('MOVE'):
            direction = action.split('_')[1]
            tank.direction = direction
            dx, dy = DIR_DELTA[direction]
            new_pos = (tank.position[0] + dx, tank.position[1] + dy)

            # Verificar colisiones (muros, bordes, otros tanques, bases)
            if (0 <= new_pos[0] < 24 and 0 <= new_pos[1] < 24):
                # Muros
                blocked = False
                for wall in next_game.walls:
                    if wall.position == new_pos and not wall.is_destroyed:
                        blocked = True
                        break
                # Bases
                if next_game.baseA.position == new_pos or next_game.baseB.position == new_pos:
                    blocked = True
                # Tanques
                for t in all_tanks:
                    if t != tank and t.is_alive and t.position == new_pos:
                        blocked = True
                        break
                if not blocked:
                    tank.move(new_pos)

        elif action == 'FIRE':
            # Crear bala frente al tanque
            # Cuando un tanque dispara estando pegado a un muro/objeto, la bala
            # se creaba en la celda contigua y luego se movía una celda más
            # antes de comprobar colisiones, lo que provocaba que atravesara
            # el objeto. Aquí comprobamos colisiones inmediatas en la celda
            # de spawn antes de crear la bala.
            if tank.direction is not None:
                dx, dy = DIR_DELTA[tank.direction]
                bullet_pos = (tank.position[0] + dx, tank.position[1] + dy)
                if 0 <= bullet_pos[0] < 24 and 0 <= bullet_pos[1] < 24:
                    # Impedir disparos múltiples: un tanque solo puede tener
                    # una bala activa a la vez (por owner_id)
                    already_has_bullet = False
                    for b in next_game.bullets:
                        if b.owner_id == tankIndex and b.is_active:
                            already_has_bullet = True
                            break
                    if already_has_bullet:
                        immediate_hit = True  # bloquear la creación
                    else:
                        immediate_hit = False

                    # 1) Impacto inmediato con muro
                    for wall in next_game.walls:
                        if not wall.is_destroyed and wall.position == bullet_pos:
                            wall.takeDamage(1)
                            immediate_hit = True
                            break

                    # 2) Impacto inmediato con base enemiga
                    if not immediate_hit:
                        if tank.team == 'A' and next_game.baseB and next_game.baseB.position == bullet_pos:
                            next_game.baseB.takeDamage()
                            immediate_hit = True
                        elif tank.team == 'B' and next_game.baseA and next_game.baseA.position == bullet_pos:
                            next_game.baseA.takeDamage()
                            immediate_hit = True

                    # 3) Impacto inmediato con tanque enemigo
                    if not immediate_hit:
                        for t in all_tanks:
                            if t.is_alive and t.team != tank.team and t.position == bullet_pos:
                                t.takeDamage(1)
                                immediate_hit = True
                                break

                    # Si no hubo impacto inmediato, crear la bala normalmente
                    if not immediate_hit:
                        next_game.bullets.append(
                            Bullet(bullet_pos, tank.direction, tank.team, owner_id=tankIndex)
                        )

        # --- Mover balas ---
        active_bullets = []
        for bullet in next_game.bullets:
            if not bullet.is_active:
                continue
            bullet.move()
            x, y = bullet.position

            # 1. Fuera del tablero
            if not (0 <= x < 24 and 0 <= y < 24):
                bullet.is_active = False
                continue

            # 2. Impacto con muro
            for wall in next_game.walls:
                if not wall.is_destroyed and wall.position == (x, y):
                    wall.takeDamage(1)
                    bullet.is_active = False
                    break
            if not bullet.is_active:
                continue

            # 3. Impacto con base
            if bullet.team == 'A' and next_game.baseB.position == (x, y):
                next_game.baseB.takeDamage()
                bullet.is_active = False
            elif bullet.team == 'B' and next_game.baseA.position == (x, y):
                next_game.baseA.takeDamage()
                bullet.is_active = False
            if not bullet.is_active:
                continue

            # 4. Impacto con tanque
            for t in all_tanks:
                if t.is_alive and t.team != bullet.team and t.position == (x, y):
                    t.takeDamage(1)
                    bullet.is_active = False
                    break

            if bullet.is_active:
                active_bullets.append(bullet)

        next_game.bullets = active_bullets
        next_game.current_time += 1
        return next_game
    
    def advance_time(self, delta_seconds):
        """Avanza el tiempo real del juego y maneja respawns.

        delta_seconds: segundos transcurridos desde la última llamada.
        """
        self.elapsed_time += delta_seconds

        # Manejar respawn de tanques muertos
        for t in self.teamA_tanks + self.teamB_tanks:
            if not t.is_alive and getattr(t, 'respawn_timer', 0) > 0:
                t.respawn_timer -= delta_seconds
                if t.respawn_timer <= 0:
                    t.respawn()

    # Nota: is_terminal usa elapsed_time para decidir empates por tiempo
    
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
