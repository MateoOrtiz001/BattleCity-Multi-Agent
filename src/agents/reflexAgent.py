import random
from ..utils import manhattanDistance

class ReflexTankAgent:
    """
    Un agente para el jugador que toma desiciones basadas en una función de evaluación simple.
    Se contruye sobre el parámetro 'script_type', cuyos valores son: 'offensive' o 'defensive'.
    """
    def __init__(self,script_type='offensive'):
        self.agent_index = 0  # Índice del agente jugador
        self.script_type = script_type
        
    
    def getAction(self, game_state):
        legal_actions = game_state.getLegalActions(self.agent_index)

        # Si está muerto o atascado, devuelve STOP
        if 'STOP' in legal_actions and len(legal_actions) == 1:
            return 'STOP'

        # Elige qué comportamiento seguir
        if self.script_type == 'offensive':
            score = self.run_offensiveFunction(game_state, legal_actions)
            bestScore = max(score)
            bestIndices = [index for index in range(len(score)) if score[index] == bestScore]
            chosenIndex = random.choice(bestIndices) # Pick randomly among the best
            return legal_actions[chosenIndex]
        elif self.script_type == 'defensive':
            score = self.run_defensive_script(game_state, legal_actions)
            # Seleccionar la mejor acción igual que en ofensiva
            bestScore = max(score) if score else float('-inf')
            bestIndices = [index for index in range(len(score)) if score[index] == bestScore]
            chosenIndex = random.choice(bestIndices) if bestIndices else 0
            return legal_actions[chosenIndex]
        else:
            return self.run_random_script(legal_actions)
        
    def run_offensiveFunction(self, game_state, legal_actions):
        # Evalua las acciones y elige la mejor para ir a atacar más agresivamente
        score = []

        # Helper: comprobar si existe un enemigo en la dirección del FIRE
        def enemy_in_direction(origin, direction):
            dirs = {'UP': (0,1), 'DOWN': (0,-1), 'LEFT': (-1,0), 'RIGHT': (1,0)}
            dx, dy = dirs.get(direction, (0,0))
            tx, ty = origin
            wall_count = 0
            while 0 <= tx + dx < game_state.getBoardSize() and 0 <= ty + dy < game_state.getBoardSize():
                tx += dx; ty += dy
                # Chequear muros
                for wall in game_state.getWalls():
                    if not wall.isDestroyed() and wall.getPosition() == (tx, ty):
                        if wall.getType() == 'steel':
                            return False
                        else:
                            wall_count += 1
                            if wall_count > 1:
                                return False
                            # brick, la bala podría seguir
                            break

                # Chequear tanques enemigos
                for et in game_state.getTeamBTanks():
                    if et is None:
                        continue
                    if et.isAlive() and et.getPos() == (tx, ty):
                        # si hay como máximo 1 pared entre origen y objetivo, consideramos que hay un objetivo
                        if wall_count <= 1:
                            return True
                        return False

            return False

        # Estado actual del tanque (antes de aplicar la acción)
        cur_tank = game_state.getTeamATank()
        cur_pos = cur_tank.getPos() if cur_tank and cur_tank.isAlive() else None

        for action in legal_actions:
            # Priorizar disparos que apunten a un enemigo vivo en línea de fuego
            if isinstance(action, str) and action.startswith('FIRE_') and cur_pos is not None:
                _, dir = action.split('_', 1)
                if enemy_in_direction(cur_pos, dir):
                    # Score muy alto para asegurar prioridad frente a movimientos
                    score.append(1000.0)
                    continue

            # Caso general: estimar por distancia en el sucesor
            try:
                succesor_game_state = game_state.getSuccessor(self.agent_index, action)
                tank = succesor_game_state.getTeamATank()
                enemy_tanks = succesor_game_state.getTeamBTanks()
                newPos = tank.getPos()
                enemy_positions = [t.getPos() for t in enemy_tanks if t.isAlive()]

                if enemy_positions:
                    dists = [manhattanDistance(newPos, pos) for pos in enemy_positions]
                    min_dist = min(dists)
                    action_score = 10.0 / (min_dist + 1)
                else:
                    action_score = 0.0
            except Exception:
                # En caso de que getSuccessor falle por cualquier razón, asignar score neutro
                action_score = 0.0

            if action == 'STOP':
                action_score -= 1.0

            score.append(action_score)

        return score
              
    def run_defensive_script(self, game_state, legal_actions):
        """Comportamiento defensivo simple: priorizar mantenerse cerca de la base y
        interceptar enemigos que se acerquen. También prioriza disparos que puedan
        impactar a un enemigo (igual que en ofensiva).
        """
        score = []

        # Reusar helper para detectar enemigos en dirección de FIRE
        def enemy_in_direction(origin, direction):
            dirs = {'UP': (0,1), 'DOWN': (0,-1), 'LEFT': (-1,0), 'RIGHT': (1,0)}
            dx, dy = dirs.get(direction, (0,0))
            tx, ty = origin
            wall_count = 0
            while 0 <= tx + dx < game_state.getBoardSize() and 0 <= ty + dy < game_state.getBoardSize():
                tx += dx; ty += dy
                # Chequear muros
                for wall in game_state.getWalls():
                    if not wall.isDestroyed() and wall.getPosition() == (tx, ty):
                        if wall.getType() == 'steel':
                            return False
                        else:
                            wall_count += 1
                            if wall_count > 1:
                                return False
                            break

                # Chequear tanques enemigos
                for et in game_state.getTeamBTanks():
                    if et is None:
                        continue
                    if et.isAlive() and et.getPos() == (tx, ty):
                        if wall_count <= 1:
                            return True
                        return False

            return False

        base = game_state.getBase()
        try:
            base_pos = base.getPosition()
        except Exception:
            base_pos = getattr(base, 'position', None)

        cur_tank = game_state.getTeamATank()
        cur_pos = cur_tank.getPos() if cur_tank and cur_tank.isAlive() else None

        for action in legal_actions:
            # Priorizar FIRE si apunta a enemigo
            if isinstance(action, str) and action.startswith('FIRE_') and cur_pos is not None:
                _, dir = action.split('_', 1)
                if enemy_in_direction(cur_pos, dir):
                    score.append(1000.0)
                    continue

            # Evaluar posición sucesora
            try:
                succ = game_state.getSuccessor(self.agent_index, action)
                tank = succ.getTeamATank()
                newPos = tank.getPos()
            except Exception:
                newPos = cur_pos

            # Distancia a la base (queremos estar cerca -> mayor score)
            if base_pos is not None and newPos is not None:
                dist_base = manhattanDistance(newPos, base_pos)
                score_base = 10.0 / (dist_base + 1)
            else:
                score_base = 0.0

            # Distancia al enemigo más cercano (queremos interceptar => estar relativamente cerca)
            enemy_positions = [t.getPos() for t in game_state.getTeamBTanks() if t.isAlive()]
            if enemy_positions and newPos is not None:
                dists = [manhattanDistance(newPos, p) for p in enemy_positions]
                min_enemy = min(dists)
                score_enemy = 8.0 / (min_enemy + 1)
            else:
                score_enemy = 0.0

            action_score = score_base + score_enemy
            if action == 'STOP':
                action_score -= 0.5

            score.append(action_score)

        # Elegir la acción con mayor score (se delega a getAction)
        # Pero devolver lista de scores para compatibilidad
        return score

    def run_random_script(self, legal_actions):
        return random.choice(legal_actions)
        

