"""Generate per-finding social cards as SVG and PNG assets."""

from __future__ import annotations

import json
import subprocess
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FINDINGS_PATH = ROOT / "data" / "public" / "findings.json"
SOCIAL_DIR = ROOT / "docs" / "assets" / "social"

CARD_W = 1200
CARD_H = 630
PANEL_X = 36
PANEL_Y = 32
PANEL_W = 1128
PANEL_H = 566
LEFT_X = 72
RIGHT_X = 700
BG = "#090909"
PANEL_STROKE = "#262626"
PANEL_FILL_A = "#151515"
PANEL_FILL_B = "#0b0b0b"
TEXT = "#f4f4f4"
MUTED = "#c7c7c7"
FAINT = "#a0a0a0"
GRID = "#242424"
AMBER = "#ffcc66"
BLUE = "#66ccff"
GREEN = "#b6e880"
RED = "#ff6666"
BAR_COLORS = [AMBER, BLUE, GREEN, RED]


def load_findings() -> dict[str, dict]:
    items = json.loads(FINDINGS_PATH.read_text())
    return {item["id"]: item for item in items}


def wrap_text(text: str, width: int) -> list[str]:
    words = text.split()
    if not words:
        return [""]
    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        candidate = current + " " + word
        if len(candidate) <= width:
            current = candidate
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def svg_text(
    x: int,
    y: int,
    value: str,
    *,
    size: int,
    fill: str,
    weight: int | None = None,
    family: str = "Inter, Arial, sans-serif",
    anchor: str = "start",
) -> str:
    attrs = [
        f'x="{x}"',
        f'y="{y}"',
        f'fill="{fill}"',
        f'font-family="{family}"',
        f'font-size="{size}"',
        f'text-anchor="{anchor}"',
    ]
    if weight is not None:
        attrs.append(f'font-weight="{weight}"')
    return f"<text {' '.join(attrs)}>{escape(value)}</text>"


def gradient_defs() -> str:
    return (
        "<defs>"
        '<linearGradient id="panel" x1="0" y1="0" x2="1" y2="1">'
        f'<stop offset="0%" stop-color="{PANEL_FILL_A}"/>'
        f'<stop offset="100%" stop-color="{PANEL_FILL_B}"/>'
        "</linearGradient>"
        "</defs>"
    )


