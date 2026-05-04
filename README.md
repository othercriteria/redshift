# redshift

Toy mathematical model exploring whether — and how — Doppler redshift
(peculiar motion) can be statistically separated from cosmological
redshift (metric expansion).

The deliverable is **[`doc/redshift.pdf`](doc/redshift.pdf)**. A
verbatim chat transcript of the session that produced this repository
is at [`doc/transcript.md`](doc/transcript.md).

## Story

A single observed redshift `z_obs` mixes two physically distinct
contributions:

- a **cosmological** piece, deterministic in distance: `z_cos ≈ H₀ d / c`
- a **Doppler** piece, drawn from a peculiar-velocity distribution: `z_pec ≈ v / c`

For a single galaxy these are perfectly degenerate. With an
*independent distance proxy* (a standard candle) and many galaxies,
the regression structure separates them: the slope of the
distance/redshift relation constrains `H₀`, the scatter constrains
`σ_v`. This repo builds a small generative model in the low-redshift
linear regime, fits it with Stan, ablates incrementally toward the
minimum that still makes the identifiability argument, and finishes
with the no-distance-proxy case so the underlying degeneracy is
visible. The PDF is the place to read about all of that; the rest of
this README is just enough to reproduce.

## Authorship

This repository was produced collaboratively by Daniel Klein and
Claude Opus 4.7 (Anthropic), working via the Claude Code CLI over
several conversational sessions. The git history attributes Claude
as co-author on every commit; `doc/transcript.md` is the verbatim
record of the chat. See the "How this document was made" section in
the deliverable PDF for an explicit division of labor.

## Dev environment

Everything is pinned via Nix. Enter the dev shell:

```bash
nix develop      # or: direnv allow
just             # list recipes
```

The flake provides Python 3.14 (numpy, scipy, matplotlib, pandas,
cmdstanpy), CmdStan, Pandoc, TeXLive, just, git-lfs, and gh.

## Reproducing the deliverable

```bash
just generate                          # synthetic catalog → build/catalog.json
python src/fit.py --tag complete       # also: additive, no_q0, fixed_obs, no_mu
python src/figures.py --tag complete   # per-tag figures → doc/figures/{tag}/
python src/compare.py                  # cross-tag figures → doc/figures/compare/
just pdf                               # render doc/redshift.pdf
just transcript                        # regenerate doc/transcript.md
```

All fits in the deliverable use `seed=1` and `N=500` galaxies.
Default `H₀=70 km/s/Mpc`, `σ_v=300 km/s`, `σ_M=0.10 mag`,
`σ_meas=0.05 mag`, `q₀=−0.55`, `d ∈ [20, 400] Mpc` with volume prior.

## Layout

```
flake.nix                 Nix-pinned toolchain
justfile                  Pipeline recipes
src/
  generate.py             Generative process → build/catalog.json
  fit.py                  Stan fitting wrapper
  figures.py              Per-tag diagnostic figures
  compare.py              Cross-tag comparison figures
  models/
    complete.stan         Multiplicative + q0 + fitted σ_obs
    additive.stan         Additive redshift (safe ablation)
    no_q0.stan            Drop q0 (UNSAFE counter-example)
    fixed_obs.stan        Additive + σ_obs as data
    no_mu.stan            Drop μ likelihood (degeneracy demo)
scripts/
  extract_transcript.py   Claude Code session log → readable markdown
doc/
  redshift.md             Narrative source
  redshift.pdf            Rendered deliverable (LFS)
  transcript.md           Verbatim chat transcript
  figures/                Committed figures (LFS)
build/                    Ephemeral output (gitignored)
```
