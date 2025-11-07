from ..utils import manhattanDistance, lookup
import time
import threading
import concurrent.futures
import os


class MinimaxAgent():
    """
    Your minimax agent (question 2)
    """
    def __init__(self, depth = '1', tankIndex = 0):
        self.index = tankIndex  # Índice del tanque que controla este agente
        self.depth = int(depth)  
        self.expanded_nodes = 0
        # Para permitir un corte por tiempo similar a AlphaBetaAgent
        self.start_time = 0
        self.time_limit = 1.0
        
    
    def is_time_exceeded(self):
        """Verifica si se ha excedido el límite de tiempo"""
        return (
            self.time_limit is not None
            and (time.time() - self.start_time) > self.time_limit
        )

    def getAction(self, gameState):
        """Minimax search for multi-agent BattleCity.

        This implementation treats the agent with index self.index as the
        maximizing player; all other agents are treated as adversaries
        (minimizers). Depth is counted in "full-turns": we increment the
        depth when we cycle back to the root agent.
        """
        import time

        num_tanks = gameState.getNumAgents()

        # Use the attribute 'index' if present, otherwise assume 0
        root_index = getattr(self, 'index', 0)

        self.start_time = time.time()

        def minimax(state, depth, agent_index):
            self.expanded_nodes += 1

            # Terminal or max depth reached
            if depth >= self.depth or state.is_terminal() or self.is_time_exceeded():
                return state.evaluate_state()

            next_agent = (agent_index + 1) % num_tanks
            # Increase depth when we've completed a full cycle back to root
            next_depth = depth + 1 if next_agent == root_index else depth

            # If this agent is the maximizer (the one that called getAction)
            if agent_index == root_index:
                v = float('-inf')
                for action in state.getLegalActions(agent_index):
                    if time.time() - self.start_time > self.time_limit:
                        break
                    succ = state.getSuccessor(agent_index, action)
                    v = max(v, minimax(succ, next_depth, next_agent))
                return v
            else:
                # Minimizing adversary
                v = float('inf')
                for action in state.getLegalActions(agent_index):
                    if time.time() - self.start_time > self.time_limit:
                        break
                    succ = state.getSuccessor(agent_index, action)
                    v = min(v, minimax(succ, next_depth, next_agent))
                return v

        legal_actions = gameState.getLegalActions(root_index)
        if not legal_actions:
            return 'STOP'

        best_action = legal_actions[0]
        best_score = float('-inf')

        # Evaluate each root action
        for action in legal_actions:
            if time.time() - self.start_time > self.time_limit:
                break
            succ = gameState.getSuccessor(root_index, action)
            score = minimax(succ, 0, (root_index + 1) % num_tanks)
            if score > best_score:
                best_score = score
                best_action = action

        return best_action

class AlphaBetaAgent():
    """
    Your minimax agent with alpha-beta pruning and iterative deepening for Battle City
    """
    def __init__(self, depth = '1', tankIndex = 0, time_limit=1.0):
        self.index = tankIndex  # Índice del tanque que controla este agente
        self.depth = int(depth)  # Profundidad máxima para IDS
        self.expanded_nodes = 0  # Contador de nodos expandidos
        self.start_time = 0     # Tiempo de inicio de la búsqueda
        self.time_limit = time_limit   # Límite de tiempo en segundos para tomar una decisión

    def is_time_exceeded(self):
        """Verifica si se ha excedido el límite de tiempo"""
        return (
            self.time_limit is not None
            and (time.time() - self.start_time) > self.time_limit
        )

    def getAction(self, gameState):
        """
        Returns the best action found using iterative deepening search with alpha-beta pruning
        """
        import time

        num_tanks = gameState.getNumAgents()

        # Use the attribute 'index' if present, otherwise assume 0
        root_index = getattr(self, 'index', 0)

        self.start_time = time.time()

        def alpha_beta(state, depth, agent_index, alpha=float('-inf'), beta=float('inf')):
            self.expanded_nodes += 1

            # Terminal or max depth reached
            if depth >= self.depth or state.is_terminal() or self.is_time_exceeded():
                return state.evaluate_state()

            next_agent = (agent_index + 1) % num_tanks
            # Increase depth when we've completed a full cycle back to root
            next_depth = depth + 1 if next_agent == root_index else depth

            # If this agent is the maximizer (the one that called getAction)
            if agent_index == root_index:
                v = float('-inf')
                for action in state.getLegalActions(agent_index):
                    if self.is_time_exceeded():
                        break
                    succ = state.getSuccessor(agent_index, action)
                    v = max(v, alpha_beta(succ, next_depth, next_agent, alpha, beta))
                    alpha = max(alpha,v)
                    if beta < alpha:
                        break
                return v
            else:
                # Minimizing adversary
                v = float('inf')
                for action in state.getLegalActions(agent_index):
                    if self.is_time_exceeded():
                        break
                    succ = state.getSuccessor(agent_index, action)
                    v = min(v, alpha_beta(succ, next_depth, next_agent, alpha, beta))
                    beta = min(beta, v)
                    if beta <= alpha:
                        break  # Alpha-beta pruning
                return v

        legal_actions = gameState.getLegalActions(root_index)
        if not legal_actions:
            return 'STOP'

        best_action = legal_actions[0]
        best_score = float('-inf')

        # Evaluate each root action
        alpha = float('-inf')
        beta = float('inf')
        step = num_tanks if num_tanks > 0 else 1
        for current_max in range(step, (self.depth * step) + 1, step):
            if self.is_time_exceeded() or current_max > self.depth:
                break
            for action in legal_actions:
                succ = gameState.getSuccessor(root_index, action)
                score = alpha_beta(succ, 0, (root_index + 1) % num_tanks, alpha, beta)
                if score > best_score:
                    best_score = score
                    best_action = action
                alpha = max(alpha, best_score)

        return best_action


