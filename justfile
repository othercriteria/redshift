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

# Build the deliverable PDF via Pandoc. xelatex (rather than pdflatex)
# so unicode in code blocks doesn't blow up; --resource-path so figure
# references in the markdown resolve relative to doc/.
pdf:
    pandoc doc/redshift.md -o doc/redshift.pdf \
        --pdf-engine=xelatex \
        --resource-path=doc

# Full pipeline.
all: generate fit figures pdf

# Re-extract the chat transcript from the local Claude Code session log.
# Picks the largest .jsonl in this project's session dir.
transcript:
    #!/usr/bin/env bash
    set -euo pipefail
    session_dir="$HOME/.claude/projects/-home-dlk-workspace-redshift"
    latest=$(ls -S "$session_dir"/*.jsonl 2>/dev/null | head -1)
    if [ -z "$latest" ]; then
        echo "no session log found in $session_dir" >&2
        exit 1
    fi
    python scripts/extract_transcript.py --session "$latest"

# Drop generated outputs.
clean:
    rm -rf build/*
