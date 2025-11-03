from ..utils import manhattanDistance, lookup
import time


class MinimaxAgent():
    """
    Your minimax agent (question 2)
    """
    def __init__(self, depth = '1', tankIndex = 0):
        self.index = tankIndex  # Índice del tanque que controla este agente
        self.depth = int(depth)  # Debe ser múltiplo de 4 para completar un ciclo de todos los tanques
        self.expanded_nodes = 0  # Contador de nodos expandidos
        # Para permitir un corte por tiempo similar a AlphaBetaAgent
        self.start_time = 0
        self.time_limit = 1.0

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

            # Time cutoff
            if time.time() - self.start_time > self.time_limit:
                return state.evaluate_state(state.getState())

            # Terminal or max depth reached
            if depth >= self.depth or state.is_terminal():
                return state.evaluate_state(state.getState())

            next_agent = (agent_index + 1) % num_tanks
            # Increase depth when we've completed a full cycle back to root
            next_depth = depth + 1 if next_agent == root_index else depth

            # If this agent is the maximizer (the one that called getAction)
            if agent_index == root_index:
                v = float('-inf')
                for action in state.getLegalActions(agent_index):
                    if time.time() - self.start_time > self.time_limit:
                        break
                    succ = state.generateSuccessor(agent_index, action)
                    v = max(v, minimax(succ, next_depth, next_agent))
                return v
            else:
                # Minimizing adversary
                v = float('inf')
                for action in state.getLegalActions(agent_index):
                    if time.time() - self.start_time > self.time_limit:
                        break
                    succ = state.generateSuccessor(agent_index, action)
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
            succ = gameState.generateSuccessor(root_index, action)
            score = minimax(succ, 0, (root_index + 1) % num_tanks)
            if score > best_score:
                best_score = score
                best_action = action

        return best_action

