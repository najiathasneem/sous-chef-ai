"""Run Sous-Chef AI on the simulator.

    python main.py run recipes/simple_dal.json
    python main.py ai "chana masala for 4" --save recipes/chana.json
"""
import argparse
import json
import sys

from souschef import recipe as recipe_mod
from souschef.engine import CookingEngine, SafetyAbort
from souschef.simulator import build_sim_machine


def cmd_run(args):
    r = recipe_mod.load(args.recipe)
    machine, _ = build_sim_machine(r["slots"])
    try:
        CookingEngine(machine).run(r)
    except SafetyAbort:
        sys.exit(1)


def cmd_ai(args):
    from souschef.ai import generate_recipe
    r = generate_recipe(args.request)
    text = json.dumps({**r, "slots": {str(k): v for k, v in r["slots"].items()}}, indent=2)
    if args.save:
        with open(args.save, "w") as f:
            f.write(text)
        print(f"Saved to {args.save}")
    else:
        print(text)
    if args.cook:
        machine, _ = build_sim_machine(r["slots"])
        CookingEngine(machine).run(r)


def main():
    p = argparse.ArgumentParser(description="Sous-Chef AI simulator")
    sub = p.add_subparsers(required=True)

    run = sub.add_parser("run", help="cook a recipe JSON on the simulator")
    run.add_argument("recipe")
    run.set_defaults(func=cmd_run)

    ai = sub.add_parser("ai", help="ask Claude to write a recipe")
    ai.add_argument("request")
    ai.add_argument("--save")
    ai.add_argument("--cook", action="store_true", help="also cook it on the simulator")
    ai.set_defaults(func=cmd_ai)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
