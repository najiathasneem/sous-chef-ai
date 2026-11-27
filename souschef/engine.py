"""The cooking engine: runs a recipe step by step on any Machine."""
from .hardware import Machine
from .pid import PID
from .recipe import MAX_TEMP_C

TICK_S = 1.0
HEAT_TIMEOUT_S = 20 * 60      # give up if a target temp isn't reached in 20 min
ADD_TIMEOUT_S = 60            # a hopper should never take a minute
OVERHEAT_MARGIN_C = 20        # abort if this far above the safety limit


class SafetyAbort(RuntimeError):
    pass


class CookingEngine:
    def __init__(self, machine: Machine, log=print):
        self.m = machine
        self.pid = PID()
        self.log = log
        self.step_marks: list[tuple[float, str]] = []   # (time_s, description) for graphs

    # ---------- public ----------
    def run(self, recipe: dict) -> None:
        self.log(f"Cooking: {recipe['name']}")
        try:
            for i, step in enumerate(recipe["steps"], 1):
                desc = self._describe(step, recipe)
                self.step_marks.append((self.m.clock.now(), desc))
                self.log(f"[{self._clock()}] step {i}: {desc}")
                getattr(self, f"_do_{step['action']}")(step)
            self.log(f"[{self._clock()}] Done! Food is ready.")
        except SafetyAbort as e:
            self.log(f"[{self._clock()}] SAFETY STOP: {e}")
            raise
        finally:
            self.m.all_off()

    # ---------- actions ----------
    def _do_heat(self, step):
        target = step["target_c"]
        self.pid.reset()
        start = self.m.clock.now()
        while self._read_temp() < target - 2:
            if self.m.clock.now() - start > HEAT_TIMEOUT_S:
                raise SafetyAbort(f"could not reach {target} C in time")
            self.m.heater.set_power(1.0)
            self.m.clock.sleep(TICK_S)

    def _do_hold(self, step):
        target, seconds = step["target_c"], step["seconds"]
        self.m.stirrer.set_rpm(step.get("stir_rpm", 0))
        self.pid.reset()
        end = self.m.clock.now() + seconds
        while self.m.clock.now() < end:
            power = self.pid.update(target, self._read_temp(), TICK_S)
            self.m.heater.set_power(power)
            self.m.clock.sleep(TICK_S)
        self.m.stirrer.set_rpm(0)

    def _do_add(self, step):
        slot, grams = step["slot"], step["grams"]
        goal = self.m.scale.read_grams() + grams
        start = self.m.clock.now()
        self.m.dispenser.open(slot)
        try:
            while self.m.scale.read_grams() < goal:
                if self.m.clock.now() - start > ADD_TIMEOUT_S:
                    raise SafetyAbort(f"slot {slot} seems empty or jammed")
                self._read_temp()           # keep watching the temperature
                self.m.clock.sleep(0.2)
        finally:
            self.m.dispenser.close(slot)

    def _do_stir(self, step):
        self.m.stirrer.set_rpm(step["rpm"])
        self._wait_watching(step["seconds"])
        self.m.stirrer.set_rpm(0)

    def _do_wait(self, step):
        self.m.heater.set_power(0.0)
        self._wait_watching(step["seconds"])

    def _do_done(self, step):
        self.m.all_off()

    # ---------- helpers ----------
    def _wait_watching(self, seconds):
        end = self.m.clock.now() + seconds
        while self.m.clock.now() < end:
            self._read_temp()
            self.m.clock.sleep(min(TICK_S, end - self.m.clock.now()))

    def _read_temp(self) -> float:
        t = self.m.temp.read_c()
        if t is None:
            raise SafetyAbort("temperature sensor not responding")
        if t > MAX_TEMP_C + OVERHEAT_MARGIN_C:
            raise SafetyAbort(f"overheating ({t:.0f} C)")
        return t

    def _clock(self) -> str:
        s = int(self.m.clock.now())
        return f"{s // 60:02d}:{s % 60:02d} {self.m.temp.read_c() or 0:5.1f}C"

    @staticmethod
    def _describe(step, recipe) -> str:
        a = step["action"]
        if a == "heat":
            return f"heat to {step['target_c']} C"
        if a == "add":
            name = recipe["slots"][step["slot"]].get("name", f"slot {step['slot']}")
            return f"add {step['grams']} g {name}"
        if a == "hold":
            return f"cook at {step['target_c']} C for {step['seconds']}s (stir {step.get('stir_rpm', 0)} rpm)"
        if a == "stir":
            return f"stir {step['rpm']} rpm for {step['seconds']}s"
        if a == "wait":
            return f"rest for {step['seconds']}s, heat off"
        return a
