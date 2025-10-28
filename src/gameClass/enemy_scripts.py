import random
from ..utils import manhattanDistance

class ScriptedEnemyAgent:
    """
    Un agente simple que sigue un script determinista 
    (o con un poco de aleatoriedad) para moverse en el juego 'real'.
    """
    def __init__(self, agent_index, script_type='attack_base'):
        self.agent_index = agent_index
        self.script_type = script_type

    def getAction(self, game_state):
        """
        Devuelve UNA sola acción (string), no probabilidades.
        Este es el 'cerebro' real del bot.
        """
        
        legal_actions = game_state.getLegalActions(self.agent_index)
        
        # Si está muerto o atascado, devuelve STOP
        if 'STOP' in legal_actions and len(legal_actions) == 1:
            return 'STOP'

        # Elige qué comportamiento seguir
        if self.script_type == 'attack_base':
            return self.run_attack_base_script(game_state, legal_actions)
        else:
            return self.run_random_script(legal_actions)

    def run_attack_base_script(self, game_state, legal_actions):
        """Un script simple que intenta moverse hacia la base."""
        
        # Información del estado
        tank = game_state.teamB_tanks[self.agent_index - 1]
        base_pos = game_state.base.position
        tank_pos = tank.position
        current_dist = manhattanDistance(tank_pos, base_pos)

        best_move = 'STOP'
        min_dist = current_dist

        # 1. Buscar la mejor acción de MOVIMIENTO
        move_actions = []
        for action in legal_actions:
            if action.startswith('MOVE_'):
                x, y = tank_pos
                if action == 'MOVE_UP': next_pos = (x, y + 1)
                elif action == 'MOVE_DOWN': next_pos = (x, y - 1)
                elif action == 'MOVE_LEFT': next_pos = (x - 1, y)
                elif action == 'MOVE_RIGHT': next_pos = (x + 1, y)
                else: continue
                
                new_dist = manhattanDistance(next_pos, base_pos)
                
                if new_dist < min_dist:
                    min_dist = new_dist
                    best_move = action
                
                move_actions.append(action)

        # 2. Decidir si disparar (con un poco de aleatoriedad)
        # Por ejemplo, 20% de probabilidad de disparar si es legal
        if 'FIRE' in legal_actions and random.random() < 0.2:
            return 'FIRE'
        
        # 3. Si el mejor movimiento es STOP (atascado), elige uno al azar
        if best_move == 'STOP' and move_actions:
            return random.choice(move_actions)

        return best_move

    def run_random_script(self, legal_actions):
        """Un bot tonto que se mueve al azar."""
        return random.choice(legal_actions)