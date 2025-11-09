import time
from pathlib import Path
from typing import Tuple

from src.gameClass.game import BattleCityState
from src.agents.enemyAgent import ScriptedEnemyAgent


def run_single_game(layout, agent, max_ticks=None, debug=False, return_stats=False):
    """Ejecuta una partida completa en modo headless.
    layout: lista de strings con el mapa
    agent: instancia con método getAction(gameState)
    max_ticks: si se da, fuerza un draw si se alcanzan
    Retorna: 'win' | 'loss' | 'draw'
    """
    state = BattleCityState()
    state.initialize(layout)

    # Crear agentes enemigos según la cantidad de tanques B detectados
    enemies = [ScriptedEnemyAgent(i+1, script_type='attack_base') for i in range(len(state.getTeamBTanks()))]

    ticks = 0
    # Estadísticas
    sim_start = time.time()
    decision_counts = 0
    total_nodes = 0
    nodes_per_decision = []
    try:
        while True:
            if state.isWin():
                if return_stats:
                    duration = time.time() - sim_start
                    avg_nodes = (total_nodes / decision_counts) if decision_counts > 0 else 0.0
                    stats = {
                        'duration': duration,
                        'decision_count': decision_counts,
                        'total_nodes': total_nodes,
                        'avg_nodes_per_search': avg_nodes,
                        'nodes_per_decision': nodes_per_decision,
                    }
                    return 'win', stats
                return 'win'
            if state.isLose():
                if return_stats:
                    duration = time.time() - sim_start
                    avg_nodes = (total_nodes / decision_counts) if decision_counts > 0 else 0.0
                    stats = {
                        'duration': duration,
                        'decision_count': decision_counts,
                        'total_nodes': total_nodes,
                        'avg_nodes_per_search': avg_nodes,
                        'nodes_per_decision': nodes_per_decision,
                    }
                    return 'loss', stats
                return 'loss'
            if state.isLimitTime():
                if return_stats:
                    duration = time.time() - sim_start
                    avg_nodes = (total_nodes / decision_counts) if decision_counts > 0 else 0.0
                    stats = {
                        'duration': duration,
                        'decision_count': decision_counts,
                        'total_nodes': total_nodes,
                        'avg_nodes_per_search': avg_nodes,
                        'nodes_per_decision': nodes_per_decision,
                    }
                    return 'draw', stats
                return 'draw'
            if max_ticks is not None and ticks >= max_ticks:
                if return_stats:
                    duration = time.time() - sim_start
                    avg_nodes = (total_nodes / decision_counts) if decision_counts > 0 else 0.0
                    stats = {
                        'duration': duration,
                        'decision_count': decision_counts,
                        'total_nodes': total_nodes,
                        'avg_nodes_per_search': avg_nodes,
                        'nodes_per_decision': nodes_per_decision,
                    }
                    return 'draw', stats
                return 'draw'

            # Turno del agente principal (índice 0)
            try:
                # Medir nodos expandidos si el agente expone `node_count`
                actionA = agent.getAction(state)
                try:
                    # Algunos agentes usan `node_count` y otros `expanded_nodes`
                    nodes = getattr(agent, 'node_count', None)
                    if nodes is None:
                        nodes = getattr(agent, 'expanded_nodes', None)
                    if nodes is not None:
                        decision_counts += 1
                        total_nodes += nodes
                        nodes_per_decision.append(nodes)
                except Exception:
                    pass
            except Exception as e:
                if debug:
                    print(f"[utils.run_single_game] Excepción en agent.getAction: {e}")
                # fallback: STOP
                actionA = 'STOP'

            if actionA:
                try:
                    state.applyTankAction(0, actionA)
                except Exception as e:
                    if debug:
                        print(f"[utils.run_single_game] Acción ilegal/applyTankAction(0): {e}")

            # Turnos enemigos (índices 1..N)
            for i, enemy_agent in enumerate(enemies, start=1):
                try:
                    actionB = enemy_agent.getAction(state)
                except Exception as e:
                    if debug:
                        print(f"[utils.run_single_game] Excepción en enemy.getAction (idx={i}): {e}")
                    actionB = 'STOP'
                if actionB:
                    try:
                        state.applyTankAction(i, actionB)
                    except Exception:
                        # Silenciar errores en acciones enemigas para permitir avance
                        if debug:
                            print(f"[utils.run_single_game] applyTankAction fallo para enemigo idx={i} action={actionB}")

            # Avanzar físicas y gestionar colisiones/respawns
            try:
                state.moveBullets()
                state._check_collisions()
                state._handle_deaths_and_respawns()
            except Exception:
                if debug:
                    print("[utils.run_single_game] Warning: fallo en físicas/colisiones")

            # Avanzar tiempo y contador de ticks
            try:
                state.current_time += 1
            except Exception:
                pass
            ticks += 1

            # Actualizar score si es útil
            try:
                state.score = state.evaluate_state()
            except Exception:
                pass

    except KeyboardInterrupt:
        # Permitir abortar desde teclado si se ejecuta interactivamente
        if return_stats:
            duration = time.time() - sim_start
            avg_nodes = (total_nodes / decision_counts) if decision_counts > 0 else 0.0
            stats = {
                'duration': duration,
                'decision_count': decision_counts,
                'total_nodes': total_nodes,
                'avg_nodes_per_search': avg_nodes,
                'nodes_per_decision': nodes_per_decision,
            }
            return 'draw', stats
        return 'draw'

    # Fin de la simulación
    duration = time.time() - sim_start
    avg_nodes = (total_nodes / decision_counts) if decision_counts > 0 else 0.0
    stats = {
        'duration': duration,
        'decision_count': decision_counts,
        'total_nodes': total_nodes,
        'avg_nodes_per_search': avg_nodes,
        'nodes_per_decision': nodes_per_decision,
    }

    if return_stats:
        return result, stats
    return result


def evaluate_result(result: str) -> Tuple[int,int,int]:
    """Convierte 'win'|'loss'|'draw' en incremento para (wins,losses,draws)."""
    if result == 'win':
        return (1,0,0)
    if result == 'loss':
        return (0,1,0)
    return (0,0,1)
