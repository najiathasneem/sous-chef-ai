import unittest
from pathlib import Path

from souschef import recipe as recipe_mod
from souschef.engine import CookingEngine, SafetyAbort
from souschef.simulator import build_sim_machine

ROOT = Path(__file__).resolve().parent.parent


def quiet(*_):
    pass


class EngineTests(unittest.TestCase):
    def test_dal_cooks_to_completion(self):
        r = recipe_mod.load(ROOT / "recipes" / "simple_dal.json")
        machine, pot = build_sim_machine(r["slots"])
        CookingEngine(machine, log=quiet).run(r)
        self.assertAlmostEqual(pot.food_g, 25 + 150 + 180 + 250 + 800, delta=10)
        self.assertEqual(pot.power, 0.0)
        self.assertEqual(pot.rpm, 0)

    def test_hold_keeps_temperature(self):
        r = recipe_mod.validate({"name": "t", "slots": {"1": {"name": "x"}}, "steps": [
            {"action": "heat", "target_c": 150},
            {"action": "hold", "target_c": 150, "seconds": 300},
            {"action": "done"}]})
        machine, pot = build_sim_machine(r["slots"])
        CookingEngine(machine, log=quiet).run(r)
        self.assertLess(abs(pot.temp_c - 150), 8)

    def test_sensor_failure_turns_everything_off(self):
        r = recipe_mod.validate({"name": "t", "slots": {}, "steps": [
            {"action": "heat", "target_c": 200}, {"action": "done"}]})
        machine, pot = build_sim_machine(r["slots"])
        pot.sensor_broken = True
        with self.assertRaises(SafetyAbort):
            CookingEngine(machine, log=quiet).run(r)
        self.assertEqual(pot.power, 0.0)

    def test_invalid_recipes_rejected(self):
        bad = [
            {"name": "x", "slots": {}, "steps": [{"action": "heat", "target_c": 500}, {"action": "done"}]},
            {"name": "x", "slots": {}, "steps": [{"action": "add", "slot": 1, "grams": 10}, {"action": "done"}]},
            {"name": "x", "slots": {}, "steps": [{"action": "fry"}]},
            {"name": "x", "slots": {}, "steps": [{"action": "heat", "target_c": 100}]},
        ]
        for r in bad:
            with self.assertRaises(recipe_mod.RecipeError):
                recipe_mod.validate(r)


if __name__ == "__main__":
    unittest.main()
