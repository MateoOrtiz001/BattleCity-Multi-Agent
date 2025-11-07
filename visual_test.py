import pygame
import sys
import time
from src.gameClass.game import BattleCityState
from src.agents.minimax import MinimaxAgent, AlphaBetaAgent, ParallelAlphaBetaAgent
from src.agents.expectimax import ExpectimaxAgent, ParallelExpectimaxAgent
from src.agents.enemyAgent import ScriptedEnemyAgent
from src.gameClass.scenarios.level1 import get_level1
from src.gameClass.scenarios.level2 import get_level2
from src.gameClass.scenarios.level3 import get_level3

# Configuración visual
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
}

def draw_game(screen, game_state, action=None):
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
    if tankA.isAlive():
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

    # Mostrar overlay con acción y puntaje
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
    # Dibujarlos en esquina superior izquierda
    screen.blit(surf_action, (5, 5))
    screen.blit(surf_score, (5, 30))

    pygame.display.flip()

def main():
    pygame.init()

    # Layout de prueba
    layout = get_level1()

    game_state = BattleCityState()
    game_state.initialize(layout)

    # Agentes
    #agentA = ParallelExpectimaxAgent(depth=3,time_limit=None, debug=True)
    agentA = ParallelAlphaBetaAgent(depth=3, tankIndex=0, time_limit=7)
    enemies = [ScriptedEnemyAgent(i+1, script_type='attack_base') for i in range(len(game_state.getTeamBTanks()))]

    # Ventana
    size_px = game_state.getBoardSize() * TILE_SIZE
    screen = pygame.display.set_mode((size_px, size_px))
    pygame.display.set_caption("Battle City - Visual Tester")

    clock = pygame.time.Clock()

    # --- Mostrar pantalla de título antes de iniciar el algoritmo ---
    try:
        title_font = pygame.font.SysFont(None, 48)
    except Exception:
        pygame.font.init()
        title_font = pygame.font.SysFont(None, 48)

    title_start = pygame.time.get_ticks()
    TITLE_DURATION_MS = 5000
    while pygame.time.get_ticks() - title_start < TITLE_DURATION_MS:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        screen.fill(COLORS['background'])
        title_surf = title_font.render("BattleCity Agent", True, (255, 255, 255))
        tw, th = title_surf.get_size()
        screen.blit(title_surf, ((size_px - tw) // 2, (size_px - th) // 2))
        pygame.display.flip()
        clock.tick(FPS)

    # Mostrar el primer frame (estado inicial) antes de que los agentes calculen la primera acción
    draw_game(screen, game_state, action=None)
    pygame.display.flip()
    # breve pausa para asegurar que el frame inicial se perciba
    pygame.time.delay(200)

    running = True
    while running:
        clock.tick(FPS)

        # Eventos
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # --- Turno de los agentes ---
        if game_state.isWin() or game_state.isLose():
            print("¡Fin del juego!", "Ganaste" if game_state.isWin() else "Perdiste")
            time.sleep(3)
            running = False
            continue

        # Turno jugador
        actionA = agentA.getAction(game_state)
        # Depuración: mostrar acción y posición antes/después
        tankA = game_state.getTeamATank()
        pos_before = tankA.getPos() if tankA else None
        print(f"[DEBUG] Agent action: {actionA} | pos_before={pos_before}")
        if actionA:
            game_state.applyTankAction(0, actionA)
        pos_after = tankA.getPos() if tankA else None
        print(f"[DEBUG] pos_after={pos_after} | score={game_state.score} | time={game_state.current_time}")

        # Turnos enemigos
        for i, enemy_agent in enumerate(enemies, start=1):
            actionB = enemy_agent.getAction(game_state)
            if actionB:
                game_state.applyTankAction(i, actionB)

        # Avanzar físicas
        game_state.moveBullets()
        game_state._check_collisions()
        game_state._handle_deaths_and_respawns()

        # Avanzar el tiempo del juego (ticks)
        try:
            game_state.current_time += 1
        except Exception:
            pass

        # Actualizar el score en la partida en vivo usando la función de evaluación
        try:
            game_state.score = game_state.evaluate_state()
        except Exception:
            # Si evaluate_state falla por alguna razón, dejar el score tal cual
            pass

        # Dibujar estado (pasar la acción elegida por el agente 0)
        draw_game(screen, game_state, action=actionA)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        # Graceful shutdown if user sends Ctrl-C from terminal
        try:
            pygame.quit()
        except Exception:
            pass
        print("Interrupted by user. Exiting...")
        sys.exit(0)
