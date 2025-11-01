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
        # Mapeo opcional de controladores externos por índice de agente (1..n)
        # Por ejemplo: {1: ScriptedEnemyAgent(1), 2: ScriptedEnemyAgent(2)}
        # Estos controladores serán respetados por los algoritmos de búsqueda
        # y pueden ser usados por el bucle de juego para obtener acciones.
        self.scripted_agents = {}
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
                    # Antes de añadir la bala, comprobar colisión inmediata en la casilla de spawn
                    collided = False

                    # 1) Colisión con muros en la posición inicial
                    for wall in next_game.walls:
                        if not wall.is_destroyed and wall.position == bullet_pos:
                            if hasattr(wall, 'takeDamage'):
                                wall.takeDamage(1)
                            else:
                                try:
                                    wall.destroy()
                                except Exception:
                                    pass
                            collided = True
                            break

                    # 2) Colisión con tanques en la posición inicial
                    if not collided:
                        all_tanks_next = [next_game.teamA_tank] + next_game.teamB_tanks
                        for other_tank in all_tanks_next:
                            if other_tank and getattr(other_tank, 'is_alive', False) and other_tank.team != tank.team and other_tank.position == bullet_pos:
                                if hasattr(other_tank, 'takeDamage'):
                                    other_tank.takeDamage(1)
                                else:
                                    try:
                                        other_tank.destroy()
                                    except Exception:
                                        other_tank.is_alive = False
                                collided = True
                                break

                    # 3) Colisión con la base en la posición inicial
                    if not collided and next_game.base and (not next_game.base.isDestroyed()) and next_game.base.position == bullet_pos:
                        if hasattr(next_game.base, 'takeDamage'):
                            next_game.base.takeDamage()
                        else:
                            try:
                                next_game.base.is_destroyed = True
                            except Exception:
                                pass
                        collided = True

                    # Si no colisionó inmediatamente, añadimos la bala para que siga su trayectoria
                    if not collided:
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
        if isinstance(state, dict):
            s = state
        else:
            s = self.getState()

        base = s['base']
        tankA = s['teamA_tank']
        teamB_tanks = s['teamB_tanks']
        walls = s['walls']
        reserves_A = s['reserves_A']
        reserves_B = s['reserves_B']
        current_time = s['current_time']

        # terminales
        if base['is_destroyed']:
            return float('-inf')
        if reserves_B == 0:
            return float('inf')
        if reserves_A == 0:
            return float('-inf')
        if current_time >= self.time_limit:
            return 0

        score = 0.0

        # reservas
        score += 5000 * reserves_A
        score -= 3000 * reserves_B

        # salud tanque A
        score += 50 * tankA['health']

        pos_base = base['position']
        pos_A = tankA['position']

        # --- defensa ---
        # enemigos cerca de la base
        min_dist_enemy = float('inf')
        avg_enemy_dist = 0
        alive_enemies = 0
        for t in teamB_tanks:
            if t['is_alive']:
                d = manhattanDistance(t['position'], pos_base)
                avg_enemy_dist += d
                alive_enemies += 1
                if d < min_dist_enemy:
                    min_dist_enemy = d

        if alive_enemies > 0:
            avg_enemy_dist /= alive_enemies

        # castigo si hay enemigos muy cerca de la base
        if min_dist_enemy < 5:
            score -= 100 * (5 - min_dist_enemy)

        # --- ataque ---
        # incentivo por acercarse a enemigos
        if alive_enemies > 0:
            for t in teamB_tanks:
                if t['is_alive']:
                    d = manhattanDistance(pos_A, t['position'])
                    score += 300 * (10 - d)

        # --- defensa pasiva: cuidar muros cercanos a la base ---
        for w in walls:
            if not w['is_destroyed']:
                if manhattanDistance(w['position'], pos_base) <= 2:
                    score += 250 * w['health']
            else:
                if manhattanDistance(w['position'], pos_base) <= 2:
                    score -= 500

        # --- posición estratégica ---
        # penalizar si el tanque se aleja demasiado de la base (>4 celdas)
        dist_to_base = manhattanDistance(pos_A, pos_base)
        if dist_to_base > 4:
            score -= 500 * (dist_to_base - 4)

        # --- bonus si tiene línea de tiro a enemigos o base ---
        visible_targets = 0
        for t in teamB_tanks:
            if t['is_alive'] and self._has_line_of_fire(tankA, t['position'], walls):
                visible_targets += 1
        score += 30 * visible_targets

        return score


    def _has_line_of_fire(self, tankA, target_pos, walls):
        """Devuelve True si no hay muro entre el tanque y el objetivo."""
        x0, y0 = tankA['position']
        x1, y1 = target_pos
        if x0 == x1:
            dy = 1 if y1 > y0 else -1
            for y in range(y0 + dy, y1, dy):
                if any((w['position'] == (x0, y) and not w['is_destroyed']) for w in walls):
                    return False
            return True
        elif y0 == y1:
            dx = 1 if x1 > x0 else -1
            for x in range(x0 + dx, x1, dx):
                if any((w['position'] == (x, y0) and not w['is_destroyed']) for w in walls):
                    return False
            return True
        return False


    def _check_collisions(self):
        """Verifica colisiones de balas con muros, tanques y la base."""
        bullets_to_keep = []

        # --- Primero: detectar colisiones entre balas (misma celda y choques cabeza-a-cabeza) ---
        active_bullets = [b for b in self.bullets if getattr(b, 'is_active', True)]
        removed_ids = set()

        # Agrupar por posición actual
        pos_map = {}
        for b in active_bullets:
            pos_map.setdefault(b.position, []).append(b)

        # Si en una misma celda hay balas de al menos dos equipos diferentes, anularlas todas
        for pos, blist in pos_map.items():
            if len(blist) > 1:
                teams = set(b.team for b in blist)
                if len(teams) > 1:
                    for b in blist:
                        b.is_active = False
                        removed_ids.add(id(b))

        # Detectar choques cabeza-a-cabeza (intercambio de posiciones entre ticks)
        n = len(active_bullets)
        for i in range(n):
            b1 = active_bullets[i]
            if id(b1) in removed_ids:
                continue
            for j in range(i + 1, n):
                b2 = active_bullets[j]
                if id(b2) in removed_ids:
                    continue
                # Solo considerar si son de equipos diferentes y hay posiciones prev/current disponibles
                if b1.team != b2.team and getattr(b1, 'prev_position', None) is not None and getattr(b2, 'prev_position', None) is not None:
                    if b1.position == b2.prev_position and b2.position == b1.prev_position:
                        b1.is_active = False
                        b2.is_active = False
                        removed_ids.add(id(b1))
                        removed_ids.add(id(b2))

        # --- Luego: procesar colisiones restantes de cada bala con muros, tanques y base ---
        for bullet in self.bullets:
            # Omitir balas ya anuladas por colisión entre balas o marcadas inactivas
            if not getattr(bullet, 'is_active', True) or id(bullet) in removed_ids:
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
                    bullet.is_active = False
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
                    bullet.is_active = False
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
                bullet.is_active = False

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