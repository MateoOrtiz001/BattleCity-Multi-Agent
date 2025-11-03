import argparse
import time

from src.gameClass.game import BattleCityGame
from src.gameClass.scenarios.level1 import get_level1
from src.gameClass.scenarios.level2 import get_level2
from src.gameClass.scenarios.level3 import get_level3
from src.gameClass.scenarios.level4 import get_level4
from src.agents.minimax import MinimaxAgent, AlphaBetaAgent
from src.agents.expectimax import ExpectimaxAgent, ExpectimaxAlphaBetaAgent
from src.agents.mcts import MCTSAgent
from src.gameClass.enemy_scripts import ScriptedEnemyAgent


def build_agent(agent_type: str, depth: int, time_limit: float):
    agent_type = agent_type.lower()
    if agent_type == "minimax":
        return MinimaxAgent(depth=str(depth), tankIndex=0)
    if agent_type == "alphabeta":
        return AlphaBetaAgent(depth=str(depth), tankIndex=0)
    if agent_type == "mcts":
        return MCTSAgent(simulations=300, rollout_depth=40, time_limit=time_limit, tankIndex=0)
    if agent_type == "expectimax":
        return ExpectimaxAgent(depth=str(depth), tankIndex=0, time_limit=time_limit)
    if agent_type in ("expectimax_ab", "expectimaxalpha"):
        return ExpectimaxAlphaBetaAgent(depth=str(depth), tankIndex=0, time_limit=time_limit)
    # por defecto
    return AlphaBetaAgent(depth=str(depth), tankIndex=0)


def build_level(level_name: str):
    name = (level_name or "level1").lower()
    if name == "level1":
        return get_level1()
    if name == "level2":
        return get_level2()
    if name == "level3":
        return get_level3()
    if name == "level4":
        return get_level4()
    # default
    return get_level1()


def run_headless_game(agent_type: str = "expectimax_ab", depth: int = 12, time_limit: float = 0.7, level_name: str = "level1"):
    """Ejecuta una partida sin entorno gráfico y devuelve (winner, turns, score)."""
    layout = build_level(level_name)
    game = BattleCityGame(9)
    game.initialize(layout)

    # Alias para compatibilidad de agentes
    if not hasattr(game, 'teamA_tanks'):
        game.teamA_tanks = [game.teamA_tank] if getattr(game, 'teamA_tank', None) else []

    # Agente que controla al tanque A (índice 0)
    agentA = build_agent(agent_type, depth, time_limit)

    # Enemigos scriptados
    game.scripted_agents = getattr(game, 'scripted_agents', {})
    for i in range(1, len(game.teamB_tanks) + 1):
        if i not in game.scripted_agents:
            game.scripted_agents[i] = ScriptedEnemyAgent(i, script_type='attack_base')

    num_tanks = len(game.teamA_tanks) + len(game.teamB_tanks)
    last_actions = [None] * max(1, num_tanks)

    # Loop de juego
    while not game.is_terminal():
        for tank_index in range(num_tanks):
            # Scripted enemies
            scripted = getattr(game, 'scripted_agents', {})
            if scripted and (tank_index in scripted):
                act = scripted[tank_index].getAction(game)
                game = game.generateSuccessor(tank_index, act)
                last_actions[tank_index] = act
                continue

            # Agente de búsqueda
            prev_index = getattr(agentA, 'index', None)
            agentA.index = tank_index
            try:
                act = agentA.getAction(game)
                game = game.generateSuccessor(tank_index, act)
                last_actions[tank_index] = act
            finally:
                if prev_index is not None:
                    agentA.index = prev_index

    # Resultado
    if getattr(game, 'base', None) and game.base.isDestroyed():
        winner = "Enemigos"
    elif getattr(game, 'reserves_B', 0) == 0:
        winner = "Equipo A"
    elif getattr(game, 'current_time', 0) >= getattr(game, 'time_limit', 0):
        winner = "EMPATE (tiempo)"
    else:
        winner = "Sin resultado claro"

    try:
        score = game.evaluate_state(None)
    except Exception:
        score = game.evaluate_state(game.getState())

    turns = getattr(game, 'current_time', 0)
    return winner, turns, score


def main():
    parser = argparse.ArgumentParser(description="Run headless BattleCity multiagent tests")
    parser.add_argument("--games", type=int, default=10, help="Número de partidas a ejecutar")
    parser.add_argument("--agent", type=str, default="expectimax_ab", help="Tipo de agente (minimax|alphabeta|expectimax|expectimax_ab|mcts)")
    parser.add_argument("--depth", type=int, default=12, help="Profundidad base (turnos, se multiplican en el agente)")
    parser.add_argument("--time_limit", type=float, default=0.7, help="Límite de tiempo por decisión (s), si aplica")
    parser.add_argument("--level", type=str, default="level1", help="Nivel (level1|level2|level3|level4)")
    args = parser.parse_args()

    total_A = total_B = total_draw = 0

    print(f"\n=== Ejecutando {args.games} partidas headless ===")
    print(f"Agente: {args.agent} | depth={args.depth} | time_limit={args.time_limit}s | nivel={args.level}\n")

    for i in range(1, args.games + 1):
        t0 = time.time()
        winner, turns, score = run_headless_game(args.agent, args.depth, args.time_limit, args.level)
        dt = time.time() - t0
        print(f"Partida {i:02d}: winner={winner:>14} | turns={turns:4d} | score={score:8.1f} | tiempo={dt:5.2f}s")

        if winner == "Equipo A":
            total_A += 1
        elif winner == "Enemigos":
            total_B += 1
        else:
            total_draw += 1

    print("\n=== Resumen ===")
    print(f"Equipo A: {total_A} | Enemigos: {total_B} | Empates: {total_draw}")


if __name__ == "__main__":
    main()