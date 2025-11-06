import time
import sys
import os
# Ensure repo root is on sys.path so we can import src.gameClass
repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from src.gameClass.tank import Tank as TankSlots
from src.gameClass.bullet import Bullet as BulletSlots
from src.gameClass.walls import Wall as WallSlots

# Local classes without __slots__ to simulate pre-change behavior
class TankNoSlots:
    def __init__(self, position, team):
        self.position = position
        self.spawn_position = position
        self.direction = None
        self.team = team
        self.is_alive = True
        self.health = 3
        self.respawn_timer = 0.0
    def getPos(self):
        return self.position

class BulletNoSlots:
    def __init__(self, position, direction, team, owner_id=None):
        self.position = position
        self.direction = direction
        self.team = team
        self.owner_id = owner_id
        self.is_active = True
        self.prev_position = None

class WallNoSlots:
    def __init__(self, position, wall_type):
        self.position = position
        self.wall_type = wall_type
        self.is_destroyed = False
        self.health = 5

N = 20000
print(f"Benchmarking creation and attribute access for N={N} instances each")

# Creation: Tanks
start = time.perf_counter()
no_slots_tanks = [TankNoSlots((i%20, i%15), 'A') for i in range(N)]
end = time.perf_counter()
print(f"TankNoSlots creation: {end-start:.4f} s")

start = time.perf_counter()
slots_tanks = [TankSlots((i%20, i%15), 'A') for i in range(N)]
end = time.perf_counter()
print(f"TankSlots creation:   {end-start:.4f} s")

# Access: getPos (method) vs attribute
start = time.perf_counter()
sumx = 0
for t in no_slots_tanks:
    p = t.getPos()
    sumx += p[0]
end = time.perf_counter()
print(f"TankNoSlots getPos(): {end-start:.4f} s (sumx={sumx})")

start = time.perf_counter()
sumx = 0
for t in slots_tanks:
    p = t.getPos()
    sumx += p[0]
end = time.perf_counter()
print(f"TankSlots getPos():   {end-start:.4f} s (sumx={sumx})")

start = time.perf_counter()
sumx = 0
for t in no_slots_tanks:
    p = t.position
    sumx += p[0]
end = time.perf_counter()
print(f"TankNoSlots .position: {end-start:.4f} s (sumx={sumx})")

start = time.perf_counter()
sumx = 0
for t in slots_tanks:
    p = t.position
    sumx += p[0]
end = time.perf_counter()
print(f"TankSlots .position:   {end-start:.4f} s (sumx={sumx})")

# Repeat similar tests for Bullet and Wall
start = time.perf_counter()
no_slots_bullets = [BulletNoSlots((i%20, i%15), 'UP', 'A') for i in range(N)]
end = time.perf_counter()
print(f"BulletNoSlots creation: {end-start:.4f} s")

start = time.perf_counter()
slots_bullets = [BulletSlots((i%20, i%15), 'UP', 'A') for i in range(N)]
end = time.perf_counter()
print(f"BulletSlots creation:   {end-start:.4f} s")

start = time.perf_counter()
no_slots_walls = [WallNoSlots((i%20, i%15), 'brick') for i in range(N)]
end = time.perf_counter()
print(f"WallNoSlots creation:   {end-start:.4f} s")

start = time.perf_counter()
slots_walls = [WallSlots((i%20, i%15), 'brick') for i in range(N)]
end = time.perf_counter()
print(f"WallSlots creation:     {end-start:.4f} s")

# Quick access loop for bullets
start = time.perf_counter()
sumx = 0
for b in no_slots_bullets:
    sumx += b.position[0]
end = time.perf_counter()
print(f"BulletNoSlots .position: {end-start:.4f} s")

start = time.perf_counter()
sumx = 0
for b in slots_bullets:
    sumx += b.position[0]
end = time.perf_counter()
print(f"BulletSlots .position:   {end-start:.4f} s")

print("Benchmark finished")
