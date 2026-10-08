from dataclasses import dataclass, asdict

SCENARIOS = ("NORMAL_COMBAT", "LOW_HEALTH", "TARGET_LOST", "VISION_LOW_CONFIDENCE",
             "PLAYER_STUCK", "ACTION_TIMEOUT", "UNKNOWN_STATE", "MULTIPLE_TARGETS")
MAP_WIDTH, MAP_HEIGHT, CELL_SIZE = 20, 11, 32
OBSTACLES = {(7, y) for y in range(2, 8) if y != 7} | {(12, y) for y in range(3, 9) if y != 5} | {(4, 8), (5, 8), (16, 2), (17, 2)}


@dataclass
class World:
    scenario: str
    player_health: int = 82
    target_health: int = 73
    target_distance: float = 18.2
    target_visible: bool = True
    vision_confidence: float = .94
    player_stuck: bool = False
    action_timeout: bool = False
    unknown_state: bool = False
    targets: int = 1
    player_x: float = 92
    player_y: float = 180
    target_x: float = 535
    target_y: float = 180
    combat_state: str = "COMBAT"
    tick: int = 0
    facing: str = "E"
    idle_ticks: int = 0
    recovery_count: int = 0

    def snapshot(self) -> dict:
        state = asdict(self)
        state["map_width"] = MAP_WIDTH
        state["map_height"] = MAP_HEIGHT
        return state


def make_world(scenario: str) -> World:
    if scenario not in SCENARIOS:
        raise ValueError(f"Unknown scenario: {scenario}")
    w = World(scenario)
    if scenario == "LOW_HEALTH": w.player_health = 18
    if scenario == "TARGET_LOST": w.target_visible = False
    if scenario == "VISION_LOW_CONFIDENCE": w.vision_confidence = .31
    if scenario == "PLAYER_STUCK": w.player_stuck = True
    if scenario == "ACTION_TIMEOUT": w.action_timeout = True
    if scenario == "UNKNOWN_STATE": w.unknown_state = True; w.combat_state = "UNKNOWN"
    if scenario == "MULTIPLE_TARGETS": w.targets = 3
    return w
