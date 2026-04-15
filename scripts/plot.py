"""Generate simple static SVG charts without external dependencies."""

from __future__ import annotations

import json
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHARTS = ROOT / "docs" / "assets" / "charts"
FINDINGS = ROOT / "data" / "public" / "findings.json"

BG = "#0c0c0c"
FG = "#e0e0e0"
GRID = "#2a2a2a"
MUTED = "#9a9a9a"
AMBER = "#ffcc66"
BLUE = "#66ccff"
RED = "#ff6666"
GREEN = "#b6e880"


def load_findings() -> dict[str, dict]:
    if not FINDINGS.exists():
        import subprocess
        import sys

        subprocess.run([sys.executable, str(ROOT / "scripts" / "aggregate.py")], check=True)
    return {item["id"]: item for item in json.loads(FINDINGS.read_text())}


def svg_frame(width: int, height: int, body: str) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">'
        f'<rect width="100%" height="100%" fill="{BG}"/>'
        f'<g font-family="JetBrains Mono, Menlo, monospace" font-size="14" fill="{FG}">'
        f"{body}</g></svg>\n"
    )


def text(
    x: int,
    y: int,
    value: str,
    *,
    size: int = 14,
    anchor: str = "start",
    fill: str | None = None,
    opacity: float | None = None,
    weight: int | None = None,
) -> str:
    attrs = [f'x="{x}"', f'y="{y}"', f'font-size="{size}"', f'text-anchor="{anchor}"']
    if fill is not None:
        attrs.append(f'fill="{fill}"')
    if opacity is not None:
        attrs.append(f'opacity="{opacity}"')
    if weight is not None:
        attrs.append(f'font-weight="{weight}"')
    return f"<text {' '.join(attrs)}>{escape(value)}</text>"


def axis_label(x: int, y: int) -> str:
    return text(
        x,
        y,
        "Average pass rate (0 = no graded calls passed, 1 = all graded calls passed)",
        size=12,
        anchor="middle",
        fill=MUTED,
    )


def watermark(x: int, y: int, *, anchor: str = "end") -> str:
    return text(x, y, "Signal Depth", size=24, anchor=anchor, fill=FG, opacity=0.18, weight=700)


def subtitle_line(value: str) -> str:
    return text(30, 70, value, size=13, fill=MUTED)


def bar_chart(
    path: Path,
    title: str,
    subtitle: str,
    rows: list[tuple[str, float]],
    *,
    max_value: float = 1.0,
) -> None:
    width = 980
    left, top, bar_h, gap = 260, 120, 38, 20
    bottom = 95
    plot_w = 620
    plot_h = len(rows) * (bar_h + gap) - gap + 20
    height = top + plot_h + bottom
    body = text(30, 42, title, size=22, weight=700)
    body += subtitle_line(subtitle)
    for i in range(6):
        x = left + int(plot_w * i / 5)
        body += (
            f'<line x1="{x}" y1="{top - 20}" x2="{x}" y2="{top + plot_h}" '
            f'stroke="{GRID}" stroke-dasharray="4 6"/>'
        )
        body += text(x, height - 48, f"{i / 5:.1f}", size=12, anchor="middle")
    for idx, (label, value) in enumerate(rows):
        y = top + idx * (bar_h + gap)
        w = int(plot_w * value / max_value)
        color = [AMBER, BLUE, GREEN, RED][idx % 4]
        body += text(30, y + 29, label)
        body += f'<rect x="{left}" y="{y}" width="{w}" height="{bar_h}" rx="3" fill="{color}"/>'
        body += text(left + w + 12, y + 29, f"{value:.2f}", size=13)
    body += axis_label(left + plot_w // 2, height - 20)
    body += watermark(left + plot_w - 18, top + plot_h - 18)
    path.write_text(svg_frame(width, height, body))


def grouped_chart(
    path: Path,
    title: str,
    subtitle: str,
    data: dict[str, dict[str, float]],
    levels: list[str],
) -> None:
    width = 1080
    left, top = 280, 120
    label_h, bar_h, bar_gap, group_gap = 26, 18, 5, 30
    scale_w = 620
    group_h = label_h + len(levels) * bar_h + (len(levels) - 1) * bar_gap
    plot_h = len(data) * group_h + max(0, len(data) - 1) * group_gap
    bottom = 95
    height = top + plot_h + bottom
    body = text(30, 42, title, size=22, weight=700)
    body += subtitle_line(subtitle)
    for i in range(6):
        x = left + int(scale_w * i / 5)
        body += (
            f'<line x1="{x}" y1="{top - 20}" x2="{x}" y2="{top + plot_h}" '
            f'stroke="{GRID}" stroke-dasharray="4 6"/>'
        )
        body += text(x, height - 48, f"{i / 5:.1f}", size=12, anchor="middle")
    colors = [AMBER, BLUE, GREEN, RED]
    for group_idx, (model, values) in enumerate(data.items()):
        base_y = top + group_idx * (group_h + group_gap)
        body += text(30, base_y + 14, model, size=12)
        for level_idx, level in enumerate(levels):
            value = float(values.get(level, 0.0))
            y = base_y + label_h + level_idx * (bar_h + bar_gap)
            w = int(scale_w * value)
            color = colors[level_idx % len(colors)]
            body += (
                f'<rect x="{left}" y="{y}" width="{w}" height="{bar_h}" '
                f'rx="2" fill="{color}"/>'
            )
            body += text(left + w + 8, y + 14, f"{value:.2f}", size=11)
    legend_x = left + scale_w + 45
    for i, level in enumerate(levels):
        y = top + i * 24
        color = colors[i % len(colors)]
        body += (
            f'<rect x="{legend_x}" y="{y - 14}" width="14" height="14" '
            f'fill="{color}"/>'
        )
        body += text(legend_x + 22, y, level.replace("_", " "), size=12)
    body += axis_label(left + scale_w // 2, height - 20)
    body += watermark(left + scale_w - 18, top + plot_h - 18)
    path.write_text(svg_frame(width, height, body))


def main() -> None:
    CHARTS.mkdir(parents=True, exist_ok=True)
    findings = load_findings()

    spec = findings["specificity"]["data"]["levels"]
    bar_chart(
        CHARTS / "specificity.svg",
        "E9 specificity gradient",
        "Prompt levels on deterministic Python code tasks; higher means more graded calls passed.",
        [
            (level, float(spec.get(level, 0.0)))
            for level in ["vague", "task_only", "task_io", "full_spec"]
        ],
    )

    comp = findings["complexity"]["data"]["models"]
    grouped_chart(
        CHARTS / "complexity.svg",
        "E8 prompt complexity by model",
        "Average pass rate by prompt-detail level; higher means more generated code passed tests.",
        comp,
        ["minimal", "role+constr", "examples", "maximal"],
    )

    context_budget = findings["context-budget"]["data"]["models"]
    grouped_chart(
        CHARTS / "context-budget.svg",
        "E15 context budget by model",
        "Sparse vs dense task contract, short vs long prompt; pass rate ranges from 0 to 1.",
        context_budget,
        ["short_sparse", "long_sparse", "short_dense", "long_dense"],
    )

    filler = findings["filler"]["data"]["models"]
    grouped_chart(
        CHARTS / "filler.svg",
        "E4 compression sensitivity",
        "Average pass rate before and after prompt compression; only archived models shown.",
        filler,
        ["original", "compressed"],
    )
    print(f"wrote charts under {CHARTS.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
