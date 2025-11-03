import pygame
import time
import sys

from src.gameClass.game import BattleCityState
from src.gameClass.scenarios.level1 import get_level1
from src.gameClass.enemy_scripts import ScriptedEnemyAgent
from src.agents.expectimax import ExpectimaxAgent

# Import GameAdapter from the non-visual simulation helper so agents get the expected API
from simulate_expectimax_level1 import GameAdapter


CELL_SIZE = 32


def draw_game(screen, state, grid_size):
    COLORS = {
        'background': (0, 0, 0),
        'brick': (200, 80, 50),
        'steel': (180, 180, 180),
        'tankA': (186, 177, 154),
        'tankB': (145, 145, 145),
        'base': (255, 255, 0),
        'bullet': (255, 255, 255),
        'text': (255, 255, 255),
    }

    screen.fill(COLORS['background'])

    # Walls
    for wall in getattr(state, 'walls', []):
        if not wall.isDestroyed():
            color = COLORS['brick'] if wall.getType() == 'brick' else COLORS['steel']
            x, y = wall.getPosition()
            pygame.draw.rect(screen, color, (x*CELL_SIZE, (grid_size-1-y)*CELL_SIZE, CELL_SIZE, CELL_SIZE))

    # Base
    base = getattr(state, 'base', None)
    if base and not base.isDestroyed():
        x, y = base.getPosition()
        pygame.draw.rect(screen, COLORS['base'], (x*CELL_SIZE, (grid_size-1-y)*CELL_SIZE, CELL_SIZE, CELL_SIZE))

    # Tanks
    tanks = []
    if getattr(state, 'teamA_tank', None):
        tanks.append(state.teamA_tank)
    tanks.extend(getattr(state, 'teamB_tanks', []))

    for t in tanks:
        if getattr(t, 'is_alive', True):
            x, y = t.getPos()
            color = COLORS['tankA'] if t.getTeam() == 'A' else COLORS['tankB']
            pygame.draw.rect(screen, color, (x*CELL_SIZE, (grid_size-1-y)*CELL_SIZE, CELL_SIZE, CELL_SIZE))

    # Bullets (draw only active bullets; defensive: skip bullets sitting on non-destroyed walls)
    bullets = getattr(state, 'bullets', []) or []
    # build set of non-destroyed wall positions for quick lookup
    wall_positions = set()
    for w in getattr(state, 'walls', []):
        try:
            if not w.isDestroyed():
                wall_positions.add(w.getPosition())
        except Exception:
            if not getattr(w, 'is_destroyed', False):
                wall_positions.add(getattr(w, 'position', None))

    def _bullet_active(b):
        try:
            return b.isActive()
        except Exception:
            return getattr(b, 'is_active', True)

    def _bullet_pos(b):
        try:
            return b.getPosition()
        except Exception:
            return getattr(b, 'position', None)

    for b in bullets:
        if not _bullet_active(b):
            continue
        pos = _bullet_pos(b)
        if pos is None:
            continue
        # if the bullet sits exactly on a non-destroyed wall position, skip drawing (collision should remove it)
        if pos in wall_positions:
            continue
        x, y = pos
        pygame.draw.circle(screen, COLORS['bullet'], (int(x*CELL_SIZE + CELL_SIZE/2), int((grid_size-1-y)*CELL_SIZE + CELL_SIZE/2)), 4)

    # HUD
    font = pygame.font.Font(None, 24)
    time_text = f"Time: {getattr(state, 'current_time', 0)}"
    screen.blit(font.render(time_text, True, COLORS['text']), (8, 8))

    pygame.display.flip()


def run_visual(time_limit_agent=0.75, depth=16, fps=5):
    pygame.init()
    layout = get_level1()
    state = BattleCityState()
    state.initialize(layout)

    grid = state.getBoardSize()
    screen = pygame.display.set_mode((grid*CELL_SIZE, grid*CELL_SIZE))
    pygame.display.set_caption('BattleCity - Expectimax Level1')
    clock = pygame.time.Clock()

    # Agents
    expectimax = ExpectimaxAgent(depth=depth, time_limit=time_limit_agent)
    try:
        expectimax.index = 0
    except Exception:
        pass

    num_agents = state.getNumAgents()
    scripted_agents = {i: ScriptedEnemyAgent(i, script_type='attack_base') for i in range(1, num_agents)}

    running = True
    paused = False
    turn = 0

    while running:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False
            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    running = False
                elif ev.key == pygame.K_SPACE:
                    paused = not paused

        if not running:
            break

        if paused:
            clock.tick(10)
            continue

        # Check terminal
        if state.isWin() or state.isLose() or state.isLimitTime():
            draw_game(screen, state, grid)
            pygame.display.flip()
            time.sleep(2)
            break

        # Per-agent decisions
        for agent_index in range(state.getNumAgents()):
            adapter = GameAdapter(state)
            if agent_index == 0:
                action = expectimax.getAction(adapter)
            else:
                action = scripted_agents.get(agent_index).getAction(adapter)

            # apply
            try:
                state.applyTankAction(agent_index, action)
            except Exception:
                pass

            # After last agent, advance bullets and handle deaths
            if agent_index == state.getNumAgents() - 1:
                try:
                    state.moveBullets()
                    state._handle_deaths_and_respawns()
                    state._check_collisions()
                except Exception:
                    pass

        # Defensive cleanup: ensure bullets list doesn't contain inactive bullets
        # or bullets sitting on non-destroyed wall positions (visual consistency).
        try:
            wall_positions = set()
            for w in getattr(state, 'walls', []):
                try:
                    if not w.isDestroyed():
                        wall_positions.add(w.getPosition())
                except Exception:
                    if not getattr(w, 'is_destroyed', False):
                        wall_positions.add(getattr(w, 'position', None))

            cleaned = []
            for b in getattr(state, 'bullets', []) or []:
                try:
                    active = b.isActive()
                except Exception:
                    active = getattr(b, 'is_active', True)
                try:
                    pos = b.getPosition()
                except Exception:
                    pos = getattr(b, 'position', None)
                if not active:
                    continue
                if pos in wall_positions:
                    # If bullet is exactly at a non-destroyed wall position, drop it
                    continue
                cleaned.append(b)
            state.bullets = cleaned
        except Exception:
            # tolerate any issue here - visualization should not crash the game
            pass

        # advance time
        state.current_time = getattr(state, 'current_time', 0) + 1
        turn += 1

        # draw
        draw_game(screen, state, grid)
        clock.tick(fps)

    pygame.quit()


if __name__ == '__main__':
    run_visual(time_limit_agent=0.75, depth=16, fps=5)
