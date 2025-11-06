# src/agents/mcts.py
import time
import math
import random
import copy

from ..gameClass.enemy_scripts import ScriptedEnemyAgent

class MCTSNode:
    def __init__(self, state, parent=None, action_from_parent=None):
        self.state = state              # objeto BattleCityState (copia)
        self.parent = parent
        self.action_from_parent = action_from_parent
        self.children = {}              # action -> MCTSNode
        self.untried_actions = None     # lista de acciones (solo del jugador en este diseño)
        self.visits = 0
        self.value = 0.0                # suma de recompensas (desde perspectiva del jugador)

    def expand(self, action, child_state):
        child = MCTSNode(child_state, parent=self, action_from_parent=action)
        self.children[action] = child
        return child

    def is_fully_expanded(self):
        return self.untried_actions is not None and len(self.untried_actions) == 0

    def best_child(self, c_param=1.4):
        # UCT over children (maximize for player)
        best = None
        best_score = -float("inf")
        total_N = sum(child.visits for child in self.children.values())
        for action, child in self.children.items():
            if child.visits == 0:
                score = float("inf")
            else:
                exploit = child.value / child.visits
                explore = c_param * math.sqrt(math.log(max(1, total_N)) / child.visits)
                score = exploit + explore
            if score > best_score:
                best_score = score
                best = child
        return best

