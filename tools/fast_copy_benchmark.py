import time, copy, sys
sys.path.insert(0, r'C:/Users/mateo/Repositorios/BattleCity-MultiAgent/BattleCity-Multi-Agent')
from src.gameClass.game import BattleCityState
from src.gameClass.scenarios.level1 import get_level1

s=BattleCityState()
layout = get_level1()
s.initialize(layout)
# measure fast_copy
n=200
t0=time.time()
for i in range(n):
    c = s.fast_copy()
end=time.time()
print('fast_copy avg ms:', (end-t0)/n*1000)
# measure deepcopy
m=20
t0=time.time()
for i in range(m):
    d = copy.deepcopy(s)
end=time.time()
print('deepcopy avg ms:', (end-t0)/m*1000)
