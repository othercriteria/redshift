# redshift

Toy mathematical model exploring whether — and how — Doppler redshift
(peculiar motion) can be statistically separated from cosmological
redshift (metric expansion).

## Story

A single observed redshift `z_obs` mixes two physically distinct
contributions:

- a **cosmological** piece, deterministic in distance: `z_cos ≈ H₀ d / c`
- a **Doppler** piece, drawn from a peculiar-velocity distribution: `z_dop ≈ v / c`

Per object, these are perfectly degenerate. With an *independent
distance proxy* (a standard candle) and many objects, the regression
structure separates them: the slope of `z̄(d)` constrains `H₀`, the
scatter constrains `σ_v`.

This repo builds a small generative model in that low-redshift linear
regime, fits it with Stan, and ablates incrementally toward the
minimum that still makes the identifiability argument.

The deliverable is a Pandoc-built PDF, not a notebook. Interactive
parameter twiddling is intentionally low-priority.

## Dev environment

Enter the flake shell:

```bash
nix develop
```

Or, with `direnv`:

```bash
direnv allow
```

Then list available recipes:

```bash
just
```

## Layout

```
flake.nix          Nix-managed toolchain (Python, CmdStan, Pandoc, TeX, just)
justfile           Orchestration: generate → fit → figures → pandoc
src/               Python + Stan source
doc/               Markdown narrative + bibliography
build/             Generated figures, draws, and final PDF (gitignored)
```
