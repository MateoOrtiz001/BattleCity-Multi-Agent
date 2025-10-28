from src.agents.minimax import AlphaBetaAgent
from src.gameClass.game import BattleCityGame
from src.gameClass.scenarios.level1 import get_level1
import time

def test_minimax_timing():
    # Crear juego con el nivel más pequeño
    game = BattleCityGame(board_size=8)
    layout = get_level1()
    game.initialize(layout)
    
    # Probar diferentes profundidades
    depths = [1, 2, 3]  # Esto resultará en búsquedas de 4, 8 y 12 niveles
    
    for depth in depths:
        print(f"\nPrueba con profundidad {depth} ({depth * 4} niveles - {depth} turnos completos):")
        agent = AlphaBetaAgent(depth=str(depth), tankIndex=0)
        
        # Medir tiempo
        start_time = time.time()
        action = agent.getAction(game)
        end_time = time.time()
        
        print(f"Acción elegida: {action}")
        print(f"Tiempo total: {end_time - start_time:.3f} segundos")
        print(f"Nodos expandidos: {agent.expanded_nodes}")
        print("-" * 50)

if __name__ == "__main__":
    test_minimax_timing()