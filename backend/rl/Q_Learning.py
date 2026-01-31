import numpy as np
import random

class Bandit:
    def __init__(self, arms, session_key, epsilon=0.1):
        self.arms = arms
        self.epsilon = epsilon
        self.session_key = session_key
        self.counts = {arm: 0 for arm in arms}
        self.values = {arm: 0.0 for arm in arms}

    def select_action(self):
        if np.random.random() < self.epsilon:
            return np.random.choice(self.arms)
        return max(self.values, key=self.values.get)

    def update(self, action, reward):
        self.counts[action] += 1
        n = self.counts[action]
        current_value = self.values[action]
        self.values[action] = current_value + (reward - current_value) / n

    def save_state(self, session):
        if 'bandit_states' not in session:
            session['bandit_states'] = {}
        session['bandit_states'][self.session_key] = {
            'counts': self.counts,
            'values': self.values
        }

    def load_state(self, session):
        if 'bandit_states' not in session or self.session_key not in session['bandit_states']:
            return
        state = session['bandit_states'][self.session_key]
        self.counts.update(state['counts'])
        self.values.update(state['values'])
    def get_arm_value(self, arm):
        """Lấy giá trị hiện tại của một arm"""
        if arm in self.arms:
            arm_index = self.arms.index(arm)
            return self.values[arm_index]
        return 0.0
    
    def get_all_arm_values(self):
        """Lấy tất cả giá trị của các arms"""
        return {arm: self.values[i] for i, arm in enumerate(self.arms)}
    
    def get_statistics(self):
        """Lấy thống kê của bandit"""
        return {
            "arms": self.arms,
            "values": self.values.tolist(),
            "counts": self.counts.tolist(),
            "total_actions": sum(self.counts),
            "epsilon": self.epsilon
        }

class QLearningAgent:
    def __init__(self, actions, alpha=0.1, gamma=0.9, epsilon=0.1):
        self.q_table = {}
        self.actions = actions
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon

    def get_q(self, state, action):
        return self.q_table.get((state, action), 0.0)

    def choose_action(self, state):
        if random.random() < self.epsilon:
            return random.choice(self.actions)
        qs = [self.get_q(state, a) for a in self.actions]
        max_q = max(qs)
        return self.actions[qs.index(max_q)]

    def update(self, state, action, reward, next_state):
        max_next_q = max([self.get_q(next_state, a) for a in self.actions])
        old_q = self.get_q(state, action)
        self.q_table[(state, action)] = old_q + self.alpha * (reward + self.gamma * max_next_q - old_q)