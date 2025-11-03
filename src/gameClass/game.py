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

TIME_PENALTY = 1

class BattleCityState:
    """Clase que representa el estado del juego Battle City.
    Contiene la información de los elementos de un estado del juego.
    Siempre vamos a suponer que el jugador (tanque del equipo A) es el agente 0.
    El equipo B siempre tiene 2 tanques enemigos vivos a menos que se queden sin reservas.
    """
    def __init__(self):
        self.board_size = None        # Tamaño del tablero (board_size x board_size)
        self.teamA_tank = None              # Estado del tanque     
        self.teamB_tanks = []               # Estado de los tanques del enemigo
        self.walls = []                     # Estado de las paredes
        self.base = None                    # Estado de la base del enemigo
        self.bullets = []                   # Estado de las balas
        self.time_limit = 500               # Tiempo límite 
        self.current_time = 0               # Tiempo actual en ticks
        self.reserves_A = 2                 # Reservas de tanques adicionales para el jugador
        self.reserves_B = 6                 # Reservas de tanques adicionales para los enemigos
        self.score = 0                      # Puntaje del juego

    def initialize(self, layout):
        """Inicializa el juego con un layout dado."""
        # Ajustar el tamaño del tablero en base al layout proporcionado
        height = len(layout)
        # Usar el máximo entre ancho/alto para definir board_size (cuadrado)
        self.board_size = height
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
                    self.base = Base(position=pos)
                elif cell == 'X':
                    wall = Wall(position=pos, wall_type='brick')
                    self.walls.append(wall)
                elif cell == 'S':
                    wall = Wall(position=pos, wall_type='steel')
                    self.walls.append(wall)
    
    def getTeamATank(self):
        """Devuelve el tanque del equipo A (jugador)."""
        return self.teamA_tank
    
    def getTeamBTanks(self):
        """Devuelve la lista de tanques del equipo B (enemigos)."""
        return self.teamB_tanks
    
    def getBoardSize(self):
        """Devuelve el tamaño del tablero."""
        return self.board_size
    
    def getWalls(self):
        """Devuelve la lista de paredes."""
        return self.walls
    
    def getBase(self):
        """Devuelve la base."""
        return self.base
    
    def getBullets(self):
        """Devuelve la lista de balas."""
        return self.bullets
    
    def getTimeLimit(self):
        """Devuelve el tiempo límite del juego."""
        return self.time_limit
    
    def getCurrentTime(self):
        """Devuelve el tiempo actual del juego."""
        return self.current_time
    
    def getReservesA(self):
        """Devuelve las reservas de tanques del equipo A."""
        return self.reserves_A
    
    def getReservesB(self):
        """Devuelve las reservas de tanques del equipo B."""
        return self.reserves_B
    
    def isLimitTime(self):
        """Verifica si el juego terminó."""
        return self.current_time >= self.time_limit
    
    def isWin(self):
        """Verifica si el equipo A ganó. (El equipo B se queda sin reservas y ni tanques en el escenario)"""
        return self.reserves_B == 0 and all(not t.isAlive() for t in self.teamB_tanks)

    def isLose(self):
        """Verifica si el equipo B ganó. (El equipo A se queda sin reservas y ni tanques en el escenario, o la base es destruida)"""
        return (self.reserves_A == 0 and not self.teamA_tank.isAlive()) or (self.base.isDestroyed())

    def getLegalActions(self, tankIndex):
        """Obtener acciones legales para un tanque específico"""
        actions = []
        
        if self.isWin() or self.isLose():
            return actions
        
        # Seleccionamos el tanque correspondiente
        tank = None
        if tankIndex == 0:
            tank = self.teamA_tank
        else:
            tank = self.teamB_tanks[tankIndex - 1]
        
        # Verificamos que el tanque esté vivo, no lo está, simplemente es como si no hiciera nada
        if not tank or not tank.isAlive():
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
                    if other_tank.isAlive() and other_tank.getTeam() != tank.getTeam() and other_tank.getPos() == test_pos:
                        actions.append('FIRE')
                        break
                
                # Verificar muros
                blocked = False
                for wall in self.walls:
                    if not wall.isDestroyed() and wall.getPosition() == test_pos:
                        if wall.getType() == 'brick':  # Si es un muro de ladrillo, es un objetivo válido
                            actions.append('FIRE')
                        blocked = True
                        break
                if blocked:
                    break
                    
                test_pos = (test_pos[0] + dx, test_pos[1] + dy)
        
        # Añadir movimientos posibles (si no hay obstáculos)
        x, y = tank.getPos()
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
                    if other_tank != tank and other_tank.isAlive() and other_tank.getPos() == new_pos:
                        can_move = False
                        break
                if not can_move:
                    continue
                        
                # Colisión con base
                if not self.base.isDestroyed() and self.base.getPosition() == new_pos:
                    continue
                        
                actions.append(move)
                
        # Permitir girar la mira en cualquier momento (útil si está atascado o quiere cambiar objetivo)
        actions.extend(['TURN_UP', 'TURN_DOWN', 'TURN_LEFT', 'TURN_RIGHT'])

        # Si no hay acciones de movimiento ni FIRE (aparte de TURN), al menos permitir STOP
        if not actions:
            actions.append('STOP')
            
        return actions

    def getNumAgents(self):
        """Número total de agentes (1 tanque de A + len(teamB_tanks))."""
        return (1 if self.teamA_tank is not None else 0) + len(self.teamB_tanks)

    def getSuccessor(self, tankIndex, action):
        """
        Devuelve un nuevo estado del juego después de aplicar la acción
        del agente 'tankIndex'. Garantiza que el avance de tiempo, balas
        y colisiones se ejecuten una vez por ciclo completo de agentes.
        """
        
        if self.isWin() or self.isLose():
            raise Exception("El juego ya terminó")  # Si el juego ya terminó, no generar sucesores

        state = copy.deepcopy(self) #BattleCityState(self)
        legalActions = state.getLegalActions(tankIndex)
        
        if action not in legalActions:
            raise Exception(f"Acción ilegal {action} para el tanque {tankIndex}")
        
        
        state.applyTankAction(tankIndex, action)
        
        if tankIndex == 0:
            state.score -= TIME_PENALTY
        
        if tankIndex == state.getNumAgents() - 1:
            state.moveBullets()
            state._check_collisions()
            state._handle_deaths_and_respawns()
        
        return state
    
    """def evaluate_state(self):
        Función de evaluación mejorada con énfasis en defensa activa
        score = self.score
        if self.isWin():
            return float('inf')
        elif self.isLose():
            return float('-inf')
        
        posTankA = self.teamA_tank.getPos()
        posBase = self.base.getPosition()
        tankCercano2Base = None
        dist2Base = float('inf')
        
        for tank in self.teamB_tanks:
            if tank.isAlive():
                dist = manhattanDistance(posBase, tank.getPos())
                if dist < dist2Base:
                    dist2Base = dist
                    tankCercano2Base = tank

        if tankCercano2Base is not None:
            dist2Enemy = manhattanDistance(posTankA, tankCercano2Base.getPos())
            score += 20 / (dist2Enemy + 1)  # Recompensar por estar cerca del tanque enemigo más cercano a la base

        score -= 10 * self.reserves_B  # Penalizar por reservas enemigas restantes
        
        return score
"""
    def evaluate_state(self):
        if self.isWin():
            return float('inf')
        elif self.isLose():
            return float('-inf')

        posA = self.teamA_tank.getPos()
        posBase = self.base.getPosition()

        # --- Distancia del jugador a la base (debe protegerla)
        distA2Base = manhattanDistance(posA, posBase)
        protect_score = max(0, 15 - distA2Base) * 3  # recompensa por estar cerca de la base

        # --- Penalización por enemigos cercanos a la base
        danger_score = 0
        for enemy in self.teamB_tanks:
            if enemy.isAlive():
                dist_enemy_base = manhattanDistance(enemy.getPos(), posBase)
                danger_score += max(0, 10 - dist_enemy_base) * 5  # penaliza enemigos cercanos

        # --- Incentivo por atacar tanques enemigos
        attack_score = 0
        for enemy in self.teamB_tanks:
            if enemy.isAlive():
                dist_enemy_player = manhattanDistance(enemy.getPos(), posA)
                attack_score += 10 / (dist_enemy_player + 1)

        # --- Penaliza tiempo y reservas enemigas
        score = -self.reserves_B * 15 - self.current_time * 0.1

        # --- Suma ponderada total
        final_score = protect_score + attack_score - danger_score + score
        return final_score

    def getTankByIndex(self, agentIndex):
        """
        Devuelve el objeto Tank correspondiente al índice global del agente.
        Índice 0 -> tanque del jugador (team A)
        Índices >=1 -> tanques enemigos (team B)
        """
        if agentIndex == 0:
            return getattr(self, "teamA_tank", None)
        else:
            idx = agentIndex - 1
            if 0 <= idx < len(self.teamB_tanks):
                return self.teamB_tanks[idx]
            return None

    def moveBullets(self):
        # Mover sólo las balas activas. Evita que balas desactivadas
        # (por colisiones) sigan avanzando en el mismo tick si no
        # fueron removidas de la lista todavía.
        for b in self.bullets:
            try:
                if b.isActive():
                    b.move()
            except Exception:
                # Fallback: si la bala no expone isActive(), moverla de todos modos
                try:
                    b.move()
                except Exception:
                    pass

    def applyTankAction(self, tankIndex, action):
        """
        Aplica la acción al tanque identificado por tankIndex sobre este objeto juego.
        """
        tank = self.getTankByIndex(tankIndex)
        if tank is None or not tank.is_alive:
            return
        x,y = tank.getPos()
        # movimiento / giro
        if action == 'MOVE_UP':
            tank.direction = 'UP'
            tank.move((x, y + 1))
        elif action == 'MOVE_DOWN':
            tank.direction = 'DOWN'
            tank.move((x, y - 1))
        elif action == 'MOVE_LEFT':
            tank.direction = 'LEFT'
            tank.move((x - 1, y))
        elif action == 'MOVE_RIGHT':
            tank.direction = 'RIGHT'
            tank.move((x + 1, y))
        elif action == 'TURN_UP':
            tank.direction = 'UP'
        elif action == 'TURN_DOWN':
            tank.direction = 'DOWN'
        elif action == 'TURN_LEFT':
            tank.direction = 'LEFT'
        elif action == 'TURN_RIGHT':
            tank.direction = 'RIGHT'
        elif action == 'FIRE':
            # crear bala en la casilla adyacente (manteniendo tu chequeo original)
            if tank.getDirection():
                dx, dy = {'UP': (0, 1), 'DOWN': (0, -1), 'LEFT': (-1, 0), 'RIGHT': (1, 0)}[tank.getDirection()]
                bullet_pos = (x + dx, y + dy)
                if 0 <= bullet_pos[0] < self.board_size and 0 <= bullet_pos[1] < self.board_size:
                    # comprueba colisiones inmediatas (igual que en generateSuccessor)
                    collided = False
                    for wall in self.walls:
                        if not wall.isDestroyed() and wall.getPosition() == bullet_pos:
                            if hasattr(wall, 'takeDamage'):
                                wall.takeDamage(1)
                            else:
                                try:
                                    wall.destroy()
                                except Exception:
                                    pass
                            collided = True
                            break
                    if not collided:
                        all_tanks_next = [self.teamA_tank] + self.teamB_tanks
                        for other_tank in all_tanks_next:
                            if other_tank and other_tank.isAlive() and other_tank.getTeam() != tank.getTeam() and other_tank.getPos() == bullet_pos:
                                if hasattr(other_tank, 'takeDamage'):
                                    other_tank.takeDamage(1)
                                else:
                                    try:
                                        other_tank.destroy()
                                    except Exception:
                                        other_tank.is_alive = False
                                collided = True
                                break
                    if not collided and self.base and (not self.base.isDestroyed()) and self.base.getPosition() == bullet_pos:
                        if hasattr(self.base, 'takeDamage'):
                            self.base.takeDamage()
                        else:
                            try:
                                self.base.is_destroyed = True
                            except Exception:
                                pass
                        collided = True

                    if not collided:
                        new_bullet = Bullet(position=bullet_pos, direction=tank.getDirection(), team=tank.getTeam(), owner_id=tankIndex)
                        self.bullets.append(new_bullet)
        elif action == 'STOP':
            pass

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
        active_bullets = [b for b in self.bullets if b.isActive()]
        removed_ids = set()

        # Agrupar por posición actual (usar la API correcta de Bullet: getPosition)
        pos_map = {}
        for b in active_bullets:
            try:
                pos = b.getPosition()
            except Exception:
                # fallback a posible atributo directo
                pos = getattr(b, 'position', None)
            pos_map.setdefault(pos, []).append(b)

        # Si en una misma celda hay balas de al menos dos equipos diferentes, anularlas todas
        for pos, blist in pos_map.items():
            if len(blist) > 1:
                teams = set(b.getTeam() for b in blist)
                if len(teams) > 1:
                    for b in blist:
                        b.setActive(False)
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
                try:
                    team1 = b1.getTeam()
                    team2 = b2.getTeam()
                    prev1 = b1.getPrevPosition()
                    prev2 = b2.getPrevPosition()
                    pos1 = b1.getPosition()
                    pos2 = b2.getPosition()
                except Exception:
                    # Fallback a atributos directos si la API no está disponible
                    team1 = getattr(b1, 'team', None)
                    team2 = getattr(b2, 'team', None)
                    prev1 = getattr(b1, 'prev_position', None)
                    prev2 = getattr(b2, 'prev_position', None)
                    pos1 = getattr(b1, 'position', None)
                    pos2 = getattr(b2, 'position', None)

                if team1 != team2 and prev1 is not None and prev2 is not None:
                    if pos1 == prev2 and pos2 == prev1:
                        try:
                            b1.setActive(False)
                        except Exception:
                            setattr(b1, 'is_active', False)
                        try:
                            b2.setActive(False)
                        except Exception:
                            setattr(b2, 'is_active', False)
                        removed_ids.add(id(b1))
                        removed_ids.add(id(b2))

        # --- Luego: procesar colisiones restantes de cada bala con muros, tanques y base ---
        for bullet in self.bullets:
            # Omitir balas ya anuladas por colisión entre balas o marcadas inactivas
            if not bullet.isActive() or id(bullet) in removed_ids:
                continue

            removed = False

            # 1) Colisión con muros
            for wall in self.walls:
                if not wall.isDestroyed() and wall.getPosition() == bullet.getPosition():
                    # Dar daño al muro (brick reduce health, steel ignorado)
                    wall.takeDamage(1)
                    # La bala desaparece
                    removed = True
                    bullet.setActive(False)
                    break

            if removed:
                continue

            # 2) Colisión con tanques
            all_tanks = [self.teamA_tank] + self.teamB_tanks
            for tank in all_tanks:
                try:
                    bteam = bullet.getTeam()
                    bpos = bullet.getPosition()
                except Exception:
                    bteam = getattr(bullet, 'team', None)
                    bpos = getattr(bullet, 'position', None)
                if tank and tank.isAlive() and tank.getTeam() != bteam and tank.getPos() == bpos:
                    # Aplicar daño al tanque
                    if hasattr(tank, 'takeDamage'):
                        tank.takeDamage(1)
                    else:
                        try:
                            tank.destroy()
                        except Exception:
                            tank.is_alive = False
                    removed = True
                    try:
                        bullet.setActive(False)
                    except Exception:
                        bullet.is_active = False
                    break

            if removed:
                continue

            # 3) Colisión con la base
            if self.base and (not self.base.isDestroyed()):
                try:
                    base_pos = self.base.getPosition()
                except Exception:
                    base_pos = getattr(self.base, 'position', None)
                try:
                    bpos = bullet.getPosition()
                except Exception:
                    bpos = getattr(bullet, 'position', None)
                if base_pos == bpos:
                    if hasattr(self.base, 'takeDamage'):
                        self.base.takeDamage()
                    else:
                        try:
                            self.base.is_destroyed = True
                        except Exception:
                            pass
                    removed = True
                    try:
                        bullet.setActive(False)
                    except Exception:
                        bullet.is_active = False

            # Si la bala no impactó nada, mantenerla (si sigue dentro del tablero)
            if not removed:
                x, y = bullet.getPosition()
                if 0 <= x < self.board_size and 0 <= y < self.board_size and bullet.isActive():
                    bullets_to_keep.append(bullet)

        # Actualizar la lista de balas activas
        self.bullets = bullets_to_keep

    def _handle_deaths_and_respawns(self):
        """Verifica tanques muertos, resta reservas e inicia respawn."""
        # Manejar muerte/respawn del tanque del jugador
        if self.teamA_tank and not self.teamA_tank.isAlive():
            if self.reserves_A > 0:
                self.reserves_A -= 1
                # Reaparecer instantáneamente en la posición de spawn
                try:
                    self.teamA_tank.respawn()
                except Exception:
                    # si respawn no existe, resetear manualmente
                    self.teamA_tank.position = self.teamA_tank.getSpawnPos()
                    self.teamA_tank.health = 3
                    self.teamA_tank.is_alive = True
            else:
                self.reserves_A = 0

        # Manejar muertes/respawns de enemigos: si mueren y hay reservas, respawnearlos,
        # en otro caso eliminarlos de la lista.
        new_teamB = []
        for tank in self.teamB_tanks:
            if tank.isAlive():
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