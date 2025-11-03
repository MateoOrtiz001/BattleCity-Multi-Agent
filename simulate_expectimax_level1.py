"""
Simulación simple en consola del nivel 1 usando Expectimax.
- Usa la implementación existente del juego (BattleCityState) y los agentes.
- Ajusta una "envoltura" (GameAdapter) que expone la API que espera ExpectimaxAgent
  (generateSuccessor, getLegalActions, getNumAgents, isWin/isLose/isLimitTime, etc).

Configuración solicitada:
- Algoritmo: Expectimax
- time_limit: 0.75 segundos
- depth: 16

Este script no abre ventana; corre en modo texto y muestra un resumen final.
"""

import copy
import time

from src.gameClass.game import BattleCityState
from src.gameClass.scenarios.level1 import get_level1
from src.gameClass.enemy_scripts import ScriptedEnemyAgent
from src.agents.expectimax import ExpectimaxAgent


class TeamBWrapper:
    """Pequeño wrapper para compatibilidad con código que espera
    un objeto con atributo `teamB_tanks`.
    """

    def __init__(self, tanks_list):
        self.teamB_tanks = tanks_list


class GameAdapter:
    """Adaptador que envuelve un BattleCityState y expone la API
    que buscan los agentes (generateSuccessor, getLegalActions, ...).

    Notas:
    - generateSuccessor / getSuccessor crean una copia profunda del estado,
      aplican la acción, avanzan las balas/resurrecciones si corresponde y
    - También expone atributos usados por ScriptedEnemyAgent (teamB_tanks, base, etc.).
    """

    def __init__(self, bc_state: BattleCityState):
        self._state = bc_state
        # No duplicar atributos: delegamos dinámicamente a través de __getattr__.

    # ---- atributos / métodos directos ----
    def getNumAgents(self):
        return self._state.getNumAgents()

    def isWin(self):
        return self._state.isWin()

    def isLose(self):
        return self._state.isLose()

    def isLimitTime(self):
        return self._state.isLimitTime()

    def getLegalActions(self, agentIndex):
        return self._state.getLegalActions(agentIndex)

    def getBase(self):
        return self._state.getBase()

    def getState(self):
        # Exponer el estado "crudo" cuando sea necesario
        return self._state

    # ---- successors (EXPECTIMAX llama a generateSuccessor y a veces a getSuccessor) ----
    def generateSuccessor(self, agentIndex, action):
        # Crear copia profunda del estado actual
        new_state = copy.deepcopy(self._state)
        # Aplicar la acción sobre la copia
        try:
            new_state.applyTankAction(agentIndex, action)
        except Exception:
            # Si la API falla, intentar emular comportamiento mínimo
            pass

        # Penalizar tiempo por acción del jugador (mismo comportamiento que en la base)
        if agentIndex == 0:
            try:
                new_state.score -= 1
            except Exception:
                pass

        # Si era el último agente del ciclo, actualizar balas / muertes / respawns
        try:
            if agentIndex == new_state.getNumAgents() - 1:
                new_state.moveBullets()
                new_state._handle_deaths_and_respawns()
            new_state._check_collisions()
        except Exception:
            # tolerancia a excepciones internas del engine para evitar fallo completo
            pass

        return GameAdapter(new_state)

    # alias para compatibilidad con implementaciones mixtas
    def getSuccessor(self, agentIndex, action):
        return self.generateSuccessor(agentIndex, action)

    def __getattr__(self, item):
        """Delegar al estado subyacente cualquier atributo/método no definido aquí.

        Esto hace que GameAdapter se comporte como un proxy casi transparente
        para BattleCityState, evitando errores cuando los agentes llaman
        métodos/propiedades directamente en el estado.
        """
        # Evitar recursión: getattr sobre _state directamente
        try:
            return getattr(self._state, item)
        except AttributeError:
            raise AttributeError(f"GameAdapter: neither adapter nor wrapped state have attribute '{item}'")