class AlphaBetaAgent():
    """
    Your minimax agent with alpha-beta pruning and iterative deepening for Battle City
    """
    def __init__(self, depth = '1', tankIndex = 0):
        self.index = tankIndex  # Índice del tanque que controla este agente
        self.depth = int(depth)  # Profundidad máxima para IDS
        self.expanded_nodes = 0  # Contador de nodos expandidos
        self.start_time = 0     # Tiempo de inicio de la búsqueda
        self.time_limit = 1.0   # Límite de tiempo en segundos para tomar una decisión

    def is_time_exceeded(self):
        """Verifica si se ha excedido el límite de tiempo"""
        return time.time() - self.start_time > self.time_limit

    def getAction(self, gameState):
        """
        Returns the best action found using iterative deepening search with alpha-beta pruning
        """
        import time
        self.start_time = time.time()
        num_tanks = 1 + len(gameState.teamB_tanks)
        
        # Obtener acciones legales
        legal_actions = gameState.getLegalActions(self.index)
        if not legal_actions:
            return 'STOP'

        # Acción por defecto en caso de que se acabe el tiempo en la primera iteración
        best_overall_action = legal_actions[0]
        
        # Iterative Deepening Search por turnos completos (4 niveles por turno)
        for current_depth in range(4, (self.depth * 4) + 1, 4):
            if self.is_time_exceeded():
                break
            # Mostrar progreso solo si no se ha suprimido la salida desde el invocador
            if not getattr(self, 'suppress_output', False):
                print(f"Búsqueda a profundidad {current_depth} ({current_depth//4} turnos completos)")
                
            current_best_action = None
            current_best_score = float('-inf') if self.index == 1 else float('inf')
            alpha = float('-inf')
            beta = float('inf')
            
            # Obtener siguiente tanque
            next_tank = (self.index + 1) % num_tanks
            
            # Evaluar cada acción con la profundidad actual
            for action in legal_actions:
                if self.is_time_exceeded():
                    break
                    
                successor = gameState.generateSuccessor(self.index, action)
                eval = self.alpha_beta(successor, 0, current_depth, alpha, beta, next_tank)
                
                if self.index == 1:  # Equipo A maximiza
                    if eval > current_best_score:
                        current_best_score = eval
                        current_best_action = action
                    alpha = max(alpha, current_best_score)
                else:  # Equipo B minimiza
                    if eval < current_best_score:
                        current_best_score = eval
                        current_best_action = action
                    beta = min(beta, current_best_score)
                
                if beta < alpha:
                    break
            
            if not self.is_time_exceeded() and current_best_action is not None:
                best_overall_action = current_best_action
        
        return best_overall_action

    def alpha_beta(self, state, current_depth, max_depth, alpha, beta, tank_index):
        """
        Implementación modificada de alpha-beta para IDS
        """
        self.expanded_nodes += 1
        
        if self.is_time_exceeded():
            return 0  # Retornar valor neutral si se acaba el tiempo
            
        if current_depth >= max_depth or state.is_terminal():
            return state.evaluate_state(state.getState())
            
        num_tanks = 1 + len(state.teamB_tanks)
        is_team_a = tank_index == 0
        next_tank = (tank_index + 1) % num_tanks
        next_depth = current_depth + 1 if next_tank == 0 else current_depth
        
        if is_team_a:  # Maximizing player
            v = float('-inf')
            for action in state.getLegalActions(tank_index):
                if self.is_time_exceeded():
                    break
                successor = state.generateSuccessor(tank_index, action)
                v = max(v, self.alpha_beta(successor, next_depth, max_depth, alpha, beta, next_tank))
                alpha = max(alpha, v)
                if beta <= alpha:
                    break
            return v
        else:  # Minimizing player
            v = float('inf')
            for action in state.getLegalActions(tank_index):
                if self.is_time_exceeded():
                    break
                successor = state.generateSuccessor(tank_index, action)
                v = min(v, self.alpha_beta(successor, next_depth, max_depth, alpha, beta, next_tank))
                beta = min(beta, v)
                if beta <= alpha:
                    break
            return v
            v = float('-inf')
            next_tank = (tank_index + 1) % num_tanks
            next_depth = depth + 1 if next_tank == 0 else depth
            
            for action in state.getLegalActions(tank_index):
                successor = state.generateSuccessor(tank_index, action)
                eval = alpha_beta(successor, next_depth, alpha, beta, next_tank)
                v = max(v, eval)
                alpha = max(alpha, v)
                if beta < alpha:
                    break
            return v
            
        def min_value(state, depth, alpha, beta, tank_index):
            v = float('inf')
            next_tank = (tank_index + 1) % num_tanks
            next_depth = depth + 1 if next_tank == 0 else depth
            
            for action in state.getLegalActions(tank_index):
                successor = state.generateSuccessor(tank_index, action)
                eval = alpha_beta(successor, next_depth, alpha, beta, next_tank)
                v = min(v, eval)
                beta = min(beta, v)
                if beta < alpha:
                    break
            return v
        def alpha_beta(state, depth, alpha, beta, tank_index):
            self.expanded_nodes += 1
            if depth >= self.depth or state.is_terminal():
                team = 'A' if self.index < len(state.teamA_tanks) else 'B'
                return state.evaluate_state(state.getState(), team)
                
            # Determinar si es un tanque del equipo A (maximizador) o B (minimizador)
            is_team_a = tank_index < len(state.teamA_tanks)
            
            if is_team_a:
                return max_value(state, depth, alpha, beta, tank_index)
            else:
                return min_value(state, depth, alpha, beta, tank_index)
                
        # Obtener acciones legales
        legal_actions = gameState.getLegalActions(self.index)
        if not legal_actions:
            return 'STOP'  # Si no hay acciones legales, detenerse
            
        # Inicializar búsqueda desde el tanque actual
        best_score = float('-inf') if self.index < len(gameState.teamA_tanks) else float('inf')
        best_action = legal_actions[0]  # Asignar una acción por defecto (primera acción legal)
        alpha = float('-inf')
        beta = float('inf')
        
        # Obtener siguiente tanque
        next_tank = (self.index + 1) % num_tanks
        
        for action in legal_actions:
            successor = gameState.generateSuccessor(self.index, action)
            eval = alpha_beta(successor, 0, alpha, beta, next_tank)
            
            if self.index < len(gameState.teamA_tanks):  # Equipo A maximiza
                if eval > best_score:
                    best_score = eval
                    best_action = action
                alpha = max(alpha, best_score)
            else:  # Equipo B minimiza
                if eval < best_score:
                    best_score = eval
                    best_action = action
                beta = min(beta, best_score)
                
            if beta < alpha:
                break
                
        return best_action