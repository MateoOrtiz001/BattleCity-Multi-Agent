import pygame
import sys
import os

# Añadir el directorio raíz al path para poder importar los módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.gameClass.game import BattleCityGame
#from src.gameClass.scenarios.level1 import get_layout
from src.gameClass.scenarios.level2 import get_layout

# Inicializar Pygame
pygame.init()
CELL_SIZE = 32
GRID_SIZE = 21
WIDTH, HEIGHT = CELL_SIZE * GRID_SIZE, CELL_SIZE * GRID_SIZE
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Battle City AI Prototype")
clock = pygame.time.Clock()

# Colores
COLORS = {
    'background': (0, 0, 0),
    'brick': (200, 80, 50),
    'steel': (130, 130, 130),
    'tankA': (0, 200, 0),
    'tankB': (0, 100, 255),
    'base': (255, 255, 0),
    'bullet': (255, 255, 255),
}

# Crear juego
game = BattleCityGame()  # Asegúrate de inicializarlo con tanques, muros y bases
game.initialize(get_layout())  # Usar el layout definido en level1.py
running = True

def draw_game():
    """Dibuja el estado actual del juego."""
    screen.fill(COLORS['background'])

    # Muros
    for wall in game.walls:
        if not wall.is_destroyed:
            color = COLORS['brick'] if wall.wall_type == 'brick' else COLORS['steel']
            x, y = wall.position
            pygame.draw.rect(screen, color, (x*CELL_SIZE, (GRID_SIZE-1-y)*CELL_SIZE, CELL_SIZE, CELL_SIZE))

    # Bases
    for base in [game.baseA, game.baseB]:
        if not base.is_destroyed:
            x, y = base.position
            pygame.draw.rect(screen, COLORS['base'], (x*CELL_SIZE, (GRID_SIZE-1-y)*CELL_SIZE, CELL_SIZE, CELL_SIZE))

    # Tanques
    for tank in game.teamA_tanks:
        if tank.is_alive:
            x, y = tank.position
            pygame.draw.rect(screen, COLORS['tankA'], (x*CELL_SIZE, (GRID_SIZE-1-y)*CELL_SIZE, CELL_SIZE, CELL_SIZE))
    for tank in game.teamB_tanks:
        if tank.is_alive:
            x, y = tank.position
            pygame.draw.rect(screen, COLORS['tankB'], (x*CELL_SIZE, (GRID_SIZE-1-y)*CELL_SIZE, CELL_SIZE, CELL_SIZE))

    # Balas
    for bullet in game.bullets:
        if bullet.is_active:
            x, y = bullet.position
            pygame.draw.circle(screen, COLORS['bullet'], (int(x*CELL_SIZE+CELL_SIZE/2), int((GRID_SIZE-1-y)*CELL_SIZE+CELL_SIZE/2)), 4)

    pygame.display.flip()

# Control manual simple (para pruebas)
def handle_input():
    global game
    keys = pygame.key.get_pressed()
    tank = game.getState()['teamA_tanks'][0]  # controlamos solo el primer tanque de A

    if keys[pygame.K_UP]:
        game = game.generateSuccessor(0, 'MOVE_UP')
    elif keys[pygame.K_DOWN]:
        game = game.generateSuccessor(0, 'MOVE_DOWN')
    elif keys[pygame.K_LEFT]:
        game = game.generateSuccessor(0, 'MOVE_LEFT')
    elif keys[pygame.K_RIGHT]:
        game = game.generateSuccessor(0, 'MOVE_RIGHT')
    elif keys[pygame.K_SPACE]:
        game = game.generateSuccessor(0, 'FIRE')

    return game

# Bucle principal
while running:
    # limitar FPS y obtener delta time en segundos
    dt = clock.tick(10) / 1000.0

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Control de jugador
    game = handle_input()

    # Actualizar balas (paso sin movimiento)
    for _ in range(1):
        game = game.generateSuccessor(0, 'NONE')

    # Avanzar tiempo real del juego (respawns, control de tiempo)
    game.advance_time(dt)

    # Comprobar fin de juego
    if game.is_terminal():
        # Determinar resultado
        result = 'Draw'
        if game.baseA.isDestroyed() and not game.baseB.isDestroyed():
            result = 'Team B wins'
        elif game.baseB.isDestroyed() and not game.baseA.isDestroyed():
            result = 'Team A wins'
        elif game.elapsed_time >= game.time_limit_seconds:
            # Empate por tiempo: se puede evaluar por puntaje
            result = 'Time up - Draw'

        pygame.display.set_caption(f'Game Over - {result}')
        # dibujar última fotograma
        draw_game()
        # esperar un par de segundos para que el usuario vea el resultado
        pygame.time.delay(2000)
        break

    draw_game()

pygame.quit()
