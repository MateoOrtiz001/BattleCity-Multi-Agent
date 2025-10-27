import time
import random
import math

class MCTSAgent:
    """Simple root-level MCTS agent using UCT for action selection.

    This implementation treats the root decision (for the provided tank index)
    and simulates all subsequent agent moves with a random rollout policy.
    It's intentionally simple: it keeps statistics only per-root-action.
    """
    def __init__(self, simulations=300, rollout_depth=40, time_limit=None, tankIndex=0):
        self.simulations = int(simulations)
        self.rollout_depth = int(rollout_depth)
        self.time_limit = time_limit  # seconds (optional). If set, overrides simulations.
        self.index = tankIndex
        self.expanded = 0

    def getAction(self, gameState):
        """Return an action for self.index given the current BattleCityGame state.

        We perform either a fixed number of simulations or run until time_limit
        is reached. For each simulation we: select a root action by UCT,
        then simulate random play until terminal or rollout_depth reached.
        We record rewards (based on evaluate_state from the final state)
        and pick the root action with highest average reward.
        """
        root_state = gameState
        legal_actions = root_state.getLegalActions(self.index)
        if not legal_actions:
            return 'STOP'
        # Quick-return for single move
        if len(legal_actions) == 1:
            return legal_actions[0]

        # Stats per action
        stats = {a: {'visits': 0, 'value': 0.0} for a in legal_actions}
        start_time = time.time()
        sims = 0
        num_tanks = len(root_state.teamA_tanks) + len(root_state.teamB_tanks)
        team = 'A' if self.index < len(root_state.teamA_tanks) else 'B'

        # UCT exploration constant
        C = math.sqrt(2)

        def select_action_ucb(total_sims):
            # choose action maximizing UCT value
            best = None
            best_val = float('-inf')
            for a, s in stats.items():
                if s['visits'] == 0:
                    # encourage trying unvisited actions
                    u = float('inf')
                else:
                    mean = s['value'] / s['visits']
                    u = mean + C * math.sqrt(math.log(total_sims) / s['visits'])
                if u > best_val:
                    best_val = u
                    best = a
            return best

        def rollout_from(state, current_tank):
            """Perform random rollout from given state; return final numeric reward
            from perspective of `team` (higher is better for the root agent).
            """
            s = state
            steps = 0
            while not s.is_terminal() and steps < self.rollout_depth:
                # get legal actions for current_tank
                acts = s.getLegalActions(current_tank)
                if not acts:
                    act = 'STOP'
                else:
                    act = random.choice(acts)
                s = s.generateSuccessor(current_tank, act)
                current_tank = (current_tank + 1) % num_tanks
                steps += 1
            # evaluate final state from root team perspective
            val = s.evaluate_state(s.getState(), team)
            return val

        # Run simulations
        while True:
            if self.time_limit is not None and (time.time() - start_time) >= self.time_limit:
                break
            if self.time_limit is None and sims >= self.simulations:
                break

            sims += 1
            # Selection: pick root action
            # If any action unvisited, pick one of them uniformly first
            unvisited = [a for a, s in stats.items() if s['visits'] == 0]
            if unvisited:
                action = random.choice(unvisited)
            else:
                action = select_action_ucb(max(1, sims))

            # Simulate: apply action at root index, then rollout
            succ = root_state.generateSuccessor(self.index, action)
            next_tank = (self.index + 1) % num_tanks
            reward = rollout_from(succ, next_tank)

            # Backpropagate to root action stats
            stats[action]['visits'] += 1
            stats[action]['value'] += reward

        # Choose action with best average value
        best_action = None
        best_avg = float('-inf')
        for a, s in stats.items():
            if s['visits'] == 0:
                avg = float('-inf')
            else:
                avg = s['value'] / s['visits']
            if avg > best_avg:
                best_avg = avg
                best_action = a

        # Fallback
        if best_action is None:
            best_action = random.choice(legal_actions)

        return best_action
