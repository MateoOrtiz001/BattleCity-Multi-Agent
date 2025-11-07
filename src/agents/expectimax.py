from ..utils import manhattanDistance
import time
import random
import threading
import concurrent.futures

class ExpectimaxAgent:
    """Algoritmo Expectimax con profundización iterativa."""
    def __init__(self, depth=2, time_limit=None, debug=False):
        self.depth = depth
        self.time_limit = time_limit
        self.start_time = None
        self.node_count = 0   # <--- NUEVO
        self.debug = debug

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
        root_index = getattr(self, 'index', 0)

        def expectimax(state, depth, max_depth, agent_index):
            # --- Contamos cada expansión ---
            self.node_count += 1

            # Condición de parada
            if depth >= max_depth or self.is_time_exceeded() or state.isWin() or state.isLose() or state.isLimitTime():
                return state.evaluate_state()

            # Use the current number of agents in 'state' (puede cambiar dinámicamente)
            curr_num_agents = state.getNumAgents()
            if curr_num_agents <= 0:
                return state.evaluate_state()
            next_agent = (agent_index + 1) % curr_num_agents
            # Increment depth only when we cycle back to the root agent
            next_depth = depth + 1 if next_agent == root_index else depth
            legal_actions = state.getLegalActions(agent_index)
            #print(f"[DEBUG] Acciones legales disponibles: {legal_actions}, para agente={agent_index} en profundidad={depth}")
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
        # step by number of agents to make `self.depth` mean "turnos completos"
        step = num_agents if num_agents > 0 else 1
        for current_max in range(step, (self.depth * step) + 1, step):
            if self.is_time_exceeded() or current_max > self.depth:
                break

            current_best_action = None
            current_best_score = float("-inf")

            for action in gameState.getLegalActions(root_index):
                if self.is_time_exceeded():
                    break
                successor = gameState.getSuccessor(root_index, action)
                val = expectimax(successor, 0, current_max, (root_index + 1) % num_agents)
                if self.debug:
                    try:
                        ev = successor.evaluate_state()
                    except Exception:
                        ev = None
                    print(f"[DEBUG][IDS {current_max}] action={action} -> expectimax={val} eval(successor)={ev}")
                if val > current_best_score:
                    current_best_score = val
                    current_best_action = action

            if current_best_action is not None:
                best_overall_action = current_best_action
                best_overall_score = current_best_score

            # --- Mostrar progreso por iteración ---
            if self.debug:
                print(f"[Expectimax] Profundidad {current_max}: nodos expandidos = {self.node_count}")
            else:
                # mostrar progreso ligero si no está silenciado
                try:
                    if not getattr(self, 'suppress_output', False):
                        print(f"[Expectimax] Profundidad {current_max}: nodos expandidos = {self.node_count}")
                except Exception:
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

        # Obtener el tanque correspondiente de forma segura
        enemy = None
        try:
            enemy = state.getTankByIndex(agentIndex)
        except Exception:
            try:
                enemy = state.teamB_tanks[agentIndex - 1] if agentIndex > 0 and len(state.teamB_tanks) >= agentIndex else None
            except Exception:
                enemy = None

        if enemy is None or not getattr(enemy, 'isAlive', lambda: False)():
            # Distribución uniforme si el tanque enemigo está muerto
            uniform = 1.0 / len(legalActions)
            return {a: uniform for a in legalActions}

        for action in legalActions:
            # evaluar la posición del enemigo tras realizar la acción
            try:
                succ = state.getSuccessor(agentIndex, action)
                succ_enemy = None
                try:
                    succ_enemy = succ.getTankByIndex(agentIndex)
                except Exception:
                    # fallback: buscar en estructuras internas
                    if hasattr(succ, 'teamB_tanks') and agentIndex > 0:
                        succ_enemy = succ.teamB_tanks[agentIndex - 1] if len(succ.teamB_tanks) >= agentIndex else None
                if succ_enemy is None:
                    # si no podemos obtener el tanque sucesor, usar la posición actual
                    enemy_pos = getattr(enemy, 'getPos', lambda: getattr(enemy, 'position', None))()
                else:
                    enemy_pos = getattr(succ_enemy, 'getPos', lambda: getattr(succ_enemy, 'position', None))()
                base_pos = succ.getBase().getPosition() if hasattr(succ, 'getBase') else succ.getBase().getPosition()
                dist = manhattanDistance(enemy_pos, base_pos)
            except Exception:
                # en caso de fallo de la simulación, usar la posición actual del enemy
                try:
                    base_pos = state.getBase().getPosition()
                except Exception:
                    base_pos = None
                enemy_pos = getattr(enemy, 'getPos', lambda: getattr(enemy, 'position', None))()
                if base_pos is None or enemy_pos is None:
                    dist = float('inf')
                else:
                    dist = manhattanDistance(enemy_pos, base_pos)

            if dist < best_score:
                best_score, best_action = dist, action

        # Distribución suave (acción mejor con 0.6, resto uniforme)
        for action in legalActions:
            if len(legalActions) == 1:
                probs[action] = 1.0
            else:
                probs[action] = 0.6 if action == best_action else 0.4 / (len(legalActions) - 1)
        return probs