class MCTSAgent:
    """
    MCTS agent that only branches at the player's decision points.
    Simula las respuestas enemigas usando ScriptedEnemyAgent.
    """
    def __init__(self, num_simulations=500, rollout_depth=20, c=1.4, seed=None, scripted_enemy_type='attack_base'):
        self.num_simulations = num_simulations
        self.rollout_depth = rollout_depth
        self.c = c
        self.rng = random.Random(seed)
        self.node_count = 0
        self.scripted_enemy_type = scripted_enemy_type

    # ---------------- helper: simulate enemy turns until next player turn ----------------
    def _simulate_enemies_until_player(self, state, scripted_enemies):
        """
        Dado un state cuyo turno es el de un enemigo (o que se encuentra después de aplicar la acción
        del jugador), simulamos las acciones de todos los enemigos (1..num_agents-1) usando
        scripted_enemies (lista de ScriptedEnemyAgent con índices adecuados), aplicando
        getSuccessor para cada uno. Devuelve el nuevo estado al llegar de nuevo al turno del jugador.
        """
        num_agents = state.getNumAgents()
        # Suponemos que los índices de enemigos son 1..num_agents-1
        # Para cada enemy_index aplicamos una acción (si está vivo)
        s = state
        for enemy_index in range(1, num_agents):
            legal = s.getLegalActions(enemy_index)
            if not legal:
                continue
            # Usar el ScriptedEnemyAgent para decidir (si no existe, usar random)
            try:
                enemy_agent = scripted_enemies[enemy_index - 1]
                act = enemy_agent.getAction(s)
            except Exception:
                act = self.rng.choice(legal)
            # Si la acción no es legal por alguna razón, seleccionar aleatoria segura
            if act not in legal:
                act = self.rng.choice(legal)
            # Avanzar usando getSuccessor para respetar la lógica de tu juego
            s = s.getSuccessor(enemy_index, act)
        return s

    # ---------------- rollout policy ----------------
    def _rollout(self, state, scripted_enemies):
        """
        Ejecuta un rollout hasta depth o estado terminal.
        En cada ciclo se selecciona una acción para el jugador (aleatoria con preferencia a FIRE)
        y se simulan las respuestas enemigas con scripted_enemies.
        """
        s = state
        for _ in range(self.rollout_depth):
            if s.isWin() or s.isLose() or s.isLimitTime():
                break
            # Jugador
            legal_p = s.getLegalActions(0)
            if not legal_p:
                break
            # Prefer FIRE if available, else random (ligera preferencia)
            if 'FIRE' in legal_p and self.rng.random() < 0.6:
                act_p = 'FIRE'
            else:
                act_p = self.rng.choice(legal_p)
            s = s.getSuccessor(0, act_p)
            # Simular enemigos hasta volver al jugador
            s = self._simulate_enemies_until_player(s, scripted_enemies)
        # Usamos evaluate_state como recompensa
        return s.evaluate_state()

    # ---------------- main function ----------------
    def getAction(self, gameState):
        """
        Ejecuta MCTS y devuelve la acción (string) con mejor promedio de valor.
        """
        t_start = time.time()
        self.node_count = 0

        # Instanciar scripted enemies para rollouts/respuestas rápidas
        num_agents = gameState.getNumAgents()
        scripted_enemies = []
        for i in range(1, num_agents):
            scripted_enemies.append(ScriptedEnemyAgent(i, script_type=self.scripted_enemy_type))

        # Root nodo: clonamos el estado para el árbol (usar copia rápida si está disponible)
        try:
            root_state = gameState.fast_copy()
        except Exception:
            root_state = copy.deepcopy(gameState)
        root = MCTSNode(root_state, parent=None)
        root.untried_actions = list(root_state.getLegalActions(0))  # acciones del jugador en la raíz

        # Si no hay acciones legales, devolver None
        if not root.untried_actions:
            return None

        for sim in range(self.num_simulations):
            node = root
            # arrancamos la simulación desde la raíz estado (usar fast_copy si disponible)
            try:
                state = root_state.fast_copy()
            except Exception:
                state = copy.deepcopy(root_state)
            # -------- Selection & Expansion (only at player nodes) --------
            # Descendemos por el árbol mientras los nodos estén completamente expandidos
            while True:
                # Si llegamos a un node que no tiene acciones inicializadas, inicializarlas
                if node.untried_actions is None:
                    node.untried_actions = list(state.getLegalActions(0))
                # Si hay acciones sin probar -> expandir
                if node.untried_actions:
                    # Expand: tomar una acción no probada del jugador
                    action = self.rng.choice(node.untried_actions)
                    node.untried_actions.remove(action)
                    # Aplicar acción del jugador y luego simular respuestas enemigas
                    next_state = state.getSuccessor(0, action)
                    next_state = self._simulate_enemies_until_player(next_state, scripted_enemies)
                    # crear hijo y romper selection loop
                    # next_state ya es una copia devuelta por getSuccessor / simulación de enemigos,
                    # evitar una copia redundante aquí para reducir el coste de deepcopying.
                    child = node.expand(action, next_state)
                    node = child
                    state = next_state
                    self.node_count += 1
                    break
                else:
                    # Si node completamente expandido -> seleccionar mejor child por UCT
                    if not node.children:
                        # No tiene hijos (puede ocurrir si no hay acciones)
                        break
                    child = node.best_child(self.c)
                    # Si best_child devolviera None (caso límite), salimos del bucle de selección
                    if child is None:
                        break
                    node = child
                    # Avanzar el estado aplicando la acción asociada
                    state = state.getSuccessor(0, node.action_from_parent)
                    state = self._simulate_enemies_until_player(state, scripted_enemies)

            # -------- Simulation / Rollout --------
            reward = self._rollout(state, scripted_enemies)

            # -------- Backpropagation --------
            # Actualizamos visitas/valores en la rama (desde node hacia la raíz)
            cur = node
            while cur is not None:
                cur.visits += 1
                # Nota: usamos la recompensa tal cual (desde perspectiva del jugador)
                cur.value += reward
                cur = cur.parent

        # -------- Selección final: acción con mayor promedio --------
        best_action = None
        best_mean = -float("inf")
        for act, child in root.children.items():
            if child.visits > 0:
                mean = child.value / child.visits
            else:
                mean = -float("inf")
            # preferir mayor mean, en empate escoger con más visitas
            if mean > best_mean or (mean == best_mean and child.visits > (root.children.get(best_action).visits if best_action in root.children else -1)):
                best_mean = mean
                best_action = act

        # Si no hay hijos (posible cuando num_simulations=0), elegir acción legal aleatoria
        if best_action is None:
            legal = gameState.getLegalActions(0)
            if not legal:
                return None
            best_action = self.rng.choice(legal)

        # imprimir estadísticas útiles
        elapsed = time.time() - t_start
        print(f"[MCTS] sims={self.num_simulations} time={elapsed:.3f}s node_count={self.node_count} best_action={best_action} best_mean={best_mean:.3f}")

        return best_action
