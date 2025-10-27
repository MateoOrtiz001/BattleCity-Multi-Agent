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
    def __init__(self, board_size=21):
        self.board_size = board_size        # Tamaño del tablero (board_size x board_size)
        self.teamA_tank = None              # Estado del tanque     
        self.teamB_tanks = []               # Estado de los tanques del enemigo
        self.walls = []                     # Estado de las paredes
        self.base = None                    # Estado de la base del enemigo
        self.bullets = []                   # Estado de las balas
        self.time_limit = 500               # Tiempo límite 
        self.current_time = 0               # Tiempo actual en ticks
        self.reserves_A = 2                 # Reservas de tanques adicionales para el jugador
        self.reserves_B = 6                 # Reservas de tanques adicionales para los enemigos

    def initialize(self, layout):
        """Inicializa el juego con un layout dado."""
        # Ajustar el tamaño del tablero en base al layout proporcionado
        width = len(layout[0])
        height = len(layout)
        # Usar el máximo entre ancho/alto para definir board_size (cuadrado)
        self.board_size = max(width, height)
        for y in range(len(layout)):
            for x in range(len(layout[y])):
                cell = layout[y][x]
                pos = (x, len(layout) - 1 - y)  # Invertir coordenada Y para que (0,0) esté en la esquina inferior izquierda
                if cell == 'A':
                    tank = Tank(position=pos, team='A')
                    tank.spawn_position = pos
                    self.teamA_tank = tank
                elif cell == 'B':
                    tank = Tank(position=pos, team='B')
                    tank.spawn_position = pos
                    self.teamB_tanks.append(tank)
                elif cell == 'b':
                    self.base = Base(position=pos, team='A')
                elif cell == 'X':
                    wall = Wall(position=pos, wall_type='brick')
                    self.walls.append(wall)
                elif cell == 'S':
                    wall = Wall(position=pos, wall_type='steel')
                    self.walls.append(wall)
    
    def getState(self):
        """Retorna el estado completo del juego"""
        return {
            'teamA_tank': self.teamA_tank.getState(),
            'teamB_tanks': [tank.getState() for tank in self.teamB_tanks],
            'walls': [wall.getState() for wall in self.walls],
            'base': self.base.getState(),
            'bullets': [bullet.getState() for bullet in self.bullets],
            'current_time': self.current_time,
            'time_limit': self.time_limit,
            'reserves_A': self.reserves_A,
            'reserves_B': self.reserves_B
        }
    
    def is_terminal(self):
        """Verifica si el juego terminó."""
        if self.base.isDestroyed() or self.reserves_A == 0 or self.reserves_B == 0 or self.current_time >= self.time_limit:
            return True
        return False

    def getLegalActions(self, tankIndex):
        """Obtener acciones legales para un tanque específico"""
        actions = []
        
        # Seleccionamos el tanque correspondiente
        tank = None
        if tankIndex == 0:
            tank = self.teamA_tank
        else:
            tank = self.teamB_tanks[tankIndex - 1]
        
        # Verificamos que el tanque esté vivo, no lo está, simplemente es como si no hiciera nada
        if not tank or not tank.is_alive:
            actions.append('STOP')
            return actions
            
        # Solo agregamos FIRE si hay una base enemiga o tanque enemigo en la dirección actual
        x, y = tank.position
        
        # Buscar objetivo valioso en la dirección actual
        if tank.direction:
            dx, dy = {'UP': (0, 1), 'DOWN': (0, -1), 'LEFT': (-1, 0), 'RIGHT': (1, 0)}[tank.direction]
            test_pos = (x + dx, y + dy)
            
            # Verificar si hay línea directa objetos disparables
            while 0 <= test_pos[0] < self.board_size and 0 <= test_pos[1] < self.board_size:
                # Tanque enemigo
                for other_tank in [self.teamA_tank] + self.teamB_tanks:
                    if other_tank.is_alive and other_tank.team != tank.team and other_tank.position == test_pos:
                        actions.append('FIRE')
                        break
                
                # Verificar muros
                blocked = False
                for wall in self.walls:
                    if not wall.is_destroyed and wall.position == test_pos:
                        if wall.wall_type == 'brick':  # Si es un muro de ladrillo, es un objetivo válido
                            actions.append('FIRE')
                        blocked = True
                        break
                if blocked:
                    break
                    
                test_pos = (test_pos[0] + dx, test_pos[1] + dy)
        
        # Añadir movimientos posibles (si no hay obstáculos)
        x, y = tank.position
        possible_moves = {
            'MOVE_UP': (x, y + 1),
            'MOVE_DOWN': (x, y - 1),
            'MOVE_LEFT': (x - 1, y),
            'MOVE_RIGHT': (x + 1, y)
        }
        
        # Verificar cada movimiento posible
        for move, new_pos in possible_moves.items():
            if 0 <= new_pos[0] < self.board_size and 0 <= new_pos[1] < self.board_size:  # Dentro del tablero
                can_move = True
                # Colisión con muros
                for wall in self.walls:
                    if not wall.is_destroyed and wall.position == new_pos:
                        can_move = False
                        break
                if not can_move:
                    continue
                        
                # Colisión con otros tanques
                for other_tank in [self.teamA_tank] + self.teamB_tanks:
                    if other_tank != tank and other_tank.is_alive and other_tank.position == new_pos:
                        can_move = False
                        break
                if not can_move:
                    continue
                        
                # Colisión con bases
                if not self.base.isDestroyed() and self.base.position == new_pos:
                    continue
                        
                actions.append(move)
                
        # Si no hay acciones posibles, al menos permitir STOP
        if not actions:
            actions.append('STOP')
            
        return actions

    def getNumAgents(self):
        """Número total de agentes (1 tanque de A + len(teamB_tanks))."""
        return (1 if self.teamA_tank is not None else 0) + len(self.teamB_tanks)

        
    def generateSuccessor(self, tankIndex, action):
        """
        Genera un nuevo estado del juego tras aplicar la acción del tanque dado.
        Avanza un paso de simulación (acciones + movimiento de balas).
        """
        # Crear una copia profunda del juego y aplicar la acción sobre ella
        next_game = copy.deepcopy(self)

        # Seleccionamos el tanque correspondiente en la copia
        if tankIndex == 0:
            tank = next_game.teamA_tank
        else:
            # tankIndex 1..n corresponden a teamB_tanks[0..]
            tank = next_game.teamB_tanks[tankIndex - 1] if (tankIndex - 1) < len(next_game.teamB_tanks) else None

        # Si no existe el tanque o está muerto, devolvemos la copia sin cambios
        if tank is None or not getattr(tank, 'is_alive', False):
            # Si es el último agente, aun así avanzamos el mundo (balas, colisiones, tiempo)
            if tankIndex == next_game.getNumAgents() - 1:
                for bullet in next_game.bullets:
                    bullet.move()
                next_game.current_time += 1
                next_game._check_collisions()
                next_game._handle_deaths_and_respawns()
            return next_game

        # Aplicar la acción sobre el tanque
        if action == 'MOVE_UP':
            tank.direction = 'UP'
            tank.move((tank.position[0], tank.position[1] + 1))
        elif action == 'MOVE_DOWN':
            tank.direction = 'DOWN'
            tank.move((tank.position[0], tank.position[1] - 1))
        elif action == 'MOVE_LEFT':
            tank.direction = 'LEFT'
            tank.move((tank.position[0] - 1, tank.position[1]))
        elif action == 'MOVE_RIGHT':
            tank.direction = 'RIGHT'
            tank.move((tank.position[0] + 1, tank.position[1]))
        elif action == 'FIRE':
            # Crear una bala en la casilla adyacente en la dirección actual del tanque
            # Si no tiene dirección, no se dispara
            if tank.direction:
                dx, dy = {'UP': (0, 1), 'DOWN': (0, -1), 'LEFT': (-1, 0), 'RIGHT': (1, 0)}[tank.direction]
                bullet_pos = (tank.position[0] + dx, tank.position[1] + dy)
                # Comprobar que la posición inicial de la bala esté dentro del tablero
                if 0 <= bullet_pos[0] < next_game.board_size and 0 <= bullet_pos[1] < next_game.board_size:
                    new_bullet = Bullet(position=bullet_pos, direction=tank.direction, team=tank.team, owner_id=tankIndex)
                    next_game.bullets.append(new_bullet)
        elif action == 'STOP':
            # No hacemos nada especial al detenerse
            pass

        # Si hemos procesado la última acción del ciclo de agentes, avanzamos el mundo
        if tankIndex == next_game.getNumAgents() - 1:
            # Mover todas las balas una casilla
            for bullet in next_game.bullets:
                bullet.move()

            # Incrementar el tiempo del juego en 1 tick
            next_game.current_time += 1

            # Revisar colisiones (balas contra muros, tanques, base)
            next_game._check_collisions()

            # Manejar muertes/respawns tras las colisiones
            next_game._handle_deaths_and_respawns()

        return next_game
    
    def evaluate_state(self, state):
        """Función de evaluación para el estado del juego.

        Admite tanto un diccionario devuelto por getState() como None/objeto.
        Si `state` no es un dict, se usa self.getState().
        """
        # Normalizar el estado a un diccionario plano
        if isinstance(state, dict):
            s = state
        else:
            s = self.getState()

        base = s['base']                      # dict
        tankA = s['teamA_tank']               # dict
        teamB_tanks = s['teamB_tanks']        # list[dict]
        walls = s['walls']                    # list[dict]
        reserves_A = s['reserves_A']
        reserves_B = s['reserves_B']
        current_time = s['current_time']

        # Auxiliar usada más abajo
        def is_near_2_base(wall_pos, base_pos):
            return manhattanDistance(wall_pos, base_pos) <= 2
        
        # Terminales
        if base['is_destroyed']:
            return float('-inf')
        if reserves_B == 0:
            return float('inf')
        if reserves_A == 0:
            return float('-inf')
        if current_time >= self.time_limit:
            return 0

        score = 0.0

        # Puntuación por reservas
        score += 5000 * reserves_A
        score -= 1000 * reserves_B

        # Puntuación por mantener alejado a los enemigos de la base
        pos_base = base['position']
        min_dist_enemy = float('inf')
        if not teamB_tanks:
            min_dist_enemy = 0
        else:
            for t in teamB_tanks:
                if t['is_alive']:
                    dist = manhattanDistance(t['position'], pos_base)
                    if dist < min_dist_enemy:
                        min_dist_enemy = dist
        if min_dist_enemy < 10:
            score -= 5000 * (min_dist_enemy + 0.5)  # Penalización fuerte si un enemigo está cerca

        for w in walls:
            if (not w['is_destroyed']) and is_near_2_base(w['position'], pos_base):
                score += 10 * w['health']    # Salud de cada muro cerca de la base
            elif w['is_destroyed'] and is_near_2_base(w['position'], pos_base):
                score -= 100                 # Penalización por muro destruido cerca

        # Puntuación por salud del tanque del jugador
        score += 1000 * tankA['health']

        # Puntuación por cercanía a la base
        score -= 10 * manhattanDistance(tankA['position'], pos_base)

        return score 

    def _check_collisions(self):
        """Verifica colisiones de balas con muros, tanques y la base."""
        bullets_to_keep = []

        for bullet in self.bullets:
            if not getattr(bullet, 'is_active', True):
                continue

            removed = False

            # 1) Colisión con muros
            for wall in self.walls:
                if not wall.is_destroyed and wall.position == bullet.position:
                    # Dar daño al muro (brick reduce health, steel ignorado)
                    if hasattr(wall, 'takeDamage'):
                        wall.takeDamage(1)
                    else:
                        try:
                            wall.destroy()
                        except Exception:
                            pass
                    # La bala desaparece
                    removed = True
                    break

            if removed:
                continue

            # 2) Colisión con tanques
            all_tanks = [self.teamA_tank] + self.teamB_tanks
            for tank in all_tanks:
                if tank and getattr(tank, 'is_alive', False) and tank.team != bullet.team and tank.position == bullet.position:
                    # Aplicar daño al tanque
                    if hasattr(tank, 'takeDamage'):
                        tank.takeDamage(1)
                    else:
                        try:
                            tank.destroy()
                        except Exception:
                            tank.is_alive = False
                    removed = True
                    break

            if removed:
                continue

            # 3) Colisión con la base
            if self.base and (not self.base.isDestroyed()) and self.base.position == bullet.position:
                if hasattr(self.base, 'takeDamage'):
                    self.base.takeDamage()
                else:
                    try:
                        self.base.is_destroyed = True
                    except Exception:
                        pass
                removed = True

            # Si la bala no impactó nada, mantenerla (si sigue dentro del tablero)
            if not removed:
                x, y = bullet.position
                if 0 <= x < self.board_size and 0 <= y < self.board_size and getattr(bullet, 'is_active', True):
                    bullets_to_keep.append(bullet)

        # Actualizar la lista de balas activas
        self.bullets = bullets_to_keep

    def _handle_deaths_and_respawns(self):
        """Verifica tanques muertos, resta reservas e inicia respawn."""
        # Manejar muerte/respawn del tanque del jugador
        if self.teamA_tank and not getattr(self.teamA_tank, 'is_alive', True):
            if self.reserves_A > 0:
                self.reserves_A -= 1
                # Reaparecer instantáneamente en la posición de spawn
                try:
                    self.teamA_tank.respawn()
                except Exception:
                    # si respawn no existe, resetear manualmente
                    self.teamA_tank.position = getattr(self.teamA_tank, 'spawn_position', self.teamA_tank.position)
                    self.teamA_tank.health = 3
                    self.teamA_tank.is_alive = True
            else:
                self.reserves_A = 0

        # Manejar muertes/respawns de enemigos: si mueren y hay reservas, respawnearlos,
        # en otro caso eliminarlos de la lista.
        new_teamB = []
        for tank in self.teamB_tanks:
            if getattr(tank, 'is_alive', True):
                new_teamB.append(tank)
            else:
                if self.reserves_B > 0:
                    self.reserves_B -= 1
                    try:
                        tank.respawn()
                        new_teamB.append(tank)
                    except Exception:
                        # si respawn no funciona, no reaparecer
                        pass
                else:
                    # no hay reservas, tanque eliminado
                    pass

        self.teamB_tanks = new_teamB
        
    def advance_time(self, delta_seconds):
        """Avanza el tiempo real del juego y maneja respawns.

        delta_seconds: segundos transcurridos desde la última llamada.
        """
        # Usamos current_time para medir el tiempo del juego
        self.current_time += delta_seconds

        # Manejar timers de respawn si se usan (tank.respawn_timer)
        tanks = []
        if self.teamA_tank:
            tanks.append(self.teamA_tank)
        tanks.extend(self.teamB_tanks)

        for t in tanks:
            if not getattr(t, 'is_alive', True) and getattr(t, 'respawn_timer', 0) > 0:
                t.respawn_timer -= delta_seconds
                if t.respawn_timer <= 0:
                    try:
                        t.respawn()
                    except Exception:
                        t.is_alive = True
                        t.health = 3

    # Nota: is_terminal usa elapsed_time para decidir empates por tiempo