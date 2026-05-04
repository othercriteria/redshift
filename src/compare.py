"""Cross-model comparison figures.

Loads all listed fits, overlays their (H0, sigma_v) marginals and joints,
and writes PNGs to doc/figures/compare/. The narrative the figures
support:

  • The safe ablation chain (complete → additive → fixed_obs) leaves the
    posterior on (H0, sigma_v) qualitatively unchanged.
  • The drop-q0 counter-example pulls H0 several percent low — a
    cautionary tale about "small" approximations that absorb into the
    target parameter.
  • Removing the distance proxy (no_mu) widens the joint posterior
    sharply but does not fully degenerate it; the volume prior on d
    smuggles in spatial information.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from cmdstanpy import from_csv


SAFE_CHAIN = ["complete", "additive", "fixed_obs"]
COUNTER = "no_q0"
NO_DATA = "no_mu"
ALL_TAGS = SAFE_CHAIN + [COUNTER, NO_DATA]

# Wong 2011 colorblind-safe palette (Nature Methods 8, 441).
COLORS = {
    "complete":  "#0072B2",  # blue
    "additive":  "#009E73",  # bluish green
    "fixed_obs": "#CC79A7",  # reddish purple
    "no_q0":     "#D55E00",  # vermillion — warning
    "no_mu":     "#E69F00",  # orange
}

LABELS = {
    "complete": "complete",
    "additive": "additive",
    "fixed_obs": "additive + σ_obs fixed",
    "no_q0": "additive + drop q₀  (UNSAFE)",
    "no_mu": "no μ data",
}


def load_draws(tag: str) -> dict[str, np.ndarray]:
    fit = from_csv(str(Path("build/fits") / tag))
    df = fit.draws_pd(vars=["H0", "sigma_v"])
    return {"H0": df["H0"].to_numpy(), "sigma_v": df["sigma_v"].to_numpy()}


def kde_curve(samples: np.ndarray, grid: np.ndarray) -> np.ndarray:
    # Plain Gaussian KDE; fine for unimodal posteriors at this sample size.
    h = 1.06 * samples.std() * len(samples) ** (-1 / 5)
    z = (grid[:, None] - samples[None, :]) / h
    return np.exp(-0.5 * z**2).sum(axis=1) / (len(samples) * h * np.sqrt(2 * np.pi))


def plot_marginals(draws: dict[str, dict[str, np.ndarray]], truth: dict, tags, out_path):
    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    for ax, param, truth_val in zip(axes, ("H0", "sigma_v"), (truth["H0"], truth["sigma_v"])):
        all_x = np.concatenate([draws[t][param] for t in tags])
        lo, hi = np.percentile(all_x, [0.5, 99.5])
        grid = np.linspace(lo, hi, 400)
        for t in tags:
            ax.plot(grid, kde_curve(draws[t][param], grid),
                    color=COLORS[t], label=LABELS[t], lw=1.5)
        ax.axvline(truth_val, color="black", ls="--", lw=1, label=f"truth = {truth_val}")
        ax.set_xlabel(param)
        ax.set_ylabel("posterior density")
    axes[0].legend(loc="upper left", fontsize=9)
    fig.tight_layout()
    fig.savefig(out_path, dpi=140)
    plt.close(fig)


def plot_joint(draws: dict[str, dict[str, np.ndarray]], truth: dict, tags, out_path):
    fig, ax = plt.subplots(figsize=(7, 5.5))
    for t in tags:
        ax.scatter(draws[t]["H0"], draws[t]["sigma_v"], s=1.5, alpha=0.18,
                   color=COLORS[t], label=LABELS[t], rasterized=True)
    ax.scatter([truth["H0"]], [truth["sigma_v"]], marker="x", s=80,
               color="black", linewidths=2, label=f"truth = ({truth['H0']}, {truth['sigma_v']})")
    ax.set_xlabel("H₀ [km/s/Mpc]")
    ax.set_ylabel("σ_v [km/s]")
    ax.legend(loc="upper right", fontsize=9, framealpha=0.95)
    fig.tight_layout()
    fig.savefig(out_path, dpi=140)
    plt.close(fig)


def main() -> None:
    catalog = json.loads(Path("build/catalog.json").read_text())
    truth = catalog["truth"]
    out_dir = Path("doc/figures/compare")
    out_dir.mkdir(parents=True, exist_ok=True)

    draws = {t: load_draws(t) for t in ALL_TAGS}

    plot_marginals(draws, truth, SAFE_CHAIN + [NO_DATA],
                   out_dir / "marginals_safe.png")
    plot_marginals(draws, truth, ["additive", COUNTER],
                   out_dir / "marginals_counter.png")
    plot_joint(draws, truth, SAFE_CHAIN + [NO_DATA],
               out_dir / "joint_safe_vs_no_mu.png")

    print(f"comparison figures written to {out_dir}")


if __name__ == "__main__":
    main()
