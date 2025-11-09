import json
from pathlib import Path
from statistics import mean
from experiments.loader import get_map, load_game_assets
from experiments.agent_expectimax import make_agent
from experiments.utils import run_single_game, evaluate_result


def run_experiments(num_games=10, depth=3, time_limit=8, debug=False, map_index=0, base_path=None):
    """Corre num_games partidas en el mapa map_index usando Expectimax.
    Guarda resultados en JSON y devuelve la lista [wins, losses, draws].
    """
    base = Path(base_path) if base_path is not None else Path.cwd()
    # Preparar recursos (placeholder)
    load_game_assets(base)

    layout = get_map(base, map_index)

    wins = losses = draws = 0
    per_game_stats = []

    for i in range(num_games):
        agent = make_agent(depth=depth, time_limit=time_limit, debug=debug)
        # Pedimos estadísticas por simulación
        out = run_single_game(layout, agent, debug=debug, return_stats=True)
        if isinstance(out, tuple) and len(out) == 2:
            result, stats = out
        else:
            result = out
            stats = None

        w,l,d = evaluate_result(result)
        wins += w; losses += l; draws += d

        if stats is not None:
            stats_record = {'game_index': i, 'result': result}
            stats_record.update(stats)
            per_game_stats.append(stats_record)

        if debug:
            print(f"[experiment] Juego {i+1}/{num_games} -> {result} | stats: {stats}")

    results = [wins, losses, draws]

    # Guardar en disco
    out_dir = base / 'experiments_results'
    out_dir.mkdir(parents=True, exist_ok=True)
    fname = f"results_map{map_index}_expectimax_depth{depth}.json"
    out_path = out_dir / fname
    # Guardar también las estadísticas detalladas
    out_data = {
        'summary': {
            'wins': wins,
            'losses': losses,
            'draws': draws,
            'num_games': num_games,
        },
        'per_game': per_game_stats,
    }

    # Agregar agregados si hay stats
    if per_game_stats:
        durations = [g['duration'] for g in per_game_stats]
        avg_nodes = [g['avg_nodes_per_search'] for g in per_game_stats]
        total_nodes = sum(g.get('total_nodes', 0) for g in per_game_stats)
        total_decisions = sum(g.get('decision_count', 0) for g in per_game_stats)
        out_data['aggregate'] = {
            'mean_duration_per_simulation': mean(durations) if durations else 0.0,
            'mean_avg_nodes_per_search': mean(avg_nodes) if avg_nodes else 0.0,
            'overall_total_nodes': total_nodes,
            'overall_total_decisions': total_decisions,
            'overall_avg_nodes_per_search': (total_nodes / total_decisions) if total_decisions > 0 else 0.0,
        }

    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(out_data, f, indent=2)

    print(f"Resultados guardados en {out_path}")
    print(f"Victorias: {wins}, Derrotas: {losses}, Empates: {draws}")
    return results


if __name__ == '__main__':
    # Ejecución por defecto rápida para testing
    run_experiments(num_games=1, depth=1, time_limit=1, debug=True)
