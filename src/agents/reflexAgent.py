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
        for action in legal_actions:
            succesor_game_state = game_state.getSuccessor(self.agent_index, action)
            newPos = succesor_game_state.getTankByIndex(self.agent_index).getPos()
            newPos_enemy = [tank.getPos() for tank in succesor_game_state.getTeamBTanks() if tank.isAlive()]    
        best_action = 'STOP'
        tank = game_state.getTankByIndex(self.agent_index)
        enemy_tanks = game_state.getTeamBTanks()



    def evaluateFunction(self, state, action):
        # Evaluar la acción basándose en múltiples factores
        score = 0
        
        # Factor 1: Distancia a la base enemiga
        # Factor 2: Cobertura disponible
        # Factor 3: Línea de tiro clara al enemigo
        # Factor 4: Riesgo de recibir disparos
        
        return score