def run_simulation(time_limit_agent=0.75, depth=16, max_turns=1000, verbose=False):
    layout = get_level1()
    # Crear el estado inicial
    state = BattleCityState()
    state.initialize(layout)

    # Crear wrapper para pasar a los agentes
    wrapper = GameAdapter(state)

    # Crear agentes
    expectimax_agent = ExpectimaxAgent(depth=depth, time_limit=time_limit_agent)
    # Asegurar que el agente conoce su índice (usado por algunos agentes)
    try:
        expectimax_agent.index = 0
    except Exception:
        pass

    # Scripted enemies: crear uno por cada tanque enemigo
    num_agents = wrapper.getNumAgents()
    scripted_agents = {}
    for i in range(1, num_agents):
        scripted_agents[i] = ScriptedEnemyAgent(i, script_type='attack_base')

    # Estado de juego actual (modificable) - trabajamos sobre `state` directamente
    current_state = state
    turn = 0

    start_time_wall = time.time()

    while turn < max_turns:
        num_agents = current_state.getNumAgents()

        # Chequear final
        if current_state.isWin() or current_state.isLose() or current_state.isLimitTime():
            break

        # Ciclo de agentes
        for agent_index in range(num_agents):
            if current_state.isWin() or current_state.isLose() or current_state.isLimitTime():
                break

            # Crear wrapper para el estado actual para pasar al agente
            adapter_for_agent = GameAdapter(current_state)
            # Obtener acciones legales y dirección para debug cuando verbose
            try:
                legal_actions = adapter_for_agent.getLegalActions(agent_index)
            except Exception:
                legal_actions = []

            # Obtener dirección del tanque si está disponible
            try:
                tank_obj = current_state.getTankByIndex(agent_index)
                tank_dir = getattr(tank_obj, 'direction', None) if tank_obj is not None else None
            except Exception:
                # Fallback: buscar en estructuras directas
                try:
                    if agent_index == 0:
                        tank_dir = getattr(current_state, 'teamA_tank').direction
                    else:
                        tank_dir = current_state.teamB_tanks[agent_index - 1].direction
                except Exception:
                    tank_dir = None

            if verbose:
                print(f"[DBG] TANK {agent_index} | direction={tank_dir} | legal_actions={legal_actions}")

            if agent_index == 0:
                # Agente expectimax
                act = expectimax_agent.getAction(adapter_for_agent)
            else:
                # Scripted enemy
                a_agent = scripted_agents.get(agent_index)
                if a_agent is None:
                    # fallback: elegir una acción legal al azar
                    legal = adapter_for_agent.getLegalActions(agent_index)
                    act = legal[0] if legal else 'STOP'
                else:
                    act = a_agent.getAction(adapter_for_agent)

            if verbose:
                print(f"Turn {turn} | Agent {agent_index} -> {act}")

            # Aplicar la acción directamente al estado actual
            # Instrumentación: si es FIRE, registrar número de balas antes/después
            try:
                if act == 'FIRE' and verbose:
                    before = len(getattr(current_state, 'bullets', []))
                    print(f"[DBG-FIRE] Agent {agent_index} firing: bullets_before={before}")
                    # Compute candidate bullet_pos and check immediate collisions
                    try:
                        tk = current_state.getTankByIndex(agent_index)
                    except Exception:
                        tk = None
                    bullet_pos = None
                    if tk is not None:
                        try:
                            x, y = tk.getPos()
                            dirc = tk.getDirection()
                        except Exception:
                            x = getattr(tk, 'position', None)
                            dirc = getattr(tk, 'direction', None)
                        if dirc:
                            dx, dy = {'UP': (0, 1), 'DOWN': (0, -1), 'LEFT': (-1, 0), 'RIGHT': (1, 0)}.get(dirc, (0, 0))
                            bullet_pos = (x + dx, y + dy)
                    print(f"[DBG-FIRE] candidate bullet_pos={bullet_pos} dir={getattr(tk,'direction',None) if tk else None}")

                    # Inspect what's in that position now
                    if bullet_pos is not None:
                        bx, by = bullet_pos
                        # check walls
                        wall_at = None
                        for w in getattr(current_state, 'walls', []):
                            try:
                                if w.getPos() == bullet_pos and not w.isDestroyed():
                                    wall_at = w
                                    break
                            except Exception:
                                if getattr(w, 'position', None) == bullet_pos and not getattr(w, 'is_destroyed', False):
                                    wall_at = w
                                    break
                        if wall_at:
                            try:
                                print(f"[DBG-FIRE] wall at pos health_before={wall_at.getHealth()}")
                            except Exception:
                                print(f"[DBG-FIRE] wall at pos (unknown health API)")

                        # check tanks
                        tank_at = None
                        for other in [current_state.teamA_tank] + list(getattr(current_state, 'teamB_tanks', [])):
                            if other and other.isAlive() and other.getPos() == bullet_pos and other.getTeam() != (tk.getTeam() if tk else None):
                                tank_at = other
                                break
                        if tank_at:
                            try:
                                print(f"[DBG-FIRE] tank at pos team={tank_at.getTeam()} health_before={tank_at.getHealth()}")
                            except Exception:
                                print(f"[DBG-FIRE] tank at pos (unknown health API)")

                        # check base
                        base_at = getattr(current_state, 'base', None)
                        if base_at and not base_at.isDestroyed() and base_at.getPosition() == bullet_pos:
                            print(f"[DBG-FIRE] base at pos (exists) destroyed_before={base_at.isDestroyed()}")

                current_state.applyTankAction(agent_index, act)

                if act == 'FIRE' and verbose:
                    after = len(getattr(current_state, 'bullets', []))
                    print(f"[DBG-FIRE] Agent {agent_index} firing: bullets_after={after}")
                    if after > before:
                        new_bullets = current_state.bullets[before:after]
                        for b in new_bullets:
                            try:
                                pos = b.getPosition()
                            except Exception:
                                pos = getattr(b, 'position', None)
                            print(f"[DBG-FIRE] new bullet pos={pos} dir={getattr(b,'direction',None)} team={getattr(b,'team',None)}")
                    else:
                        # If no new bullet, check whether wall/tank/base took damage
                        try:
                            if bullet_pos is not None:
                                if wall_at:
                                    try:
                                        print(f"[DBG-FIRE] wall health_after={wall_at.getHealth()}")
                                    except Exception:
                                        pass
                                if tank_at:
                                    try:
                                        print(f"[DBG-FIRE] tank health_after={tank_at.getHealth()}")
                                        print(f"[DBG-FIRE] tank isAlive_after={tank_at.isAlive()}")
                                    except Exception:
                                        pass
                                if base_at:
                                    try:
                                        print(f"[DBG-FIRE] base destroyed_after={base_at.isDestroyed()}")
                                    except Exception:
                                        pass
                        except Exception:
                            pass
            except Exception as e:
                # si falla applyTankAction, imprimir traza cuando estamos en modo verbose
                if verbose:
                    print(f"[ERROR] applyTankAction raised: {e!r}")
                else:
                    # silencioso fuera de verbose
                    pass

            # Si era el último agente, avanzar balas y manejar muertes/respawns
            if agent_index == current_state.getNumAgents() - 1:
                try:
                    current_state.moveBullets()
                    current_state._handle_deaths_and_respawns()
                    current_state._check_collisions()
                except Exception:
                    pass

        # Avanzar "tick" de tiempo del juego (usar 1 unidad)
        try:
            current_state.current_time = getattr(current_state, 'current_time', 0) + 1
        except Exception:
            pass

        turn += 1

    wall_elapsed = time.time() - start_time_wall

    # Resumen
    result = {
        'turns': turn,
        'time_wall_s': wall_elapsed,
        'is_win': current_state.isWin(),
        'is_lose': current_state.isLose(),
        'is_timeout': current_state.isLimitTime(),
        'reserves_A': getattr(current_state, 'reserves_A', None),
        'reserves_B': getattr(current_state, 'reserves_B', None),
        'base_destroyed': getattr(current_state, 'base', None) is not None and current_state.base.isDestroyed(),
    }

    # Impresión final resumida
    print("\n=== Simulación Expectimax (nivel 1) ===")
    print(f"Depth(agent)={depth} | time_limit(agent)={time_limit_agent}s")
    print(f"Turns simulated: {result['turns']}")
    print(f"Wall clock time: {result['time_wall_s']:.3f}s")
    print(f"Win: {result['is_win']} | Lose: {result['is_lose']} | Timeout (game): {result['is_timeout']}")
    print(f"Reserves A: {result['reserves_A']} | Reserves B: {result['reserves_B']}")
    print(f"Base destroyed: {result['base_destroyed']}\n")

    return result


if __name__ == '__main__':
    run_simulation(time_limit_agent=5, depth=256, max_turns=100, verbose=False)
