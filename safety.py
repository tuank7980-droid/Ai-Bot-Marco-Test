class SafetyGuard:
    ALLOWED = {"observe", "approach", "attack", "evade", "recover", "stop", "wait"}

    def __init__(self):
        self.stopped = False
        self.last_action_tick = -2

    def authorize(self, action: str, world) -> tuple[bool, str]:
        if action not in self.ALLOWED: return False, "action_not_allowlisted"
        if self.stopped: return False, "emergency_stop_active"
        if world.player_health <= 20 and action == "attack": return False, "low_health_guard"
        if action == "attack" and world.tick - self.last_action_tick < 2: return False, "cooldown"
        return True, "authorized_in_simulation"

    def record(self, action: str, tick: int):
        if action == "attack": self.last_action_tick = tick
