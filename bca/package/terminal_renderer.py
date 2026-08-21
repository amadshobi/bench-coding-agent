"""Terminal Markdown and Git Diff Renderer inspired by ~/.shell/core/sub/src/renderer.ts."""

import re
from typing import List, Optional


def highlight_syntax_line(line: str) -> str:
    """Highlights syntax for code blocks (comments, strings, keywords, numbers)."""
    stripped = line.strip()
    if stripped.startswith("//") or stripped.startswith("#"):
        return f"\x1b[3;90m{line}\x1b[0m"

    code = line
    # Strings
    code = re.sub(r'(["\'])(?:(?=(\\?))\2[\s\S])*?\1', r"\x1b[32m\g<0>\x1b[0m", code)

    # Keywords
    keywords = r"\b(const|let|var|function|def|return|import|export|from|async|await|class|if|else|for|while|try|except|catch|new|type|interface|self)\b"
    code = re.sub(keywords, r"\x1b[1;35m\g<0>\x1b[0m", code)

    # Constants & numbers
    constants = r"\b(true|false|True|False|None|null|undefined|NaN|Infinity|\d+)\b"
    code = re.sub(constants, r"\x1b[36m\g<0>\x1b[0m", code)

    return code


class TerminalMarkdownFormatter:
    """Streams and formats Markdown text into modern ANSI terminal output."""

    def __init__(self) -> None:
        self.in_code_block = False
        self.current_lang = ""

    def format_line(self, line: str) -> str:
        # Code block fences (```)
        if line.strip().startswith("```"):
            self.in_code_block = not self.in_code_block
            self.current_lang = line.strip()[3:].strip()
            if self.in_code_block:
                lang = self.current_lang or "code"
                bar = "─" * max(10, 48 - len(lang))
                return f"\x1b[90m┌─\x1b[0m \x1b[1;33m󰈙 {lang}\x1b[0m \x1b[90m{bar}\x1b[0m"
            else:
                return f"\x1b[90m└{'─' * 52}\x1b[0m"

        if self.in_code_block:
            highlighted = highlight_syntax_line(line)
            return f"\x1b[90m│\x1b[0m {highlighted}"

        # Horizontal Rules (---, ***)
        if re.match(r"^(\*{3,}|-{3,}|_{3,})$", line.strip()):
            return f"\x1b[90m{'─' * 65}\x1b[0m"

        # Blockquotes (> quote)
        if line.startswith("> "):
            quote_text = line[2:]
            return f"\x1b[90m│\x1b[0m \x1b[3;90m{quote_text}\x1b[0m"

        # Tables (| col | col |)
        if line.strip().startswith("|") and line.strip().endswith("|"):
            if "---" in line:
                # Mid table separator line: ├──────┼──────┤
                parts = [p for p in line.strip().split("|")[1:-1]]
                segs = ["─" * len(p) for p in parts]
                return f"\x1b[90m├{'┼'.join(segs)}┤\x1b[0m"
            else:
                parts = line.strip().split("|")[1:-1]
                cells = [f" {p.strip()} " for p in parts]
                return f"\x1b[90m│\x1b[0m" + f"\x1b[90m│\x1b[0m".join(cells) + f"\x1b[90m│\x1b[0m"

        # Headers (# Header)
        h_match = re.match(r"^(#{1,6})\s+(.*)$", line)
        if h_match:
            level = len(h_match.group(1))
            text = h_match.group(2)
            if level == 1:
                return f"\n\x1b[1;33m# {text}\x1b[0m"
            elif level == 2:
                return f"\n\x1b[1;36m## {text}\x1b[0m"
            return f"\x1b[1;35m{h_match.group(1)} {text}\x1b[0m"

        # Numbered lists (1. , 2. )
        line = re.sub(r"^(\s*)(\d+)\.\s+", lambda m: f"{m.group(1)}\x1b[33m{m.group(2)}.\x1b[0m ", line)

        # Bullet points (- , * )
        line = re.sub(r"^(\s*)[-*]\s+", lambda m: f"{m.group(1)}\x1b[36m •\x1b[0m ", line)

        # Task list checkboxes
        line = line.replace("[ ]", "\x1b[90m[ ]\x1b[0m")
        line = line.replace("[x]", "\x1b[32m[✓]\x1b[0m").replace("[X]", "\x1b[32m[✓]\x1b[0m")

        # Links [text](url)
        line = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", lambda m: f"\x1b[4;36m{m.group(1)}\x1b[0m \x1b[90m({m.group(2)})\x1b[0m", line)

        # Bold **text**
        line = re.sub(r"\*\*([^*]+)\*\*", lambda m: f"\x1b[1m{m.group(1)}\x1b[0m", line)

        # Italic *text* or _text_
        line = re.sub(r"(\*|_)([^*_]+)\1", lambda m: f"\x1b[3m{m.group(2)}\x1b[0m", line)

        # Inline code `code`
        line = re.sub(r"`([^`]+)`", lambda m: f"\x1b[36m{m.group(1)}\x1b[0m", line)

        return line

    def render(self, raw_markdown: str) -> str:
        lines = raw_markdown.splitlines()
        formatted: List[str] = [self.format_line(l) for l in lines]
        return "\n".join(formatted)


def render_terminal_markdown(raw_markdown: str) -> str:
    formatter = TerminalMarkdownFormatter()
    return formatter.render(raw_markdown)


def render_git_diff_terminal(diff_raw: str) -> str:
    """Formats raw git diff into clean boxed terminal styling."""
    if not diff_raw.strip():
        return ""

    lines = diff_raw.splitlines()
    formatted: List[str] = []
    current_file = ""

    for line in lines:
        if line.startswith("diff --git"):
            match = re.search(r"b/(.+)$", line)
            current_file = match.group(1) if match else "file"
            bar = "─" * max(5, 42 - len(current_file))
            formatted.append(f"\x1b[90m┌─\x1b[0m \x1b[1;33m󰏫 Diff: {current_file}\x1b[0m \x1b[90m{bar}\x1b[0m")
            continue

        if line.startswith("---") or line.startswith("+++"):
            continue

        if line.startswith("@@"):
            formatted.append(f"\x1b[90m│\x1b[0m \x1b[36m{line}\x1b[0m")
            continue

        if line.startswith("+"):
            formatted.append(f"\x1b[90m│\x1b[0m \x1b[32m{line}\x1b[0m")
            continue

        if line.startswith("-"):
            formatted.append(f"\x1b[90m│\x1b[0m \x1b[31m{line}\x1b[0m")
            continue

        if line.startswith(" "):
            formatted.append(f"\x1b[90m│   {line[1:]}\x1b[0m")
            continue

    if formatted:
        formatted.append(f"\x1b[90m└{'─' * 52}\x1b[0m")

    return "\n".join(formatted)
