from ..utils import manhattanDistance
import time
import random

class ExpectimaxAgent:
    def __init__(self, depth=2, time_limit=None):
        self.depth = depth
        self.time_limit = time_limit
        self.start_time = None
        self.node_count = 0   # <--- NUEVO

    def is_time_exceeded(self):
        return (
            self.time_limit is not None
            and (time.time() - self.start_time) > self.time_limit
        )

    def getAction(self, gameState):
        self.start_time = time.time()
        self.node_count = 0  # <--- Reiniciar contador en cada decisión

        num_agents = gameState.getNumAgents()
        best_overall_score = float("-inf")
        best_overall_action = None

        def expectimax(state, depth, max_depth, agent_index):
            # --- Contamos cada expansión ---
            self.node_count += 1

            # Condición de parada
            if depth >= max_depth or self.is_time_exceeded() or state.isWin() or state.isLose() or state.isLimitTime():
                return state.evaluate_state()

            next_agent = (agent_index + 1) % num_agents
            next_depth = depth + 1
            legal_actions = state.getLegalActions(agent_index)
            if not legal_actions:
                return state.evaluate_state()

            # MAX node
            if agent_index == 0:
                value = float("-inf")
                for action in legal_actions:
                    if self.is_time_exceeded():
                        break
                    succ = state.getSuccessor(agent_index, action)
                    eval_val = expectimax(succ, next_depth, max_depth, next_agent)
                    value = max(value, eval_val)
                return value
            # CHANCE node
            else:
                total = 0.0
                prob = self.probabilityActions(state, agent_index, legal_actions)
                for action in legal_actions:
                    if self.is_time_exceeded():
                        break
                    succ = state.getSuccessor(agent_index, action)
                    total += prob[action] * expectimax(succ, next_depth, max_depth, next_agent)
                return total

        # --- Iterative deepening ---
        for current_max in range(3, (self.depth * 3) + 1, 3):
            if self.is_time_exceeded():
                break

            current_best_action = None
            current_best_score = float("-inf")

            for action in gameState.getLegalActions(0):
                if self.is_time_exceeded():
                    break
                successor = gameState.getSuccessor(0, action)
                val = expectimax(successor, 0, current_max, 0)
                if val > current_best_score:
                    current_best_score = val
                    current_best_action = action

            if current_best_action is not None:
                best_overall_action = current_best_action
                best_overall_score = current_best_score

            # --- Mostrar progreso por iteración ---
            print(f"[Expectimax] Profundidad {current_max}: nodos expandidos = {self.node_count}")

        return best_overall_action

    
    def probabilityActions(self, state, agentIndex, legalActions):
        """
        Devuelve una distribución de probabilidad suave para las acciones del enemigo.
        Se priorizan las acciones más cercanas a la base enemiga.
        """
        probs = {}
        if not legalActions:
            return {}

        best_action = legalActions[0]
        best_score = float("inf")

        enemy = state.teamB_tanks[agentIndex - 1] if agentIndex > 0 and len(state.teamB_tanks) >= agentIndex else None
        if enemy is None or not enemy.isAlive():
            # Distribución uniforme si el tanque enemigo está muerto
            uniform = 1.0 / len(legalActions)
            return {a: uniform for a in legalActions}

        for action in legalActions:
            succ = state.getSuccessor(agentIndex, action)
            # heurística simple: distancia a base enemiga
            base_pos = succ.getBase().getPosition() if agentIndex != 0 else state.getTeamBBase().getPosition()
            dist = manhattanDistance(enemy.getPos(), base_pos)
            if dist < best_score:
                best_score, best_action = dist, action

        # Distribución suave (acción mejor con 0.6, resto uniforme)
        for action in legalActions:
            probs[action] = 0.8 if action == best_action else 0.2 / (len(legalActions) - 1)
        return probs

class ExpectimaxAlphaBetaAgent:
    def __init__(self, evalFn='evaluate_state', depth=2):
        self.index = 0
        self.evaluationFunction = evalFn
        self.depth = depth

    def getAction(self, gameState):
        num_agents = gameState.getNumAgents()
        root_index = self.index

        def expectimax(state, depth, agent_index):
            if depth == self.depth or state.isTerminal():
                return self.evaluationFunction(state.getState())

            next_agent = (agent_index + 1) % num_agents
            next_depth = depth + 1 if next_agent == root_index else depth

            legal_actions = state.getLegalActions(agent_index)
            if not legal_actions:
                return self.evaluationFunction(state.getState())

            if agent_index == root_index:  # MAX
                return max(expectimax(state.generateSuccessor(agent_index, a), next_depth, next_agent)
                           for a in legal_actions)
            else:  # EXPECT
                probs = self.probabilityActions(state, agent_index, legal_actions)
                return sum(probs[a] * expectimax(state.generateSuccessor(agent_index, a),
                                                 next_depth, next_agent) for a in legal_actions)

        best_score = float("-inf")
        best_action = None
        for action in gameState.getLegalActions(root_index):
            succ = gameState.generateSuccessor(root_index, action)
            value = expectimax(succ, 0, (root_index + 1) % num_agents)
            if value > best_score:
                best_score, best_action = value, action
        return best_action

    def probabilityActions(self, state, agentIndex, legalActions):
        """
        Devuelve una distribución de probabilidad suave para las acciones del enemigo.
        Se priorizan las acciones más cercanas a la base enemiga.
        """
        probs = {}
        if not legalActions:
            return {}

        # Evita usar agentIndex como índice: usa siempre 0 inicial
        best_action = legalActions[0]
        best_score = float("inf")

        enemy = state.teamB_tanks[agentIndex - 1] if agentIndex > 0 and len(state.teamB_tanks) >= agentIndex else None
        if enemy is None or not enemy.is_alive:
            # Distribución uniforme si el tanque enemigo está muerto
            uniform = 1.0 / len(legalActions)
            return {a: uniform for a in legalActions}

        for action in legalActions:
            succ = state.generateSuccessor(agentIndex, action)
            # heurística simple: distancia a base enemiga
            base_pos = state.teamA_base if agentIndex != 0 else state.teamB_base
            dist = state.manhattanDistance(enemy.position, base_pos)
            if dist < best_score:
                best_score, best_action = dist, action

        # Distribución suave (acción mejor con 0.6, resto uniforme)
        for action in legalActions:
            probs[action] = 0.6 if action == best_action else 0.4 / (len(legalActions) - 1)
        return probs