class ParallelAlphaBetaAgent(AlphaBetaAgent):
    """
    Alpha-beta agent that evaluates the successor states of the root action in parallel.

    Notes:
    - Keeps the same alpha-beta logic for per-subtree search.
    - Parallelizes only the root-action evaluations (each subtree executed in its own thread).
    - Uses a threading.Lock to update shared counters like `expanded_nodes` safely.
    - Respects the same time limit checks as `AlphaBetaAgent`.
    """
    def __init__(self, depth='1', tankIndex=0, time_limit=1.0, max_workers=None):
        super().__init__(depth=depth, tankIndex=tankIndex, time_limit=time_limit)
        # Optional cap for worker threads. If None, we'll use min(len(actions), cpu_count*5)
        self.max_workers = max_workers

    def getAction(self, gameState):
        """
        Same iterative-deepening + alpha-beta structure as `AlphaBetaAgent.getAction`,
        but evaluates each root action's subtree in parallel using threads.
        """
        import time

        num_tanks = gameState.getNumAgents()
        root_index = getattr(self, 'index', 0)
        self.start_time = time.time()

        # Lock for thread-safe updates
        counter_lock = threading.Lock()

        def alpha_beta(state, depth, agent_index, alpha=float('-inf'), beta=float('inf')):
            # Local reference to speed access
            nonlocal counter_lock

            with counter_lock:
                self.expanded_nodes += 1

            # Terminal or max depth reached
            if depth >= self.depth or state.is_terminal() or self.is_time_exceeded():
                return state.evaluate_state()

            next_agent = (agent_index + 1) % num_tanks
            next_depth = depth + 1 if next_agent == root_index else depth

            if agent_index == root_index:
                v = float('-inf')
                for action in state.getLegalActions(agent_index):
                    if self.is_time_exceeded():
                        break
                    succ = state.getSuccessor(agent_index, action)
                    v = max(v, alpha_beta(succ, next_depth, next_agent, alpha, beta))
                    alpha = max(alpha, v)
                    if beta < alpha:
                        break
                return v
            else:
                v = float('inf')
                for action in state.getLegalActions(agent_index):
                    if self.is_time_exceeded():
                        break
                    succ = state.getSuccessor(agent_index, action)
                    v = min(v, alpha_beta(succ, next_depth, next_agent, alpha, beta))
                    beta = min(beta, v)
                    if beta <= alpha:
                        break
                return v

        legal_actions = gameState.getLegalActions(root_index)
        if not legal_actions:
            return 'STOP'

        best_action = legal_actions[0]
        best_score = float('-inf')

        # Iterative deepening across full turns (same step calculation as AlphaBetaAgent)
        alpha = float('-inf')
        beta = float('inf')
        step = num_tanks if num_tanks > 0 else 1

        # Decide number of workers (avoid relying on private attributes)
        cpu = os.cpu_count() or 1
        suggested_workers = min(len(legal_actions), cpu * 5)
        if self.max_workers is not None:
            workers = min(self.max_workers, suggested_workers)
        else:
            workers = max(1, suggested_workers)

        for current_max in range(step, (self.depth * step) + 1, step):
            if self.is_time_exceeded() or current_max > self.depth:
                break

            # For this depth iteration, evaluate each root action in parallel
            futures = []
            with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
                for action in legal_actions:
                    succ = gameState.getSuccessor(root_index, action)
                    # next agent after root
                    next_agent = (root_index + 1) % num_tanks
                    # Submit alpha_beta subtree evaluation
                    futures.append((action, executor.submit(alpha_beta, succ, 0, next_agent, alpha, beta)))

                # Collect results, respecting the time limit
                for action, fut in futures:
                    # If time exceeded, try to cancel remaining futures
                    if self.is_time_exceeded():
                        # best-effort: cancel those that haven't started
                        for _act, f in futures:
                            try:
                                f.cancel()
                            except Exception:
                                pass
                        break

                    try:
                        # calculate remaining time and use as timeout to avoid blocking past time limit
                        remaining = max(0.0, self.time_limit - (time.time() - self.start_time)) if self.time_limit is not None else None
                        score = fut.result(timeout=remaining)
                    except Exception:
                        # If any future fails or times out, skip it
                        continue

                    if score > best_score:
                        best_score = score
                        best_action = action
                    alpha = max(alpha, best_score)

        return best_action