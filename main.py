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


def cook(r, plot_path=None):
    machine, pot = build_sim_machine(r["slots"])
    engine = CookingEngine(machine)
    try:
        engine.run(r)
    except SafetyAbort:
        sys.exit(1)
    finally:
        if plot_path:
            from souschef.plot import plot_cook
            plot_cook(pot, engine.step_marks, r["name"], plot_path)
            print(f"Graph saved to {plot_path}")


def cmd_run(args):
    cook(recipe_mod.load(args.recipe), args.plot)


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
        cook(r, args.plot)


def main():
    p = argparse.ArgumentParser(description="Sous-Chef AI simulator")
    sub = p.add_subparsers(required=True)

    run = sub.add_parser("run", help="cook a recipe JSON on the simulator")
    run.add_argument("recipe")
    run.add_argument("--plot", metavar="PNG", help="save a temperature graph, e.g. cook.png")
    run.set_defaults(func=cmd_run)

    ai = sub.add_parser("ai", help="ask Claude to write a recipe")
    ai.add_argument("request")
    ai.add_argument("--save")
    ai.add_argument("--cook", action="store_true", help="also cook it on the simulator")
    ai.add_argument("--plot", metavar="PNG", help="with --cook: save a temperature graph")
    ai.set_defaults(func=cmd_ai)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
