"""Fit a Stan model to a generated catalog.

Each fit lives under build/fits/{tag}/. The tag is what figures.py uses
to compare models in the ablation table.
"""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from cmdstanpy import CmdStanModel


KEY_PARAMS = ["H0", "sigma_v", "sigma_obs"]
SUMMARY_COLS = ["Mean", "StdDev", "5%", "50%", "95%", "R_hat", "ESS_bulk"]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--catalog", type=Path, default=Path("build/catalog.json"))
    ap.add_argument("--model", type=Path, default=Path("src/models/complete.stan"))
    ap.add_argument("--tag", type=str, default="complete")
    ap.add_argument("--chains", type=int, default=8)
    ap.add_argument("--parallel-chains", type=int, default=8)
    ap.add_argument("--iter-warmup", type=int, default=1000)
    ap.add_argument("--iter-sampling", type=int, default=1000)
    ap.add_argument("--adapt-delta", type=float, default=0.95)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    catalog = json.loads(args.catalog.read_text())
    truth = catalog["truth"]
    data = {
        "N": catalog["n"],
        "z_obs": catalog["z_obs"],
        "mu_obs": catalog["mu_obs"],
        "d_min": truth["d_min"],
        "d_max": truth["d_max"],
        "q0": truth["q0"],
    }

    out_dir = Path("build/fits") / args.tag
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)

    model = CmdStanModel(stan_file=args.model)
    fit = model.sample(
        data=data,
        chains=args.chains,
        parallel_chains=args.parallel_chains,
        iter_warmup=args.iter_warmup,
        iter_sampling=args.iter_sampling,
        adapt_delta=args.adapt_delta,
        seed=args.seed,
        show_progress=False,
    )
    fit.save_csvfiles(str(out_dir))

    summary = fit.summary()
    # Stash the summary outside the cmdstan-CSV dir so cmdstanpy.from_csv
    # doesn't mistake it for chain output.
    summary_dir = Path("build/summaries")
    summary_dir.mkdir(parents=True, exist_ok=True)
    summary.to_csv(summary_dir / f"{args.tag}.csv")

    key = summary.loc[KEY_PARAMS, SUMMARY_COLS]
    print(key)
    print(
        f"\ntruth: H0={truth['H0']}, sigma_v={truth['sigma_v']}, "
        f"sigma_obs(=sqrt(sigma_M^2+sigma_meas^2))={truth['sigma_total']:.4f}"
    )

    diagnose = fit.diagnose()
    (summary_dir / f"{args.tag}.diagnose.txt").write_text(diagnose)


if __name__ == "__main__":
    main()
