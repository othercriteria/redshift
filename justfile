default:
    @just --list

# Sample synthetic galaxy catalog from the data-generating process.
generate:
    python src/generate.py

# Fit the Stan model to the generated catalog.
fit:
    python src/fit.py

# Render figures and tables from the posterior draws.
figures:
    python src/figures.py

# Build the deliverable PDF via Pandoc.
pdf:
    pandoc doc/redshift.md -o doc/redshift.pdf

# Full pipeline.
all: generate fit figures pdf

# Drop generated outputs.
clean:
    rm -rf build/*
