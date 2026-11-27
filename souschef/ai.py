"""AI layer: turn a plain request ("dal for 4") into a machine recipe.

Uses Claude through the Anthropic API. Needs:
    pip install anthropic
    export ANTHROPIC_API_KEY=...
The generated recipe is always passed through recipe.validate() before
the machine is allowed to run it.
"""
import json
import os

from .recipe import validate, MAX_TEMP_C, MAX_RPM, NUM_SLOTS, __doc__ as FORMAT_DOC

MODEL = "claude-sonnet-5-5"

SYSTEM = f"""You write recipes for a one-pot cooking robot.
The machine has: an induction heater (max {MAX_TEMP_C} C), a stirrer (max {MAX_RPM} rpm),
{NUM_SLOTS} ingredient hoppers that pour pre-prepared (already chopped/soaked) ingredients,
and a scale. It cannot chop, flip, drain or taste.
Allowed actions: heat, add, hold, stir, wait, done.
Format:
{FORMAT_DOC}
Reply with ONLY the JSON recipe, no prose."""


def generate_recipe(request: str, retries: int = 2) -> dict:
    try:
        import anthropic
    except ImportError as e:
        raise SystemExit("Install the SDK first: pip install anthropic") from e
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise SystemExit("Set ANTHROPIC_API_KEY first")

    client = anthropic.Anthropic()
    messages = [{"role": "user", "content": request}]
    last_error = None
    for _ in range(retries + 1):
        reply = client.messages.create(model=MODEL, max_tokens=2000,
                                       system=SYSTEM, messages=messages)
        text = reply.content[0].text.strip().removeprefix("```json").removesuffix("```")
        try:
            return validate(json.loads(text))
        except (json.JSONDecodeError, ValueError) as e:
            last_error = e
            # tell the model what was wrong and let it fix it
            messages += [{"role": "assistant", "content": text},
                         {"role": "user", "content": f"That recipe is invalid: {e}. Fix it and reply with JSON only."}]
    raise ValueError(f"AI could not produce a valid recipe: {last_error}")