def render_bars(title: str, items: list[tuple[str, float]]) -> str:
    parts = [svg_text(RIGHT_X, 106, title, size=24, fill=MUTED, weight=600)]
    chart_x = RIGHT_X
    chart_y = 160
    chart_w = 380
    chart_h = 320
    for tick, label in enumerate(["1.0", "0.75", "0.50", "0.25", "0.0"]):
        y = chart_y + tick * 80
        parts.append(
            f'<line x1="{chart_x}" y1="{y}" x2="{chart_x + chart_w}" y2="{y}" stroke="{GRID}"/>'
        )
        parts.append(
            svg_text(
                chart_x - 8,
                y + 6,
                label,
                size=16,
                fill="#8f8f8f",
                family="JetBrains Mono, Menlo, monospace",
                anchor="end",
            )
        )
    parts.append(
        f'<line x1="{chart_x}" y1="{chart_y}" x2="{chart_x}" '
        f'y2="{chart_y + chart_h}" stroke="#333333"/>'
    )
    parts.append(
        f'<line x1="{chart_x}" y1="{chart_y + chart_h}" x2="{chart_x + chart_w}" '
        f'y2="{chart_y + chart_h}" stroke="#333333"/>'
    )

    bar_w = 62 if len(items) <= 4 else 48
    gap = 28 if len(items) <= 4 else 16
    total_w = len(items) * bar_w + (len(items) - 1) * gap
    start_x = chart_x + max(20, (chart_w - total_w) // 2)
    for idx, (label, value) in enumerate(items):
        x = start_x + idx * (bar_w + gap)
        height = int(chart_h * value)
        y = chart_y + chart_h - height
        color = BAR_COLORS[idx % len(BAR_COLORS)]
        parts.append(
            f'<rect x="{x}" y="{y}" width="{bar_w}" height="{height}" rx="4" fill="{color}"/>'
        )
        parts.append(
            svg_text(
                x + bar_w // 2,
                y - 12,
                f"{value:.2f}",
                size=18,
                fill=TEXT,
                family="JetBrains Mono, Menlo, monospace",
                anchor="middle",
            )
        )
        label_lines = label.split("\n")
        for line_idx, line in enumerate(label_lines):
            parts.append(
                svg_text(
                    x + bar_w // 2,
                    chart_y + chart_h + 32 + line_idx * 20,
                    line,
                    size=16,
                    fill="#d7d7d7",
                    family="JetBrains Mono, Menlo, monospace",
                    anchor="middle",
                )
            )
    return "".join(parts)


def render_badge(title: str, value: str, subtitle: str) -> str:
    parts = [svg_text(RIGHT_X, 106, title, size=24, fill=MUTED, weight=600)]
    parts.append(
        f'<rect x="{RIGHT_X}" y="170" width="360" height="220" rx="12" '
        'fill="#111111" stroke="#2b2b2b"/>'
    )
    parts.append(
        svg_text(
            RIGHT_X + 180,
            270,
            value,
            size=72,
            fill=AMBER,
            weight=800,
            anchor="middle",
        )
    )
    for idx, line in enumerate(wrap_text(subtitle, 24)):
        parts.append(
            svg_text(
                RIGHT_X + 180,
                330 + idx * 28,
                line,
                size=24,
                fill=MUTED,
                anchor="middle",
            )
        )
    return "".join(parts)


def render_table(rows: list[tuple[str, str]]) -> str:
    y0 = 420
    parts = [
        svg_text(
            LEFT_X,
            y0,
            "Key metric",
            size=20,
            fill=FAINT,
            family="JetBrains Mono, Menlo, monospace",
        ),
        svg_text(
            LEFT_X + 250,
            y0,
            "Value",
            size=20,
            fill=FAINT,
            family="JetBrains Mono, Menlo, monospace",
        ),
    ]
    for idx, (label, value) in enumerate(rows):
        y = y0 + 38 + idx * 42
        parts.append(
            svg_text(
                LEFT_X,
                y,
                label,
                size=28,
                fill=TEXT,
                family="JetBrains Mono, Menlo, monospace",
            )
        )
        parts.append(
            svg_text(
                LEFT_X + 250,
                y,
                value,
                size=28,
                fill=TEXT,
                family="JetBrains Mono, Menlo, monospace",
            )
        )
    return "".join(parts)


def render_card(
    slug: str,
    title: str,
    subtitle: str,
    scope: str,
    rows: list[tuple[str, str]],
    *,
    chart_title: str,
    chart_items: list[tuple[str, float]] | None = None,
    badge_value: str | None = None,
    badge_subtitle: str | None = None,
) -> None:
    title_lines = wrap_text(title, 26)
    subtitle_lines = wrap_text(subtitle, 28)
    scope_lines = wrap_text(scope, 40) if scope else []
    body: list[str] = [
        gradient_defs(),
        f'<rect width="{CARD_W}" height="{CARD_H}" fill="{BG}"/>',
        (
            f'<rect x="{PANEL_X}" y="{PANEL_Y}" width="{PANEL_W}" height="{PANEL_H}" rx="12" '
            f'fill="url(#panel)" stroke="{PANEL_STROKE}"/>'
        ),
        svg_text(LEFT_X, 88, "Signal Depth", size=22, fill=AMBER, weight=700),
    ]

    y = 156
    for line in title_lines:
        body.append(svg_text(LEFT_X, y, line, size=58, fill=TEXT, weight=800))
        y += 64
    y += 8
    for line in subtitle_lines:
        body.append(svg_text(LEFT_X, y, line, size=34, fill=AMBER, weight=700))
        y += 40
    if scope_lines:
        y += 16
        for line in scope_lines:
            body.append(svg_text(LEFT_X, y, line, size=22, fill=MUTED))
            y += 28

    body.append(render_table(rows))

    if chart_items is not None:
        body.append(render_bars(chart_title, chart_items))
    else:
        body.append(render_badge(chart_title, badge_value or "", badge_subtitle or ""))

    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{CARD_W}" height="{CARD_H}" '
        f'viewBox="0 0 {CARD_W} {CARD_H}" role="img" aria-label="{escape(title)}">'
        + "".join(body)
        + "</svg>\n"
    )

    svg_path = SOCIAL_DIR / f"{slug}.svg"
    png_path = SOCIAL_DIR / f"{slug}.png"
    svg_path.write_text(svg)
    subprocess.run(
        [
            "rsvg-convert",
            "-w",
            str(CARD_W),
            "-h",
            str(CARD_H),
            str(svg_path),
            "-o",
            str(png_path),
        ],
        check=True,
    )


