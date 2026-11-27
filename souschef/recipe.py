"""Recipe format + validation.

A recipe is JSON:
{
  "name": "Simple Dal",
  "servings": 4,
  "slots": {"1": {"name": "oil"}, "4": {"name": "water", "liquid": true}},
  "steps": [
    {"action": "heat", "target_c": 170},
    {"action": "add",  "slot": 1, "grams": 20},
    {"action": "hold", "target_c": 160, "seconds": 300, "stir_rpm": 20},
    {"action": "stir", "rpm": 40, "seconds": 10},
    {"action": "wait", "seconds": 60},
    {"action": "done"}
  ]
}
"""
import json
from pathlib import Path

MAX_TEMP_C = 230
MAX_RPM = 80
NUM_SLOTS = 6

ACTION_FIELDS = {
    "heat": {"target_c"},
    "add": {"slot", "grams"},
    "hold": {"target_c", "seconds"},
    "stir": {"rpm", "seconds"},
    "wait": {"seconds"},
    "done": set(),
}


class RecipeError(ValueError):
    pass


def validate(recipe: dict) -> dict:
    """Check a recipe is safe and makes sense for this machine. Returns it normalised."""
    for key in ("name", "slots", "steps"):
        if key not in recipe:
            raise RecipeError(f"missing '{key}'")

    slots = {int(k): v for k, v in recipe["slots"].items()}
    for s in slots:
        if not 1 <= s <= NUM_SLOTS:
            raise RecipeError(f"slot {s} does not exist (machine has 1-{NUM_SLOTS})")
    recipe["slots"] = slots

    steps = recipe["steps"]
    if not steps or steps[-1].get("action") != "done":
        raise RecipeError("recipe must end with a 'done' step")

    for i, step in enumerate(steps, 1):
        action = step.get("action")
        if action not in ACTION_FIELDS:
            raise RecipeError(f"step {i}: unknown action '{action}'")
        missing = ACTION_FIELDS[action] - step.keys()
        if missing:
            raise RecipeError(f"step {i} ({action}): missing {sorted(missing)}")
        if "target_c" in step and not 0 < step["target_c"] <= MAX_TEMP_C:
            raise RecipeError(f"step {i}: target_c must be 1-{MAX_TEMP_C}")
        for rpm_key in ("rpm", "stir_rpm"):
            if rpm_key in step and not 0 <= step[rpm_key] <= MAX_RPM:
                raise RecipeError(f"step {i}: {rpm_key} must be 0-{MAX_RPM}")
        if action == "add":
            if step["slot"] not in slots:
                raise RecipeError(f"step {i}: slot {step['slot']} is not loaded")
            if step["grams"] <= 0:
                raise RecipeError(f"step {i}: grams must be > 0")
        if "seconds" in step and step["seconds"] <= 0:
            raise RecipeError(f"step {i}: seconds must be > 0")
    return recipe


def load(path: str | Path) -> dict:
    return validate(json.loads(Path(path).read_text()))
