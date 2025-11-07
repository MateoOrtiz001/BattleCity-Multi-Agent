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
            return self.run_defensive_script(game_state, legal_actions)
        else:
            return self.run_random_script(legal_actions)
        
    def run_offensiveFunction(self, game_state, legal_actions):
        # Evalua las acciones y elige la mejor para ir a atacar más agresivamente
        
        score = []
        minimal_distance = float('inf')
        for action in legal_actions:
            succesor_game_state = game_state.getSuccessor(self.agent_index, action)
            tank = succesor_game_state.getTeamATank()
            enemy_tanks = succesor_game_state.getTeamBTanks()
            newPos = tank.getPos()
            newPos_enemy = [tank.getPos() for tank in enemy_tanks if tank.isAlive()]  
            dist_2_enemies = [manhattanDistance(newPos, enemy_pos) for enemy_pos in newPos_enemy]
            min_dist = min(dist_2_enemies) if dist_2_enemies else 0
            if min_dist < minimal_distance:
                minimal_distance = min_dist
            # Evaluar la acción basándose en la distancia al enemigo más cercano
            score.append(5/minimal_distance)

        return score
              
        
