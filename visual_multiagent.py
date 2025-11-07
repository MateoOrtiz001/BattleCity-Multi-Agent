import pygame
import sys
import time
from src.gameClass.game import BattleCityGame
from src.gameClass.scenarios.level1 import get_level1
from src.gameClass.scenarios.level2 import get_level2
from src.gameClass.scenarios.level3 import get_level3
from src.gameClass.scenarios.level4 import get_level4
from src.agents.minimax import MinimaxAgent, AlphaBetaAgent
from src.agents.expectimax import ExpectimaxAgent, ExpectimaxAlphaBetaAgent
from src.agents.mcts import MCTSAgent
from src.gameClass.tank import Tank
from src.gameClass.walls import Wall
from src.gameClass.base import Base
from src.gameClass.bullet import Bullet
from agents.enemyAgent import ScriptedEnemyAgent

# Inicializar Pygame
pygame.init()
CELL_SIZE = 32
GRID_SIZE = 13
WIDTH, HEIGHT = CELL_SIZE * GRID_SIZE, CELL_SIZE * GRID_SIZE
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Battle City - MultiAgent Visualization")
clock = pygame.time.Clock()

# Colores
COLORS = {
    'background': (0, 0, 0),
    'brick': (200, 80, 50),
    'steel': (235, 235, 235),
    'tankA': (186, 177, 154),
    'tankB': (145, 145, 145),
    'base': (255, 255, 0),
    'bullet': (255, 255, 255),
    'text': (255, 255, 255),
}

