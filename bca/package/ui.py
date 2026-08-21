"""Modern ANSI Box-Drawing & Card UI Components for BCA CLI."""

import re
from typing import Any, Dict, List, Optional, Tuple

# Strip ANSI codes for accurate width calculations
ANSI_STRIP_RE = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")


def visual_len(text: str) -> int:
    """Calculates visible string length ignoring ANSI escape codes."""
    return len(ANSI_STRIP_RE.sub("", str(text)))


def pad_to(text: str, width: int, align: str = "left") -> str:
    """Pads string to visual terminal width preserving ANSI color codes."""
    vlen = visual_len(text)
    pad = max(0, width - vlen)
    if align == "right":
        return " " * pad + str(text)
    elif align == "center":
        left = pad // 2
        right = pad - left
        return " " * left + str(text) + " " * right
    return str(text) + " " * pad


class TerminalUI:
    """Renders modern boxed tables, status cards, and headers with zero dependencies."""

    @classmethod
    def render_table(
        cls,
        headers: List[str],
        rows: List[List[Any]],
        col_widths: Optional[List[int]] = None,
        alignments: Optional[List[str]] = None,
        title: Optional[str] = None,
    ) -> str:
        """
        Renders a full modern box table:
        ┌────────┬────────┬────────┐
        │ Header │ Header │ Header │
        ├────────┼────────┼────────┤
        │ Val    │ Val    │ Val    │
        └────────┴────────┴────────┘
        """
        num_cols = len(headers)
        if not alignments:
            alignments = ["left"] * num_cols

        # Auto calculate column widths
        widths: List[int] = []
        for i in range(num_cols):
            max_w = visual_len(headers[i])
            for r in rows:
                if i < len(r):
                    max_w = max(max_w, visual_len(r[i]))
            if col_widths and i < len(col_widths):
                widths.append(max(col_widths[i], max_w))
            else:
                widths.append(max_w + 2)

        lines: List[str] = []

        # Optional Title Header Box
        if title:
            total_inner = sum(widths) + (3 * (num_cols - 1)) + 2
            lines.append(f"\x1b[90m┌─\x1b[0m \x1b[1;33m{title}\x1b[0m \x1b[90m{'─' * max(5, total_inner - visual_len(title) - 4)}┐\x1b[0m")
        else:
            top_segments = ["─" * (w + 2) for w in widths]
            lines.append(f"\x1b[90m┌{'┬'.join(top_segments)}┐\x1b[0m")

        # Header Row
        header_cells = [
            f" \x1b[1;37m{pad_to(headers[i], widths[i], alignments[i])}\x1b[0m "
            for i in range(num_cols)
        ]
        lines.append(f"\x1b[90m│\x1b[0m{'│'.join(header_cells)}\x1b[90m│\x1b[0m")

        # Header Divider
        mid_segments = ["─" * (w + 2) for w in widths]
        lines.append(f"\x1b[90m├{'┼'.join(mid_segments)}┤\x1b[0m")

        # Data Rows
        for row in rows:
            cells = []
            for i in range(num_cols):
                val = row[i] if i < len(row) else ""
                align = alignments[i] if i < len(alignments) else "left"
                cells.append(f" {pad_to(str(val), widths[i], align)} ")
            lines.append(f"\x1b[90m│\x1b[0m{'│'.join(cells)}\x1b[90m│\x1b[0m")

        # Bottom Border
        bot_segments = ["─" * (w + 2) for w in widths]
        lines.append(f"\x1b[90m└{'┴'.join(bot_segments)}┘\x1b[0m")

        return "\n".join(lines)

    @classmethod
    def render_card(cls, title: str, items: List[Tuple[str, str]], width: int = 60) -> str:
        """
        Renders a clean info card:
        ┌─ Title ─────────────────────────┐
        │  • Label : Value                │
        └─────────────────────────────────┘
        """
        lines = []
        bar_len = max(5, width - visual_len(title) - 6)
        lines.append(f"\x1b[90m┌─\x1b[0m \x1b[1;36m{title}\x1b[0m \x1b[90m{'─' * bar_len}┐\x1b[0m")
        for k, v in items:
            content = f"  \x1b[90m•\x1b[0m \x1b[37m{k:<20}\x1b[0m : \x1b[1;33m{v}\x1b[0m"
            padded = pad_to(content, width - 2)
            lines.append(f"\x1b[90m│\x1b[0m{padded}\x1b[90m│\x1b[0m")
        lines.append(f"\x1b[90m└{'─' * (width - 2)}┘\x1b[0m")
        return "\n".join(lines)
