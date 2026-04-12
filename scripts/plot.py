"""Generate simple static SVG charts without external dependencies."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHARTS = ROOT / "docs" / "assets" / "charts"
FINDINGS = ROOT / "data" / "public" / "findings.json"

BG = "#0c0c0c"
FG = "#e0e0e0"
GRID = "#2a2a2a"
AMBER = "#ffcc66"
BLUE = "#66ccff"
RED = "#ff6666"


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


def text(x: int, y: int, value: str, *, size: int = 14, anchor: str = "start") -> str:
    return f'<text x="{x}" y="{y}" font-size="{size}" text-anchor="{anchor}">{value}</text>'


def bar_chart(path: Path, title: str, rows: list[tuple[str, float]], *, max_value: float = 1.0) -> None:
    width, height = 900, 520
    left, top, bar_h, gap = 230, 85, 44, 22
    plot_w = 560
    body = text(30, 42, title, size=22)
    for i in range(6):
        x = left + int(plot_w * i / 5)
        body += f'<line x1="{x}" y1="70" x2="{x}" y2="{height - 60}" stroke="{GRID}" stroke-dasharray="4 6"/>'
        body += text(x, height - 28, f"{i / 5:.1f}", size=12, anchor="middle")
    for idx, (label, value) in enumerate(rows):
        y = top + idx * (bar_h + gap)
        w = int(plot_w * value / max_value)
        color = AMBER if idx != 1 else BLUE
        body += text(30, y + 29, label)
        body += f'<rect x="{left}" y="{y}" width="{w}" height="{bar_h}" rx="3" fill="{color}"/>'
        body += text(left + w + 12, y + 29, f"{value:.2f}", size=13)
    path.write_text(svg_frame(width, height, body))


def grouped_chart(path: Path, title: str, data: dict[str, dict[str, float]], levels: list[str]) -> None:
    width, height = 980, 560
    left, top = 150, 90
    group_gap, bar_h, scale_w = 90, 18, 520
    body = text(30, 42, title, size=22)
    for i in range(6):
        x = left + int(scale_w * i / 5)
        body += f'<line x1="{x}" y1="70" x2="{x}" y2="{height - 65}" stroke="{GRID}" stroke-dasharray="4 6"/>'
        body += text(x, height - 30, f"{i / 5:.1f}", size=12, anchor="middle")
    colors = [AMBER, BLUE, "#b6e880", RED]
    for group_idx, (model, values) in enumerate(data.items()):
        base_y = top + group_idx * group_gap
        body += text(30, base_y + 35, model, size=12)
        for level_idx, level in enumerate(levels):
            value = float(values.get(level, 0.0))
            y = base_y + level_idx * (bar_h + 3)
            w = int(scale_w * value)
            body += f'<rect x="{left}" y="{y}" width="{w}" height="{bar_h}" rx="2" fill="{colors[level_idx % len(colors)]}"/>'
            body += text(left + w + 8, y + 14, f"{value:.2f}", size=11)
    legend_x = 710
    for i, level in enumerate(levels):
        y = 90 + i * 24
        body += f'<rect x="{legend_x}" y="{y - 14}" width="14" height="14" fill="{colors[i % len(colors)]}"/>'
        body += text(legend_x + 22, y, level.replace("_", " "), size=12)
    path.write_text(svg_frame(width, height, body))


def main() -> None:
    CHARTS.mkdir(parents=True, exist_ok=True)
    findings = load_findings()

    spec = findings["specificity"]["data"]["levels"]
    bar_chart(
        CHARTS / "specificity.svg",
        "Specificity gradient: average pass rate",
        [(level, float(spec.get(level, 0.0))) for level in ["vague", "task_only", "task_io", "full_spec"]],
    )

    comp = findings["complexity"]["data"]["models"]
    grouped_chart(
        CHARTS / "complexity.svg",
        "Complexity by model",
        comp,
        ["minimal", "role+constr", "examples", "maximal"],
    )

    context_budget = findings["context-budget"]["data"]["models"]
    grouped_chart(
        CHARTS / "context-budget.svg",
        "Context budget by model",
        context_budget,
        ["short_sparse", "long_sparse", "short_dense", "long_dense"],
    )

    filler = findings["filler"]["data"]["models"]
    grouped_chart(
        CHARTS / "filler.svg",
        "Compression sensitivity",
        filler,
        ["original", "compressed"],
    )
    print(f"wrote charts under {CHARTS.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
