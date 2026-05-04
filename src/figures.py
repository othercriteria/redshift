"""Render diagnostic figures from a saved Stan fit.

This is the iteration-and-sanity-check rig, not the final deliverable.
Outputs PNGs to build/figures/{tag}/ so they can be eyeballed quickly.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from cmdstanpy import from_csv

C_KMS = 299792.458

PARAMS = ["H0", "sigma_v", "sigma_obs"]
TRUTH_KEY = {"H0": "H0", "sigma_v": "sigma_v", "sigma_obs": "sigma_total"}


def hubble_line(z, H0, q0):
    d = C_KMS * z / H0
    d_L = d * (1 + 0.5 * (1 - q0) * z)
    return 5 * np.log10(d_L) + 25


def plot_hubble(catalog, draws, out_path):
    z = np.asarray(catalog["z_obs"])
    mu = np.asarray(catalog["mu_obs"])
    truth = catalog["truth"]

    fig, axes = plt.subplots(2, 1, figsize=(7, 6), sharex=True,
                             gridspec_kw={"height_ratios": [3, 1]})
    ax_main, ax_res = axes

    ax_main.scatter(z, mu, s=4, alpha=0.4, color="black", label="galaxies")

    z_grid = np.linspace(z.min() * 0.9, z.max() * 1.05, 300)
    H0_med = float(np.median(draws["H0"]))
    H0_lo, H0_hi = np.percentile(draws["H0"], [5, 95])
    q0 = truth["q0"]

    ax_main.plot(z_grid, hubble_line(z_grid, H0_med, q0),
                 color="C3", lw=1.5, label=f"posterior median H₀={H0_med:.2f}")
    ax_main.fill_between(z_grid,
                         hubble_line(z_grid, H0_hi, q0),
                         hubble_line(z_grid, H0_lo, q0),
                         color="C3", alpha=0.18, label="90% band on H₀")
    ax_main.plot(z_grid, hubble_line(z_grid, truth["H0"], q0),
                 color="C0", lw=1.0, ls="--", label=f"truth H₀={truth['H0']:.1f}")
    ax_main.set_ylabel("μ (distance modulus)")
    ax_main.legend(loc="lower right", fontsize=9)
    ax_main.set_title("Hubble diagram")

    res = mu - hubble_line(z, H0_med, q0)
    ax_res.scatter(z, res, s=4, alpha=0.4, color="black")
    ax_res.axhline(0, color="C3", lw=1)
    ax_res.set_xlabel("z_obs")
    ax_res.set_ylabel("μ residual")

    fig.tight_layout()
    fig.savefig(out_path, dpi=140)
    plt.close(fig)


def plot_corner(draws, truth, out_path):
    n = len(PARAMS)
    fig, axes = plt.subplots(n, n, figsize=(8, 8))
    for i, p1 in enumerate(PARAMS):
        for j, p2 in enumerate(PARAMS):
            ax = axes[i, j]
            if i < j:
                ax.set_visible(False)
                continue
            t1 = truth.get(TRUTH_KEY[p1])
            if i == j:
                ax.hist(draws[p1], bins=40, density=True,
                        color="steelblue", alpha=0.75)
                if t1 is not None:
                    ax.axvline(t1, color="C3", ls="--", lw=1.2)
                ax.set_yticks([])
            else:
                t2 = truth.get(TRUTH_KEY[p2])
                ax.scatter(draws[p2], draws[p1], s=1, alpha=0.25,
                           color="steelblue")
                if t1 is not None and t2 is not None:
                    ax.scatter([t2], [t1], marker="x", s=60,
                               color="C3", linewidths=1.5)
            if i == n - 1:
                ax.set_xlabel(p2)
            else:
                ax.set_xticklabels([])
            if j == 0 and i > 0:
                ax.set_ylabel(p1)
            elif j > 0:
                ax.set_yticklabels([])

    fig.suptitle("Joint posterior (red × = truth)")
    fig.tight_layout()
    fig.savefig(out_path, dpi=140)
    plt.close(fig)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--catalog", type=Path, default=Path("build/catalog.json"))
    ap.add_argument("--tag", default="complete")
    args = ap.parse_args()

    catalog = json.loads(args.catalog.read_text())
    fit_dir = Path("build/fits") / args.tag
    out_dir = Path("doc/figures") / args.tag
    out_dir.mkdir(parents=True, exist_ok=True)

    fit = from_csv(str(fit_dir))
    draws = fit.draws_pd(vars=PARAMS)

    plot_hubble(catalog, draws, out_dir / "hubble.png")
    plot_corner(draws, catalog["truth"], out_dir / "posterior.png")
    print(f"figures written to {out_dir}")


if __name__ == "__main__":
    main()
