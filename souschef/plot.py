"""Draw a graph of a simulated cook: temperature, heater power and stirring over time.

Needs: pip install matplotlib
"""


def plot_cook(pot, step_marks, title: str, out_path: str) -> None:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError as e:
        raise SystemExit("Install matplotlib first: pip install matplotlib") from e

    t = [h[0] / 60 for h in pot.history]          # minutes
    temp = [h[1] for h in pot.history]
    power = [h[2] * 100 for h in pot.history]     # percent
    rpm = [h[3] for h in pot.history]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 7), sharex=True,
                                   gridspec_kw={"height_ratios": [3, 1.2]})
    fig.suptitle(title, fontsize=14, fontweight="bold", x=0.06, ha="left")

    ax1.plot(t, temp, color="#D9480F", linewidth=2)
    ax1.set_ylabel("Pot temperature (°C)")
    ax1.grid(alpha=0.25)

    # mark when ingredients go in (that's where the temperature dips)
    adds = [(ts / 60, d.replace("add ", "+ ")) for ts, d in step_marks if d.startswith("add")]
    top = ax1.get_ylim()[1]
    last_x, shift = -99.0, 0
    for x, label in adds:
        ax1.axvline(x, color="#868E96", linestyle=":", linewidth=1)
        # push labels apart when two ingredients go in close together
        shift = shift + 11 if x - last_x < 1.5 else 0
        last_x = x
        ax1.annotate(label, xy=(x, top), xytext=(3 + shift, -4), textcoords="offset points",
                     rotation=90, va="top", fontsize=8, color="#495057")

    ax2.fill_between(t, power, step="post", color="#F59F00", alpha=0.35, label="Heater power (%)")
    ax2.plot(t, rpm, color="#1C7ED6", linewidth=1.5, drawstyle="steps-post", label="Stirrer (rpm)")
    ax2.set_xlabel("Time (minutes)")
    ax2.set_ylim(0, 105)
    ax2.legend(loc="upper right", fontsize=8, frameon=False)
    ax2.grid(alpha=0.25)

    for ax in (ax1, ax2):
        ax.spines[["top", "right"]].set_visible(False)

    fig.tight_layout()
    fig.savefig(out_path, dpi=130)
    plt.close(fig)
