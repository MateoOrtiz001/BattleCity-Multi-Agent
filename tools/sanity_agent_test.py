import sys
sys.path.insert(0, r'C:/Users/mateo/Repositorios/BattleCity-MultiAgent/BattleCity-Multi-Agent')
from src.agents.expectimax import ExpectimaxAgent
from src.gameClass.game import BattleCityState
from src.gameClass.scenarios.level1 import get_level1
from src.agents.minimax import MinimaxAgent
from simulate_expectimax_level1 import GameAdapter

s = BattleCityState()
s.initialize(get_level1())
adapter = GameAdapter(s)
agent = ExpectimaxAgent(depth=3, time_limit=None)
act = agent.getAction(adapter)
print('Chosen action:', act)
