import os
import sys
import time
from typing import Optional, Any

import pygame

# Ensure repo root is on sys.path so this file can be run directly
# repo root is two levels up from src/GUI
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.gameClass.game import BattleCityState
from src.gameClass.scenarios.level1 import get_level1
from src.gameClass.scenarios.level2 import get_level2
from src.gameClass.scenarios.level3 import get_level3
from src.gameClass.scenarios.level4 import get_level4

from src.agents.enemyAgent import ScriptedEnemyAgent
from src.agents.minimax import MinimaxAgent, AlphaBetaAgent, ParallelAlphaBetaAgent
from src.agents.expectimax import ExpectimaxAgent, ParallelExpectimaxAgent


# Default visual config (compatible with the existing visual_test.py)
TILE_SIZE = 40
FPS = 10
COLORS = {
    'background': (30, 30, 30),
    'wall_brick': (139, 69, 19),
    'wall_steel': (100, 100, 100),
    'tank_A': (0, 200, 0),
    'tank_B': (200, 0, 0),
    'base': (255, 215, 0),
    'bullet': (255, 255, 255),
    'button': (50, 50, 50),
    'button_high': (80, 80, 80),
    'text': (255, 255, 255),
}


def draw_game(screen, game_state, action=None):
    """Draw a BattleCityState to the given pygame screen."""
    screen.fill(COLORS['background'])
    size = game_state.getBoardSize()

    # Dibujar muros
    for wall in game_state.getWalls():
        if wall.isDestroyed():
            continue
        color = COLORS['wall_brick'] if wall.getType() == 'brick' else COLORS['wall_steel']
        x, y = wall.getPosition()
        pygame.draw.rect(screen, color, (x*TILE_SIZE, (size-1-y)*TILE_SIZE, TILE_SIZE, TILE_SIZE))

    # Dibujar base
    if not game_state.getBase().isDestroyed():
        x, y = game_state.getBase().getPosition()
        pygame.draw.rect(screen, COLORS['base'], (x*TILE_SIZE, (size-1-y)*TILE_SIZE, TILE_SIZE, TILE_SIZE))

    # Dibujar tanque A
    tankA = game_state.getTeamATank()
    if tankA and tankA.isAlive():
        x, y = tankA.getPos()
        pygame.draw.rect(screen, COLORS['tank_A'], (x*TILE_SIZE, (size-1-y)*TILE_SIZE, TILE_SIZE, TILE_SIZE))

    # Dibujar tanques B
    for t in game_state.getTeamBTanks():
        if t.isAlive():
            x, y = t.getPos()
            pygame.draw.rect(screen, COLORS['tank_B'], (x*TILE_SIZE, (size-1-y)*TILE_SIZE, TILE_SIZE, TILE_SIZE))

    # Dibujar balas
    for b in game_state.getBullets():
        if b.isActive():
            x, y = b.getPosition()
            pygame.draw.circle(screen, COLORS['bullet'], (x*TILE_SIZE + TILE_SIZE//2, (size-1-y)*TILE_SIZE + TILE_SIZE//2), 5)

    # Overlay con acción y puntaje
    try:
        font = pygame.font.SysFont(None, 24)
    except Exception:
        pygame.font.init()
        font = pygame.font.SysFont(None, 24)

    action_text = f"Action: {action}" if action is not None else "Action: None"
    score_val = getattr(game_state, 'score', None)
    score_text = f"Score: {score_val}" if score_val is not None else "Score: N/A"

    surf_action = font.render(action_text, True, (255, 255, 255))
    surf_score = font.render(score_text, True, (255, 215, 0))
    screen.blit(surf_action, (5, 5))
    screen.blit(surf_score, (5, 30))

    pygame.display.flip()


class GameLauncher:
    """Class to launch a single BattleCity run.

    Parameters
    - level: one of 'level1','level2','level3','level4' or a layout function
    - algorithm: None (human) or a string naming the agent or an agent instance
    - agent_params: optional dict passed to agent constructor when algorithm is a string

    If algorithm is None the player controls the tank with arrow keys and 'f' to fire.
    """

    LEVEL_MAP = {
        'level1': get_level1,
        'level2': get_level2,
        'level3': get_level3,
        'level4': get_level4,
    }

    def __init__(self, level: Any = 'level1', algorithm: Optional[Any] = None, agent_params: Optional[dict] = None, tile_size: int = TILE_SIZE, fps: int = FPS):
        self.level = level
        self.algorithm = algorithm
        self.agent_params = agent_params or {}
        self.tile_size = tile_size
        self.fps = fps

    def _resolve_level(self):
        if callable(self.level):
            return self.level()
        if isinstance(self.level, str):
            fn = self.LEVEL_MAP.get(self.level.lower())
            if fn:
                return fn()
        # fallback to level1
        return get_level1()

    def _make_agent(self):
        a = self.algorithm
        if a is None:
            return None
        # If user passed an instance
        if hasattr(a, 'getAction'):
            return a

        # Accept common string names
        name = str(a).lower()
        # Default parameters required by the user request
        # Depth 3 and time_limit 7s where applicable
        if name in ('minimax', 'minmax'):
            params = {'depth': 3, 'tankIndex': 0}
            params.update(self.agent_params)
            return MinimaxAgent(**params)
        if name in ('alphabeta', 'alpha-beta', 'ab'):
            params = {'depth': 3, 'tankIndex': 0, 'time_limit': 7}
            params.update(self.agent_params)
            return ParallelAlphaBetaAgent(**params)
        if name in ('expectimax', 'expect'):
            params = {'depth': 3, 'time_limit': 7}
            params.update(self.agent_params)
            return ParallelExpectimaxAgent(**params)
            

        # Unknown string -> try to import dynamic? For now return None
        return None

    def run(self):
        pygame.init()

        layout = self._resolve_level()

        game_state = BattleCityState()
        game_state.initialize(layout)

        agentA = self._make_agent()
        # Default fallback: AlphaBeta like visual_test if algorithm was a string but unknown
        if self.algorithm and agentA is None:
            try:
                agentA = ParallelAlphaBetaAgent(depth=3, tankIndex=0, time_limit=7)
            except Exception:
                agentA = None

        enemies = [ScriptedEnemyAgent(i+1, script_type='attack_base') for i in range(len(game_state.getTeamBTanks()))]

        size_px = game_state.getBoardSize() * self.tile_size
        screen = pygame.display.set_mode((size_px, size_px))
        pygame.display.set_caption("Battle City - Launcher")

        clock = pygame.time.Clock()

        # Initial frame
        draw_game(screen, game_state, action=None)
        pygame.display.flip()
        pygame.time.delay(150)

        running = True
        while running:
            clock.tick(self.fps)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            if game_state.isWin() or game_state.isLose():
                print("Game over", "Win" if game_state.isWin() else "Lose")
                time.sleep(2)
                running = False
                continue

            # Player turn
            actionA = None
            if agentA is None:
                # Human control: read keys
                keys = pygame.key.get_pressed()
                tank = game_state.getTeamATank()
                if tank is None or not tank.isAlive():
                    actionA = 'STOP'
                else:
                    # Movement
                    if keys[pygame.K_UP]:
                        actionA = 'MOVE_UP'
                    elif keys[pygame.K_DOWN]:
                        actionA = 'MOVE_DOWN'
                    elif keys[pygame.K_LEFT]:
                        actionA = 'MOVE_LEFT'
                    elif keys[pygame.K_RIGHT]:
                        actionA = 'MOVE_RIGHT'
                    elif keys[pygame.K_SPACE] or keys[pygame.K_f]:
                        # Fire in current tank direction if available
                        try:
                            dir = tank.direction
                        except Exception:
                            dir = 'UP'
                        if not dir:
                            dir = 'UP'
                        actionA = f'FIRE_{dir}'
                    else:
                        actionA = 'STOP'
            else:
                # Agent decides
                try:
                    actionA = agentA.getAction(game_state)
                except Exception as e:
                    # If agent fails, fallback to STOP
                    print(f"Agent getAction failed: {e}")
                    actionA = 'STOP'

            # Apply action
            if actionA:
                try:
                    game_state.applyTankAction(0, actionA)
                except Exception as e:
                    # sometimes illegal actions happen if agent/human pressed quickly; ignore
                    #print(f"applyTankAction error: {e}")
                    pass

            # Enemies
            for i, enemy_agent in enumerate(enemies, start=1):
                try:
                    actionB = enemy_agent.getAction(game_state)
                except Exception:
                    actionB = 'STOP'
                if actionB:
                    try:
                        game_state.applyTankAction(i, actionB)
                    except Exception:
                        pass

            # Physics / bullets / collisions / respawns
            game_state.moveBullets()
            game_state._check_collisions()
            game_state._handle_deaths_and_respawns()

            # advance time tick
            try:
                game_state.current_time += 1
            except Exception:
                pass

            # update score
            try:
                game_state.score = game_state.evaluate_state()
            except Exception:
                pass

            draw_game(screen, game_state, action=actionA)

        # Close only the display so we return cleanly to the caller (the menu)
        try:
            pygame.display.quit()
        except Exception:
            try:
                pygame.quit()
            except Exception:
                pass
        return


class GameMenu:
    """Simple Pygame menu to pick level and algorithm and start GameLauncher."""

    ALGORITHMS = [
        ('Human', None),
        ('Minimax', 'minimax'),
        ('Alpha Beta', 'parallel_alphabeta'),
        ('Expectimax', 'parallel_expectimax'),
    ]

    LEVELS = ['level1', 'level2', 'level3', 'level4']

    def __init__(self, width=640, height=480):
        pygame.init()
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption('BattleCity - Menu')
        try:
            self.font = pygame.font.SysFont(None, 28)
        except Exception:
            pygame.font.init()
            self.font = pygame.font.SysFont(None, 28)

        self.selected_algo = None
        self.selected_level = 'level1'

    def _draw_button(self, rect, text, highlight=False):
        color = COLORS['button_high'] if highlight else COLORS['button']
        pygame.draw.rect(self.screen, color, rect)
        surf = self.font.render(text, True, COLORS['text'])
        tw, th = surf.get_size()
        self.screen.blit(surf, (rect[0] + (rect[2]-tw)//2, rect[1] + (rect[3]-th)//2))

    def run(self):
        clock = pygame.time.Clock()
        running = True

        algo_buttons = []
        lvl_buttons = []

        # Layout buttons
        left = 40
        top = 40
        bw = 220
        bh = 40
        gap = 10

        for i, (label, val) in enumerate(self.ALGORITHMS):
            rect = (left, top + i*(bh+gap), bw, bh)
            algo_buttons.append((rect, label, val))

        # level buttons on the right
        lleft = left + bw + 60
        for i, lvl in enumerate(self.LEVELS):
            rect = (lleft, top + i*(bh+gap), bw, bh)
            lvl_buttons.append((rect, lvl))

        info_rect = (40, top + len(algo_buttons)*(bh+gap) + 20, bw*2 + 60, 80)

        while running:
            clock.tick(30)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mx, my = event.pos
                    for rect, label, val in algo_buttons:
                        x,y,w,h = rect
                        if x <= mx <= x+w and y <= my <= y+h:
                            self.selected_algo = val
                    for rect, lvl in lvl_buttons:
                        x,y,w,h = rect
                        if x <= mx <= x+w and y <= my <= y+h:
                            self.selected_level = lvl
                    # Start button click
                    sx, sy, sw, sh = (self.width//2 - 80, info_rect[1] + info_rect[3] + 10, 160, 40)
                    if sx <= mx <= sx+sw and sy <= my <= sy+sh:
                        # launch the game (blocks until finished) and then recreate the menu display
                        launcher = GameLauncher(level=self.selected_level, algorithm=self.selected_algo)
                        launcher.run()
                        # Recreate menu display after the game window closed
                        try:
                            pygame.display.init()
                            self.screen = pygame.display.set_mode((self.width, self.height))
                            pygame.display.set_caption('BattleCity - Menu')
                        except Exception:
                            # If recreation fails, attempt a full pygame init
                            try:
                                pygame.init()
                                self.screen = pygame.display.set_mode((self.width, self.height))
                                pygame.display.set_caption('BattleCity - Menu')
                            except Exception:
                                pass

            # draw
            self.screen.fill(COLORS['background'])
            title = self.font.render('BattleCity - Menu', True, COLORS['text'])
            self.screen.blit(title, (self.width//2 - title.get_width()//2, 10))

            for rect, label, val in algo_buttons:
                highlight = (self.selected_algo == val)
                self._draw_button(rect, label, highlight=highlight)

            for rect, lvl in lvl_buttons:
                highlight = (self.selected_level == lvl)
                self._draw_button(rect, lvl, highlight=highlight)

            # Info area
            pygame.draw.rect(self.screen, COLORS['button'], info_rect)
            info_lines = [f'Selected algo: {self.selected_algo or "Human"}', f'Selected level: {self.selected_level}']
            for i, line in enumerate(info_lines):
                surf = self.font.render(line, True, COLORS['text'])
                self.screen.blit(surf, (info_rect[0]+8, info_rect[1]+8 + i*28))

            # Start button
            sx, sy, sw, sh = (self.width//2 - 80, info_rect[1] + info_rect[3] + 10, 160, 40)
            self._draw_button((sx, sy, sw, sh), 'Start', highlight=False)

            pygame.display.flip()

        pygame.quit()


if __name__ == '__main__':
    # Run menu when executed directly
    menu = GameMenu(800, 480)
    menu.run()