def draw_game(game, last_actions=None):
    """Dibuja el estado actual del juego."""
    screen.fill(COLORS['background'])

    # Dibujar muros
    grid = getattr(game, 'board_size', GRID_SIZE)
    for wall in game.walls:
        if not wall.is_destroyed:
            color = COLORS['brick'] if wall.wall_type == 'brick' else COLORS['steel']
            x, y = wall.position
            pygame.draw.rect(screen, color, (x*CELL_SIZE, (grid-1-y)*CELL_SIZE, CELL_SIZE, CELL_SIZE))

    # Dibujar base (modelo actual: una única base en game.base)
    base = getattr(game, 'base', None)
    if base and not base.isDestroyed():
        x, y = base.position
        color = COLORS['base']
        pygame.draw.rect(screen, color, (x*CELL_SIZE, (grid-1-y)*CELL_SIZE, CELL_SIZE, CELL_SIZE))

    # Dibujar tanques (adaptar al API actual)
    tanks_list = []
    if hasattr(game, 'teamA_tanks'):
        tanks_list.extend(game.teamA_tanks)
    elif hasattr(game, 'teamA_tank') and game.teamA_tank is not None:
        tanks_list.append(game.teamA_tank)
    tanks_list.extend(getattr(game, 'teamB_tanks', []))

    for tank in tanks_list:
        if tank.is_alive:
            x, y = tank.position
            color = COLORS['tankA'] if tank.team == 'A' else COLORS['tankB']
            pygame.draw.rect(screen, color, (x*CELL_SIZE, (grid-1-y)*CELL_SIZE, CELL_SIZE, CELL_SIZE))

    # Dibujar balas
    for bullet in game.bullets:
        if bullet.is_active:
            x, y = bullet.position
            pygame.draw.circle(screen, COLORS['bullet'], 
                             (int(x*CELL_SIZE + CELL_SIZE/2), 
                              int((grid-1-y)*CELL_SIZE + CELL_SIZE/2)), 4)

    # Dibujar información del juego
    font = pygame.font.Font(None, 24)
    
    # Información de base (modelo actual)
    base_status = f"Base: {'En pie' if base and not base.isDestroyed() else 'Destruida'}"
    base_surface = font.render(base_status, True, COLORS['text'])
    screen.blit(base_surface, (10, 10))

    # Tiempo transcurrido
    # Mostrar tiempo segun current_time (ticks)
    ct = getattr(game, 'current_time', 0)
    time_text = f"Time: {ct}"
    time_surface = font.render(time_text, True, COLORS['text'])
    screen.blit(time_surface, (WIDTH//2 - 50, 10))

    # Mostrar score (evaluación heurística del estado)
    try:
        score_val = game.evaluate_state(None)
    except Exception:
        try:
            score_val = game.evaluate_state(game.getState())
        except Exception:
            score_val = None

    if score_val is not None:
        score_text = f"Score: {score_val:.1f}"
        score_surface = font.render(score_text, True, COLORS['text'])
        screen.blit(score_surface, (WIDTH - 180, 10))

    # Mostrar acciones recientes por tanque (si se pasaron)
    if last_actions:
        # Dibujar cada acción en la esquina superior izquierda, bajo la info de base
        y_off = 40
        for idx, act in enumerate(last_actions):
            act_text = f"T{idx}: {str(act)}"
            act_surface = font.render(act_text, True, COLORS['text'])
            screen.blit(act_surface, (10, y_off))
            y_off += 18

    pygame.display.flip()

def run_visual_game(agent_type="alphabeta", depth=4, level_func=get_level1, fps=5):
    """
    Ejecuta una partida con visualización.
    
    Args:
        agent_type: "minimax" o "alphabeta"
        depth: profundidad de búsqueda (debe ser múltiplo de 4)
        level_func: función que devuelve el layout del nivel
        fps: frames por segundo para la visualización
    """
    # Crear el juego y los agentes
    game = BattleCityGame(9)
    layout = level_func()
    game.initialize(layout)

    # Ajustar tamaño de la ventana según el tamaño del tablero real
    grid_size = game.board_size
    global GRID_SIZE, WIDTH, HEIGHT, screen
    GRID_SIZE = grid_size
    WIDTH, HEIGHT = CELL_SIZE * GRID_SIZE, CELL_SIZE * GRID_SIZE
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    
    # Crear el agente único que controlará los tanques. En cada turno ajustaremos
    # `single_agent.index` al tanque a actuar.
    if agent_type.lower() == "minimax":
        AgentClass = MinimaxAgent
        kwargs = {'depth': depth}
    elif agent_type.lower() == 'alphabeta':
        AgentClass = AlphaBetaAgent
        kwargs = {'depth': depth}
    elif agent_type.lower() == 'mcts':
        AgentClass = MCTSAgent
        # default simulations; you can tune this when calling run_visual_game
        kwargs = {'simulations': 300, 'rollout_depth': 40, 'time_limit': 1.0}
    elif agent_type.lower() == 'expectimax':
        AgentClass = ExpectimaxAgent
        kwargs = {'depth': depth, 'time_limit': 1 }
    elif agent_type.lower() == 'expectimax_ab':
        AgentClass = ExpectimaxAlphaBetaAgent
        kwargs = {'depth':  depth, 'time_limit': 1 }
    else:
        AgentClass = AlphaBetaAgent
        kwargs = {'depth': depth }

    # Crear agentes por tanque. Usaremos agentes scriptados si existen,
    # y para los demás crearemos una instancia del AgentClass por cada tanque.
    template_agent = None
    try:
        template_agent = AgentClass(**kwargs)
    except Exception:
        # si la construcción falla por argumentos, intentar sin kwargs
        try:
            template_agent = AgentClass()
        except Exception:
            template_agent = None
    # Adaptar API: algunos agentes esperan teamA_tanks (lista). Creamos alias si falta.
    if not hasattr(game, 'teamA_tanks'):
        game.teamA_tanks = [game.teamA_tank] if getattr(game, 'teamA_tank', None) else []
    # Instanciar agentes scriptados para los tanques enemigos (si se desea)
    # Colocamos controladores en game.scripted_agents para que la búsqueda también los respete
    try:
        game.scripted_agents = getattr(game, 'scripted_agents', {})
        for i in range(1, len(game.teamB_tanks) + 1):
            # Si no existe ya, crear un ScriptedEnemyAgent que intente atacar la base
            if i not in game.scripted_agents:
                game.scripted_agents[i] = ScriptedEnemyAgent(i, script_type='attack_base')
    except Exception:
        # Si algo falla con scripted agents, no bloquear la ejecución
        game.scripted_agents = {}

    # Número total de tanques
    num_tanks = len(game.teamA_tanks) + len(game.teamB_tanks)
    # Trackear la última acción tomada por cada tanque para depuración/visualización
    last_actions = [None] * max(1, num_tanks)

    # Crear un agente por cada tanque: usar los scriptados si existen, sino instanciar AgentClass
    agents = {}
    for i in range(num_tanks):
        if i in game.scripted_agents:
            agents[i] = game.scripted_agents[i]
        else:
            try:
                a = AgentClass(**kwargs)
            except Exception:
                # fallback al template si no se puede construir con kwargs
                a = template_agent if template_agent is not None else AgentClass()
            # Asegurar que el agente conoce su índice
            try:
                a.index = i
            except Exception:
                pass
            try:
                a.agentIndex = i
            except Exception:
                pass
            agents[i] = a

    # Para compatibilidad con hotkeys y comportamiento previo, conservar referencia al agente del tank 0
    single_agent = agents.get(0, None)
    # Nota: ya que nuestro BattleCityGame implementa generateSuccessor que avanza
    # balas/tiempo tras el último tanque, aplicaremos acciones por turnos secuenciales.
    
    turn = 0
    last_update = time.time()
    running = True
    paused = False  # Inicializar variable paused
    
    while running:
        # Manejo de eventos de Pygame
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:  # Pausar/Reanudar
                    paused = not paused
                elif event.key in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS):
                    # Aumentar el time_limit del agente (si lo soporta)
                    if hasattr(single_agent, 'time_limit'):
                        try:
                            single_agent.time_limit = max(0.05, float(single_agent.time_limit) + 0.5)
                            print(f"[Hotkey] time_limit -> {single_agent.time_limit:.2f}s")
                        except Exception:
                            pass
                elif event.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                    # Disminuir el time_limit del agente (si lo soporta)
                    if hasattr(single_agent, 'time_limit'):
                        try:
                            single_agent.time_limit = max(0.05, float(single_agent.time_limit) - 0.5)
                            print(f"[Hotkey] time_limit -> {single_agent.time_limit:.2f}s")
                        except Exception:
                            pass
        
        if game.is_terminal():
            # Mostrar resultado final por 3 segundos
            draw_game(game, last_actions)
            pygame.display.flip()
            time.sleep(3)
            break

        # Actualizar el tiempo real (opcional). Usamos ticks de juego vía generateSuccessor.
        # Mantener last_update por si se quiere medir tiempo real.
        current_time = time.time()
        last_update = current_time

        # Decisiones por tanque y aplicación secuencial
        for tank_index in range(num_tanks):
            agent = agents.get(tank_index)
            if agent is None:
                # No hay agente definido, saltar
                continue
            # controlar salida suprimida para agentes que imprimen
            try:
                agent.suppress_output = (tank_index != (num_tanks - 1))
            except Exception:
                pass

            prev_index = getattr(agent, 'index', None)
            try:
                agent.index = tank_index
            except Exception:
                pass
            try:
                agent.agentIndex = tank_index
            except Exception:
                pass

            try:
                # DEBUG: imprimir información previa a la decisión del agente
                try:
                    agent_class = agent.__class__.__name__
                except Exception:
                    agent_class = str(type(agent))
                print(f"[DBG] TANK {tank_index} | CALL getAction -> agent_class={agent_class} index={getattr(agent,'index',None)} agentIndex_attr={getattr(agent,'agentIndex',None)}")
                try:
                    legal = game.getLegalActions(tank_index)
                except Exception as e:
                    legal = f"ERROR getting legal actions: {e}"
                print(f"[DBG] TANK {tank_index} | legal_actions={legal}")

                act = agent.getAction(game)
                # DEBUG: acción retornada por el agente
                print(f"[DBG] TANK {tank_index} | RETURN getAction -> action={act}")
                game = game.generateSuccessor(tank_index, act)
                # registrar acción
                try:
                    last_actions[tank_index] = act
                except Exception:
                    pass
            finally:
                if prev_index is not None:
                    try:
                        agent.index = prev_index
                    except Exception:
                        pass
                try:
                    agent.suppress_output = False
                except Exception:
                    pass
        turn += 1

        # Dibujar el estado actual
        draw_game(game, last_actions)
        # También imprimir info en consola breve para depuración
        try:
            s = game.evaluate_state(None)
            print(f"Turn {turn} | Score: {s:.1f} | reserves_A={getattr(game,'reserves_A',None)} reserves_B={getattr(game,'reserves_B',None)}")
        except Exception:
            pass
        clock.tick(fps)  # Controlar la velocidad de actualización
    
    # Cerrar ventana
    pygame.quit()

    # Determinar el ganador de forma simple con el modelo actual
    if getattr(game, 'base', None):
        if game.base.isDestroyed():
            winner = "Enemigos"
        elif getattr(game, 'reserves_B', 0) == 0:
            winner = "Equipo A"
        elif getattr(game, 'current_time', 0) >= getattr(game, 'time_limit', 0):
            winner = "EMPATE (tiempo)"
        else:
            winner = "Sin resultado claro"
    else:
        winner = "Sin resultado claro"

    print(f"\n=== Fin del juego ===")
    print(f"Ganador: {winner}")
    print(f"Turnos totales: {turn}")
    print(f"Tiempo total (ticks): {getattr(game, 'current_time', 0)}")
    print(f"Base destruida: {game.base.isDestroyed() if getattr(game, 'base', None) else 'N/A'}")

if __name__ == "__main__":
    # Configuración de la partida
    AGENT_TYPE = "expectimax"  # "minimax", "alphabeta" or "mcts" or "expectimax" or "expectimax_ab"
    DEPTH = 2  # Profundidad de búsqueda (múltiplo de 4 recomendado). Bajada para pruebas.
    LEVEL = get_level1  # Nivel a usar
    FPS = 30  # Velocidad de visualización
    
    print(f"Iniciando partida visual con {AGENT_TYPE.upper()}...")
    run_visual_game(AGENT_TYPE, DEPTH, LEVEL, FPS)