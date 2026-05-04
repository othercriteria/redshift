"""Sample a synthetic galaxy catalog from the toy generative model.

Generative process (low-z linear regime, multiplicative combination):

    d_i        ~ Volume(d_min, d_max)        # p(d) ∝ d^2
    v_i        ~ Normal(0, sigma_v)          # peculiar radial velocity, km/s
    z_cos_i    = H0 * d_i / c
    z_dop_i    = v_i / c
    z_obs_i    = (1 + z_cos_i)(1 + z_dop_i) - 1
    d_L_i      = d_i * (1 + 0.5*(1 - q0)*z_cos_i)
    mu_true_i  = 5 log10(d_L_i / Mpc) + 25
    mu_obs_i   = mu_true_i + Normal(0, sqrt(sigma_M^2 + sigma_meas^2))

Intrinsic candle scatter (sigma_M) and measurement noise (sigma_meas) are
exposed as separate knobs in the DGP but are degenerate in the inference,
which uses a single sigma_obs.

Output: JSON at build/catalog.json (default), holding observed columns
plus the latent ground truth for diagnostics.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

C_KMS = 299792.458


def sample_volume_distance(rng: np.random.Generator, n: int, d_min: float, d_max: float) -> np.ndarray:
    u = rng.uniform(size=n)
    return np.cbrt(d_min**3 + u * (d_max**3 - d_min**3))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--n", type=int, default=500)
    ap.add_argument("--H0", type=float, default=70.0, help="km/s/Mpc")
    ap.add_argument("--sigma-v", type=float, default=300.0, help="km/s")
    ap.add_argument("--sigma-M", type=float, default=0.10, help="intrinsic candle scatter, mag")
    ap.add_argument("--sigma-meas", type=float, default=0.05, help="measurement scatter, mag")
    ap.add_argument("--d-min", type=float, default=20.0, help="Mpc")
    ap.add_argument("--d-max", type=float, default=400.0, help="Mpc")
    ap.add_argument("--q0", type=float, default=-0.55, help="deceleration parameter")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", type=Path, default=Path("build/catalog.json"))
    args = ap.parse_args()

    rng = np.random.default_rng(args.seed)

    d = sample_volume_distance(rng, args.n, args.d_min, args.d_max)
    v = rng.normal(0.0, args.sigma_v, size=args.n)
    z_cos = args.H0 * d / C_KMS
    z_dop = v / C_KMS
    z_obs = (1.0 + z_cos) * (1.0 + z_dop) - 1.0

    d_L = d * (1.0 + 0.5 * (1.0 - args.q0) * z_cos)
    mu_true = 5.0 * np.log10(d_L) + 25.0
    sigma_total = float(np.hypot(args.sigma_M, args.sigma_meas))
    mu_obs = mu_true + rng.normal(0.0, sigma_total, size=args.n)

    catalog = {
        "n": int(args.n),
        "z_obs": z_obs.tolist(),
        "mu_obs": mu_obs.tolist(),
        "truth": {
            "H0": args.H0,
            "sigma_v": args.sigma_v,
            "sigma_M": args.sigma_M,
            "sigma_meas": args.sigma_meas,
            "sigma_total": sigma_total,
            "q0": args.q0,
            "d_min": args.d_min,
            "d_max": args.d_max,
            "d": d.tolist(),
            "v": v.tolist(),
        },
        "seed": args.seed,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(catalog, indent=2))

    z_max = float(z_obs.max())
    print(f"wrote {args.n} galaxies to {args.out} (max z_obs = {z_max:.4f})")


if __name__ == "__main__":
    main()