class ParallelExpectimaxAgent(ExpectimaxAgent):
    """Algoritmo Expectimax que corre en paralelo."""
    def __init__(self, depth=2, time_limit=None, debug=False, max_workers=None):
        super().__init__(depth=depth, time_limit=time_limit, debug=debug)
        # max_workers for ThreadPoolExecutor; None -> default heuristic
        self.max_workers = max_workers

    def getAction(self, gameState):
        # initialize timing and node counter (thread-safe)
        self.start_time = time.time()
        self.node_count = 0
        self._node_count_lock = threading.Lock()

        num_agents = gameState.getNumAgents()
        best_overall_score = float("-inf")
        best_overall_action = None
        root_index = getattr(self, 'index', 0)

        def expectimax(state, depth, max_depth, agent_index):
            # thread-safe increment
            try:
                with self._node_count_lock:
                    self.node_count += 1
            except Exception:
                # fallback (shouldn't happen) to non-locked increment
                self.node_count += 1

            # stopping conditions
            if depth >= max_depth or self.is_time_exceeded() or state.isWin() or state.isLose() or state.isLimitTime():
                return state.evaluate_state()

            curr_num_agents = state.getNumAgents()
            if curr_num_agents <= 0:
                return state.evaluate_state()
            next_agent = (agent_index + 1) % curr_num_agents
            next_depth = depth + 1 if next_agent == root_index else depth
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
                    total += prob.get(action, 0.0) * expectimax(succ, next_depth, max_depth, next_agent)
                return total

        # --- Iterative deepening (same step logic as ExpectimaxAgent) ---
        step = num_agents if num_agents > 0 else 1
        for current_max in range(step, (self.depth * step) + 1, step):
            if self.is_time_exceeded() or current_max > self.depth:
                break

            current_best_action = None
            current_best_score = float("-inf")

            legal_actions = gameState.getLegalActions(root_index)
            if not legal_actions:
                continue

            # choose number of workers
            max_workers = self.max_workers or min(32, len(legal_actions))
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as ex:
                # submit one task per root legal action
                future_to_action = {ex.submit(expectimax, gameState.getSuccessor(root_index, a), 0, current_max, (root_index + 1) % num_agents): a for a in legal_actions}

                # collect results as they complete
                for fut in concurrent.futures.as_completed(future_to_action):
                    action = future_to_action[fut]
                    if self.is_time_exceeded():
                        break
                    try:
                        val = fut.result()
                    except Exception as e:
                        if self.debug:
                            print(f"[ParallelExpectimax] exception evaluating action {action}: {e}")
                        val = float("-inf")

                    if self.debug:
                        try:
                            ev = gameState.getSuccessor(root_index, action).evaluate_state()
                        except Exception:
                            ev = None
                        print(f"[DEBUG][P-IDS {current_max}] action={action} -> expectimax={val} eval(successor)={ev}")

                    if val > current_best_score:
                        current_best_score = val
                        current_best_action = action

            if current_best_action is not None:
                best_overall_action = current_best_action
                best_overall_score = current_best_score

            # --- Mostrar progreso por iteración ---
            if self.debug:
                print(f"[ParallelExpectimax] Profundidad {current_max}: nodos expandidos = {self.node_count}")
            else:
                try:
                    if not getattr(self, 'suppress_output', False):
                        print(f"[ParallelExpectimax] Profundidad {current_max}: nodos expandidos = {self.node_count}")
                except Exception:
                    print(f"[ParallelExpectimax] Profundidad {current_max}: nodos expandidos = {self.node_count}")

        return best_overall_action