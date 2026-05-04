"""Extract a human-readable transcript from a Claude Code session log.

The Claude Code CLI persists each session as a JSONL file under
~/.claude/projects/{slug}/. Each line is one message or
metadata event. This script renders the user/assistant turns into
a readable markdown document, with:

- Real user messages under a "## User" heading.
- Assistant text replies under a "## Claude" heading.
- Internal thinking blocks shown verbatim in italic block quotes.
- Tool calls summarized as one-line "→ Tool: args" headers.
- Tool results shown verbatim in block quotes, truncated past
  TRUNCATE_TOOL_RESULT chars.

Tool-result-only "user" entries are attached to the preceding Claude
turn rather than emitting a spurious User heading.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")


def strip_ansi(s: str) -> str:
    return ANSI_ESCAPE_RE.sub("", s)

TRUNCATE_TOOL_RESULT = 4000  # chars in any single tool result before [...]

# Tools whose results contain content fetched from third-party sites.
# Their result bodies are redacted from the public transcript out of
# copyright caution; the request URL / query in the tool call itself
# is preserved so a reader can re-fetch.
REDACTED_TOOLS = {"WebSearch", "WebFetch"}


def block_quote(text: str, prefix: str = "") -> str:
    body = text.strip("\n")
    lines = body.split("\n") if body else [""]
    quoted = "\n".join(f"> {line}" if line else ">" for line in lines)
    if prefix:
        return f"> *{prefix}*\n>\n{quoted}"
    return quoted


def render_thinking(text: str) -> str | None:
    body = text.strip()
    if not body:
        # The Claude Code session log stores the thinking signature but
        # not the cleartext, so most thinking blocks come through empty.
        # Emit a placeholder rather than an empty quote.
        return "*[thinking block — content not retained in session log]*"
    return block_quote(body, prefix="thinking…")


def render_tool_use(block: dict) -> str:
    name = block.get("name", "?")
    inp = block.get("input", {}) or {}
    summary = {
        "Bash": lambda i: f"`{(i.get('command') or '').splitlines()[0][:240]}`",
        "Read": lambda i: f"`{i.get('file_path', '?')}`",
        "Edit": lambda i: f"`{i.get('file_path', '?')}`",
        "Write": lambda i: f"`{i.get('file_path', '?')}`",
        "Glob": lambda i: f"`{i.get('pattern', '?')}`",
        "Grep": lambda i: f"`{i.get('pattern', '?')}`",
        "WebSearch": lambda i: f"`{i.get('query', '?')}`",
        "WebFetch": lambda i: i.get("url", "?"),
        "TaskCreate": lambda i: i.get("subject", "?"),
        "TaskUpdate": lambda i: f"id={i.get('taskId')} → {i.get('status') or '(metadata)'}",
        "TaskGet": lambda i: f"id={i.get('taskId')}",
        "TaskList": lambda i: "(list)",
        "Skill": lambda i: f"`{i.get('skill', '?')}`",
        "ToolSearch": lambda i: f"`{i.get('query', '?')}`",
    }
    fmt = summary.get(name)
    arg_str = fmt(inp) if fmt else f"`{json.dumps(inp)[:240]}`"
    return f"**→ {name}:** {arg_str}"


def render_tool_result(block: dict, *, redact: bool = False) -> str:
    if redact:
        return block_quote(
            "[external content omitted from this public transcript out of "
            "copyright caution; see the source URL or query in the tool "
            "call above to re-fetch]",
            prefix="tool result (redacted)",
        )
    content = block.get("content", "")
    if isinstance(content, list):
        parts = []
        for c in content:
            if isinstance(c, dict) and c.get("type") == "text":
                parts.append(c.get("text", ""))
            elif isinstance(c, str):
                parts.append(c)
            elif isinstance(c, dict) and c.get("type") == "image":
                parts.append("[image]")
        content = "\n".join(parts)
    if not isinstance(content, str):
        content = str(content)
    body = strip_ansi(content).strip()
    if not body:
        return block_quote("(empty result)", prefix="tool result")
    if len(body) > TRUNCATE_TOOL_RESULT:
        elided = len(body) - TRUNCATE_TOOL_RESULT
        body = body[:TRUNCATE_TOOL_RESULT] + f"\n\n[… {elided} more chars truncated …]"
    return block_quote(body, prefix="tool result")


def render_assistant(content) -> list[str]:
    out = []
    for block in content:
        t = block.get("type")
        if t == "thinking":
            out.append(render_thinking(block.get("thinking", "")))
        elif t == "text":
            txt = block.get("text", "").strip()
            if txt:
                out.append(txt)
        elif t == "tool_use":
            out.append(render_tool_use(block))
    return out


def classify_user(content) -> str:
    if isinstance(content, str):
        return "real"
    if isinstance(content, list):
        types = {b.get("type") for b in content if isinstance(b, dict)}
        if types and types <= {"tool_result"}:
            return "tool_results"
    return "real"


def render_user(content, tool_name_by_id: dict[str, str]) -> list[str]:
    if isinstance(content, str):
        return [strip_ansi(content).strip()]
    parts = []
    for block in content:
        if not isinstance(block, dict):
            if isinstance(block, str):
                parts.append(strip_ansi(block).strip())
            continue
        t = block.get("type")
        if t == "text":
            parts.append(strip_ansi(block.get("text", "")).strip())
        elif t == "tool_result":
            tool_name = tool_name_by_id.get(block.get("tool_use_id"), "")
            redact = tool_name in REDACTED_TOOLS
            parts.append(render_tool_result(block, redact=redact))
    return [p for p in parts if p]


HEADER = """\
# Session transcript

