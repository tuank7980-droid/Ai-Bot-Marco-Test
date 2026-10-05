from .safety import SafetyGuard
from .navigation import cell_at, center_of, find_path, move_toward


class Agent:
    def __init__(self, recorder):
        self.recorder = recorder
        self.safety = SafetyGuard()
        self.steps = 0
        self.trace = []
        self.last = {}
        self.learned_stride = 20.0
        self.previous_distance = None

    def step(self, world, image_observation=None):
        self.steps += 1
        world.tick += 1
        # Coordinates originate from color-marker scanning of the dashboard canvas.
        obs = world.snapshot()
        if image_observation:
            obs["image_observation"] = image_observation
        self.recorder.emit("observation", **obs)
        detected = image_observation or {}
        player = detected.get("player")
        target = detected.get("target")
        blocked = {tuple(c) for c in detected.get("obstacles", []) if isinstance(c, list) and len(c) == 2}
        image_distance = None
        if player and target:
            image_distance = ((target[0] - player[0]) ** 2 + (target[1] - player[1]) ** 2) ** .5
        nodes = []
        if world.unknown_state:
            action, reason, outcome = "stop", "unknown_state_fail_closed", "SAFE_STOP"
            self.safety.stopped = True
        elif world.player_health <= 20:
            action, reason, outcome = "evade", "health_critical_recover", "SAFE_STOP"
            world.player_health = min(100, world.player_health + 8)
            nodes += [("Emergency", "SUCCESS"), ("Safety", "SUCCESS"), ("Recovery", "RUNNING")]
        elif not world.target_visible:
            action, reason, outcome = "observe", "target_lost_reobserve", "RECOVERED"
            world.target_visible = True
            world.vision_confidence = .81
            nodes += [("AcquireTarget", "FAILURE"), ("TargetLost", "SUCCESS"), ("Recovery", "SUCCESS")]
        elif world.vision_confidence < .6:
            action, reason, outcome = "observe", "low_confidence_reobserve", "RECOVERED"
            world.vision_confidence = .78
            nodes += [("VisionConfidence", "FAILURE"), ("Reobserve", "SUCCESS")]
        elif world.player_stuck:
            action, reason, outcome = "recover", "stuck_recovery", "RECOVERED"
            world.player_stuck = False
            world.recovery_count += 1
            world.idle_ticks = 0
            nodes += [("StuckDetector", "SUCCESS"), ("Recovery", "SUCCESS")]
        elif world.action_timeout:
            action, reason, outcome = "recover", "timeout_cancel_and_retry_once", "RECOVERED"
            world.action_timeout = False
            nodes += [("ActionTimeout", "SUCCESS"), ("Cancel", "SUCCESS"), ("Retry", "SUCCESS")]
        elif self.steps > 1 and world.target_health <= 0:
            action, reason, outcome = "wait", "target_defeat_verified", "SUCCESS"
            nodes += [("VerifyDefeat", "SUCCESS")]
        elif world.target_health > 0 and image_distance is not None and image_distance > 52:
            action, reason, outcome = "navigate", "astar_route_following", "RUNNING"
            old_distance = image_distance
            route = find_path(cell_at(tuple(player)), cell_at(tuple(target)), blocked,
                              world.snapshot().get("map_width", 20), world.snapshot().get("map_height", 11))
            self.planned_path = route
            if not route:
                action, reason, outcome = "stop", "no_safe_route_found", "SAFE_STOP"
                self.safety.stopped = True
            else:
                waypoint = center_of(route[1] if len(route) > 1 else route[0])
                old_player = tuple(player)
                world.player_x, world.player_y = move_toward(old_player, waypoint, min(32, self.learned_stride))
                dx, dy = world.player_x - old_player[0], world.player_y - old_player[1]
                world.facing = "E" if abs(dx) >= abs(dy) and dx >= 0 else "W" if abs(dx) >= abs(dy) else "S" if dy >= 0 else "N"
                if abs(dx) + abs(dy) < 1: world.idle_ticks += 1
                else: world.idle_ticks = 0
                if world.idle_ticks >= 2:
                    world.recovery_count += 1
                    world.idle_ticks = 0
                    world.player_x, world.player_y = move_toward(old_player, center_of(route[min(2, len(route)-1)]), 18)
                    action, reason, outcome = "recover", "no_progress_replan", "RECOVERED"
                nodes += [("ScanMap", "SUCCESS"), ("AStarPlanner", "SUCCESS"), ("FollowWaypoint", "RUNNING")]
            world.target_distance = max(2.5, old_distance / 18)
            if self.previous_distance is not None:
                reward = self.previous_distance - old_distance
                self.learned_stride = max(18.0, min(55.0, self.learned_stride + (2.0 if reward > 0 else -4.0)))
            self.previous_distance = old_distance
            nodes += [("AcquireTarget", "SUCCESS"), ("Position", "RUNNING")]
        elif world.target_health > 0 and image_distance is not None and image_distance <= 52:
            action, reason, outcome = "attack", "image_target_detected_in_range", "RUNNING"
            world.player_x, world.player_y = player
            nodes += [("AcquireTarget", "SUCCESS"), ("Position", "SUCCESS"), ("Attack", "RUNNING")]
        elif world.target_health <= 0 or (image_observation is not None and target is None):
            action, reason, outcome = "wait", "target_defeat_verified_from_frame", "SUCCESS"
            nodes += [("VerifyDefeat", "SUCCESS")]
        elif image_distance is None and image_observation is not None:
            action, reason, outcome = "observe", "markers_not_confident_reobserve", "RECOVERED"
            nodes += [("Perception", "FAILURE"), ("Reobserve", "SUCCESS")]
        else:
            action, reason, outcome = "attack", "target_visible_and_in_range", "RUNNING"
            nodes += [("AcquireTarget", "SUCCESS"), ("Position", "SUCCESS"), ("Attack", "RUNNING")]
        ok, safety_reason = self.safety.authorize(action, world)
        if not ok:
            action = "wait"
            reason = safety_reason
            outcome = "SAFE_STOP" if "stop" in safety_reason or "health" in safety_reason else outcome
        else:
            self.safety.record(action, world.tick)
            if action == "attack": world.target_health = max(0, world.target_health - 22)
        self.trace = nodes or [("Safety", "SUCCESS"), ("Decision", "RUNNING")]
        self.last = {"action": action, "reason": reason, "outcome": outcome, "world": world.snapshot(), "trace": self.trace}
        self.last["path"] = getattr(self, "planned_path", [])
        self.recorder.emit("decision", **self.last)
        if action == "attack":
            self.recorder.emit("action_verified", action=action, target_health=world.target_health)
            if world.target_health <= 0:
                self.last["outcome"] = outcome = "SUCCESS"
                self.trace = [("AcquireTarget", "SUCCESS"), ("Attack", "SUCCESS"), ("VerifyDefeat", "SUCCESS")]
                self.last["trace"] = self.trace
        terminal = outcome in ("SUCCESS", "SAFE_STOP")
        return {**self.last, "terminal": terminal}
