from src.gameClass.game import BattleCityGame
from src.gameClass.scenarios.level1 import get_level1
from src.gameClass.scenarios.level2 import get_level2
from src.gameClass.scenarios.level3 import get_level3
from src.gameClass.scenarios.level4 import layout as level4_layout
from src.agents.minimax import MinimaxAgent, AlphaBetaAgent
import time

def run_quick_game(agent_type="minimax", depth=4, layout=None):
    """
    Ejecuta una partida rápida y muestra un resumen de los movimientos y el resultado.
    
    Args:
        agent_type: "minimax" o "alphabeta"
        depth: profundidad de búsqueda (debe ser múltiplo de 4)
        layout: layout del nivel (si es None, usa level4_layout)
    """
    # Crear el juego y los agentes
    game = BattleCityGame(board_size=8)  # Usar tablero 8x8 para pruebas rápidas
    game.initialize(layout if layout else level4_layout)
    
    # Crear los agentes para cada tanque
    if agent_type.lower() == "minimax":
        AgentClass = MinimaxAgent
    else:
        AgentClass = AlphaBetaAgent
    
    agents = [
        AgentClass(depth=str(depth), tankIndex=0),  # Tank A1
        AgentClass(depth=str(depth), tankIndex=1),  # Tank B1
        AgentClass(depth=str(depth), tankIndex=2),  # Tank A2
        AgentClass(depth=str(depth), tankIndex=3)   # Tank B2
    ]
    
    start_time = time.time()
    turn = 0
    moves_summary = []
    
    # Loop principal del juego
    while not game.is_terminal():
        current_agent = turn % 4
        action = agents[current_agent].getAction(game)
        
        # Registrar el movimiento
        team = "A" if current_agent in [0, 2] else "B"
        tank_num = "1" if current_agent in [0, 1] else "2"
        moves_summary.append(f"Turn {turn + 1}: Team {team} Tank {tank_num} -> {action}")
        
        # Aplicar la acción
        game = game.generateSuccessor(current_agent, action)
        turn += 1
    
    # Calcular tiempo total
    total_time = time.time() - start_time
    
    # Determinar el ganador
    if game.baseA.isDestroyed() and game.baseB.isDestroyed():
        winner = "EMPATE (ambas bases destruidas)"
    elif game.baseA.isDestroyed():
        winner = "Equipo B"
    elif game.baseB.isDestroyed():
        winner = "Equipo A"
    elif game.elapsed_time >= game.time_limit_seconds:
        # Si se acabó el tiempo, gana quien tenga la base con más vida
        if game.baseA.health > game.baseB.health:
            winner = "Equipo A (por salud de base)"
        elif game.baseB.health > game.baseA.health:
            winner = "Equipo B (por salud de base)"
        else:
            winner = "EMPATE (igual salud en bases)"
    
    # Imprimir resumen
    print(f"\n=== Resumen de la partida ({agent_type.upper()}) ===")
    print(f"Profundidad de búsqueda: {depth}")
    print(f"Turnos totales: {turn}")
    print(f"Tiempo total: {total_time:.2f} segundos")
    print(f"Tiempo promedio por turno: {total_time/turn:.3f} segundos")
    print(f"Promedio de nodos expandidos por turno: {sum([a.expanded_nodes for a in agents])/turn:.1f}")
    print(f"\nGanador: {winner}")
    print(f"Base A: {'Destruida' if game.baseA.isDestroyed() else 'En pie'}")
    print(f"Base B: {'Destruida' if game.baseB.isDestroyed() else 'En pie'}")
    print("\nÚltimos 10 movimientos:")
    for move in moves_summary[-10:]:
        print(move)
    
    return winner, turn, total_time

if __name__ == "__main__":
    # Probar el algoritmo Alpha-Beta con IDS en el tablero pequeño
    print("\n=== Prueba en tablero 8x8 (Nivel 4) ===")
    
    # Usar Alpha-Beta con IDS
    print("\nEjecutando Alpha-Beta con IDS...")
    # Usamos profundidad 3 (12 niveles = 3 turnos completos de anticipación)
    winner, turns, total_time = run_quick_game("alphabeta", depth=3)
    
    print("\n=== Estadísticas Finales ===")
    print(f"Duración total de la partida: {total_time:.2f} segundos")
    print(f"Promedio de tiempo por turno: {total_time/turns:.3f} segundos")
    print(f"Total de turnos: {turns}")
    print(f"Ganador: {winner}")
    print("\n=== Comparación de rendimiento ===")
    print(f"{'Algoritmo':<15} {'Turnos':<10} {'Tiempo (s)':<12} {'Tiempo/Turno':<15} {'Ganador'}")
    print("-" * 60)
    print(f"{'Minimax':<15} {turns_minimax:<10} {time_minimax:<12.2f} {time_minimax/turns_minimax:<15.3f} {winner_minimax}")
    print(f"{'Alpha-Beta':<15} {turns_alphabeta:<10} {time_alphabeta:<12.2f} {time_alphabeta/turns_alphabeta:<15.3f} {winner_alphabeta}")