def main() -> None:
    SOCIAL_DIR.mkdir(parents=True, exist_ok=True)
    findings = load_findings()

    spec = findings["specificity"]["data"]["levels"]
    render_card(
        "home-card",
        "Making prompts longer did not help.",
        "Explicit task contracts did.",
        "Deterministic Python code tasks, 4 local-model runs, k=3, temperature 0.0",
        [
            ("short_sparse", "0.25"),
            ("long_sparse", "0.25"),
            ("short_dense", "1.00"),
            ("long_dense", "1.00"),
        ],
        chart_title="E15 context-budget result",
        chart_items=[
            ("short\nsparse", 0.25),
            ("long\nsparse", 0.25),
            ("short\ndense", 1.0),
            ("long\ndense", 1.0),
        ],
    )
    render_card(
        "context-budget-card",
        "Making prompts longer did not help.",
        "Explicit task contracts did.",
        "Deterministic Python code tasks, 4 local-model runs, k=3, temperature 0.0",
        [
            ("short_sparse", "0.25"),
            ("long_sparse", "0.25"),
            ("short_dense", "1.00"),
            ("long_dense", "1.00"),
        ],
        chart_title="E15 context-budget result",
        chart_items=[
            ("short\nsparse", 0.25),
            ("long\nsparse", 0.25),
            ("short\ndense", 1.0),
            ("long\ndense", 1.0),
        ],
    )
    render_card(
        "specificity-card",
        "Specificity dwarfs everything.",
        "Vague to task + I/O spec caused the biggest jump.",
        "",
        [
            ("vague", f'{spec["vague"]:.2f}'),
            ("task_only", f'{spec["task_only"]:.2f}'),
            ("task_io", f'{spec["task_io"]:.2f}'),
            ("full_spec", f'{spec["full_spec"]:.2f}'),
        ],
        chart_title="E9 specificity gradient",
        chart_items=[
            ("vague", float(spec["vague"])),
            ("task\nonly", float(spec["task_only"])),
            ("task\nio", float(spec["task_io"])),
            ("full\nspec", float(spec["full_spec"])),
        ],
    )

    comp = findings["complexity"]["data"]["models"]["qwen2.5-coder:1.5b"]
    render_card(
        "complexity-card",
        "Complexity hurts small models.",
        "The smallest coder model dropped sharply at maximal prompt complexity.",
        "Archived E8 run, deterministic coding tasks, 96 graded calls",
        [
            ("minimal", f'{comp["minimal"]:.2f}'),
            ("role+constr", f'{comp["role+constr"]:.2f}'),
            ("examples", f'{comp["examples"]:.2f}'),
            ("maximal", f'{comp["maximal"]:.2f}'),
        ],
        chart_title="qwen2.5-coder:1.5b",
        chart_items=[
            ("minimal", float(comp["minimal"])),
            ("role+\nconstr", float(comp["role+constr"])),
            ("examples", float(comp["examples"])),
            ("maximal", float(comp["maximal"])),
        ],
    )

    filler = findings["filler"]["data"]["models"]["qwen2.5-coder:1.5b"]
    render_card(
        "filler-card",
        "Filler words are load-bearing.",
        "Compression cut qwen2.5-coder:1.5b from 0.89 to 0.28.",
        "Archived E4 run, deterministic coding tasks, summary-first release",
        [
            ("original", f'{filler["original"]:.2f}'),
            ("compressed", f'{filler["compressed"]:.2f}'),
            ("delta", f'{filler["compressed"] - filler["original"]:+.2f}'),
        ],
        chart_title="qwen2.5-coder:1.5b",
        chart_items=[
            ("original", float(filler["original"])),
            ("compressed", float(filler["compressed"])),
        ],
    )

    fmt = findings["format"]["data"]["overall"]
    render_card(
        "format-card",
        "Format preference is noise.",
        "XML, Markdown, and plain text were indistinguishable in delimiter-only tests.",
        "Archived E7 run, 4 local models, 96 graded calls",
        [
            ("xml", f'{fmt["xml"]:.2f}'),
            ("markdown", f'{fmt["markdown"]:.2f}'),
            ("plain", f'{fmt["plain"]:.2f}'),
        ],
        chart_title="Delimiter-only format test",
        chart_items=[
            ("xml", float(fmt["xml"])),
            ("markdown", float(fmt["markdown"])),
            ("plain", float(fmt["plain"])),
        ],
    )

    render_card(
        "k1-trap-card",
        "k=1 is a methodological trap.",
        "Boundary models can flip conclusions at k=1.",
        "",
        [
            ("k=1", "unstable"),
            ("k>=3", "required"),
        ],
        chart_title="Sampling rule",
        badge_value="k >= 3",
        badge_subtitle="default for new contributions",
    )

    render_card(
        "demorgan-card",
        "DeMorgan inversion on llama3.1:8b.",
        "One task_io phrasing triggered a deterministic logic inversion on fizzbuzz.",
        "Single-model, single-task counterexample, k=3 per level",
        [
            ("task_only", "1.00"),
            ("task_io", "0.33"),
            ("full_spec", "1.00"),
        ],
        chart_title="llama3.1:8b on fizzbuzz",
        chart_items=[
            ("task\nonly", 1.0),
            ("task\nio", 0.33),
            ("full\nspec", 1.0),
        ],
    )

    print(f"wrote social cards under {SOCIAL_DIR.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
