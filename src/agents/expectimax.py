from ..utils import manhattanDistance, lookup
import time

class ExpectimaxAgent():
    """
      Your expectimax agent (question 4)
    """
    def __init__(self, depth='2', tankIndex=0):
        self.agentIndex = tankIndex
        self.depth = int(depth)
        # Para búsqueda iterativa
        self.start_time = 0
        self.time_limit = 1.0

    def getAction(self, gameState):
        """
        Returns the expectimax action using self.depth and self.evaluationFunction

        All ghosts should be modeled as choosing uniformly at random from their
        legal moves.
        """
        "*** YOUR CODE HERE ***"
        num_agents = gameState.getNumAgents()

        def probabilityActions(gameState, agentIndex):
            """Devuelve un dict action->probabilidad para el agente `agentIndex`.
            Heurística simple: dar prob 0.5 a la mejor acción (la que reduce la distancia
            a la base) y repartir 0.5 entre las demás. La distribución está normalizada.
            """
            legalActions = gameState.getLegalActions(agentIndex)
            actionProbabilities = {}
            if not legalActions:
                return actionProbabilities

            # Asumimos agentIndex >= 1 aquí (agentes enemigos) y que teamB_tanks está
            # indexado desde 0 correspondiente a agentIndex == 1
            tank = gameState.teamB_tanks[agentIndex - 1]
            basePos = gameState.base.position
            minDist = manhattanDistance(tank.position, basePos)

            # Seleccionar una acción por defecto
            bestAction = legalActions[0]

            # Buscar acción que reduzca más la distancia (entre MOVE_*)
            for action in legalActions:
                if action.startswith('MOVE_'):
                    tankPos = tank.position
                    if action == 'MOVE_UP': nextPos = (tankPos[0], tankPos[1] + 1)
                    elif action == 'MOVE_DOWN': nextPos = (tankPos[0], tankPos[1] - 1)
                    elif action == 'MOVE_LEFT': nextPos = (tankPos[0] - 1, tankPos[1])
                    elif action == 'MOVE_RIGHT': nextPos = (tankPos[0] + 1, tankPos[1])
                    else:
                        continue

                    dist = manhattanDistance(nextPos, basePos)
                    if dist < minDist:
                        minDist = dist
                        bestAction = action

            n = len(legalActions)
            if n == 1:
                actionProbabilities[legalActions[0]] = 1.0
                return actionProbabilities

            # Distribución: 0.5 al mejor, resto uniformemente al resto
            p_best = 0.5
            p_other = 0.5 / (n - 1)
            for action in legalActions:
                actionProbabilities[action] = p_other
            actionProbabilities[bestAction] = p_best

            return actionProbabilities
                
        def max_value(state,depth,agent_index, max_depth):
            v = float('-inf')
            next_agent = (agent_index + 1) % num_agents
            if next_agent == 0:
                next_depth = depth + 1
            else:
                next_depth = depth
            for action in state.getLegalActions(agent_index):
                successor = state.generateSuccessor(agent_index,action)
                eval = expectimax(successor,next_depth,max_depth,next_agent)
                v = max(v, eval)
            return v
        def exp_value(state,depth,agent_index, max_depth):
            v = 0
            next_agent = (agent_index + 1) % num_agents
            if next_agent == 0:
                next_depth = depth + 1
            else:
                next_depth = depth
            prob = probabilityActions(state, agent_index)
            for action in state.getLegalActions(agent_index):
                p = prob.get(action, 0)
                successor = state.generateSuccessor(agent_index,action)
                v += p * expectimax(successor, next_depth, max_depth, next_agent)
            return v
                
        def expectimax(gameState, depth, max_depth, agent_index):
            # Corte por profundidad o estado terminal
            if depth >= max_depth or gameState.is_terminal():
                return gameState.evaluate_state(gameState.getState())
            if agent_index == 0:
                return max_value(gameState, depth, agent_index, max_depth)
            else:
                return exp_value(gameState, depth, agent_index, max_depth)
        # --- Iterative deepening por turnos completos (4 niveles por turno) ---
        import time
        self.start_time = time.time()

        legal_actions = gameState.getLegalActions(0)
        if not legal_actions:
            return 'STOP'

        best_overall_action = legal_actions[0]

        # depth en la interfaz del agente está en "turnos"; cada turno completo son 4 niveles
        for current_max in range(4, (self.depth * 4) + 1, 4):
            # comprobar tiempo
            if time.time() - self.start_time > self.time_limit:
                break

            current_best_action = None
            current_best_score = float('-inf')

            next_agent = (0 + 1) % num_agents
            for action in legal_actions:
                if time.time() - self.start_time > self.time_limit:
                    break
                successor = gameState.generateSuccessor(0, action)
                val = expectimax(successor, 0, current_max, next_agent)
                if val > current_best_score:
                    current_best_score = val
                    current_best_action = action

            if current_best_action is not None:
                best_overall_action = current_best_action

        return best_overall_action
    