A faithful record of the Claude Code session that produced this
repository, extracted from the local jsonl session log. Each
real user message is rendered under a `## User` heading; each
Claude response is rendered under a `## Claude` heading.

Within Claude turns:

- *Italicized block quotes labeled "thinking…"* are the model's
  internal reasoning blocks. They are not visible in the chat UI;
  they are included here verbatim.
- `**→ Tool:** args` lines summarize tool calls.
- *Block quotes labeled "tool result"* are the tool outputs that
  were fed back to Claude. Long results are truncated.

The very tail of this transcript is self-referential — it
discusses generating this very file. That section is mildly
weird by construction.
"""


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--session", type=Path, required=True,
                    help="Path to a Claude Code .jsonl session log.")
    ap.add_argument("--out", type=Path, default=Path("doc/transcript.md"))
    args = ap.parse_args()

    entries = [json.loads(line) for line in args.session.read_text().splitlines() if line]

    # First pass: tool_use_id → tool_name (so tool_result blocks know which
    # tool they correspond to and can be redacted selectively).
    tool_name_by_id: dict[str, str] = {}
    for entry in entries:
        if entry.get("type") == "assistant":
            for block in (entry.get("message", {}) or {}).get("content", []) or []:
                if isinstance(block, dict) and block.get("type") == "tool_use":
                    tool_name_by_id[block.get("id")] = block.get("name", "")

    chunks: list[str] = [HEADER]
    last_was_assistant = False
    for entry in entries:
        t = entry.get("type")
        if t == "user":
            msg = entry.get("message", {}) or {}
            content = msg.get("content")
            kind = classify_user(content)
            parts = render_user(content, tool_name_by_id)
            if not parts:
                continue
            if kind == "tool_results" and last_was_assistant:
                chunks.append("\n\n".join(parts))
            else:
                chunks.append("---\n\n## User")
                chunks.append("\n\n".join(parts))
                last_was_assistant = False
        elif t == "assistant":
            msg = entry.get("message", {}) or {}
            content = msg.get("content", []) or []
            parts = render_assistant(content)
            if not parts:
                continue
            if not last_was_assistant:
                chunks.append("---\n\n## Claude")
            chunks.append("\n\n".join(parts))
            last_was_assistant = True

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n\n".join(chunks) + "\n")
    print(f"wrote {args.out} ({args.out.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
