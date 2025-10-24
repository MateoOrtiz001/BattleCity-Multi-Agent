
from battleCity_Class.tank import Tank

class ReflexTankAgent(Tank):
    def getAction(self, state):
        actions = state.getLegalActions(self.index)
        
        # Evaluar cada acción basándose en:
        # - Distancia a la base del jugador
        # - Cobertura disponible
        # - Línea de tiro clara al jugador
        # - Riesgo de recibir disparos
        
        return self.evaluateActions(state, actions)
    
    def evaluateFunction(self, state, action):
        # Evaluar la acción basándose en múltiples factores
        score = 0
        
        # Factor 1: Distancia a la base enemiga
        # Factor 2: Cobertura disponible
        # Factor 3: Línea de tiro clara al enemigo
        # Factor 4: Riesgo de recibir disparos
        
        return score

    def evaluateActions(self, state, actions):
        best_score = float('-inf')
        best_action = None

        for action in actions:
            score = self.evaluateFunction(state, action)
            if score > best_score:
                best_score = score
                best_action = action

        return best_action