"""Live Terminal Multi-Stage Progress Tracker & Elapsed Timer for BCA."""

import shutil
import sys
import threading
import time
from typing import Optional


class LiveProgressTracker:
    """
    Renders live animated spinner, active stage description, and elapsed timer
    in-place without line wrapping or cluttering terminal logs.
    """

    SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

    def __init__(self, prefix: str = ""):
        self.prefix = prefix
        self.current_stage = "Initializing..."
        self._start_time = time.perf_counter()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._is_tty = sys.stdout.isatty()

    def start(self, initial_stage: str = "Starting...") -> None:
        self.current_stage = initial_stage
        self._start_time = time.perf_counter()
        self._running = True

        if not self._is_tty:
            sys.stdout.write(f"{self.prefix} ... {self.current_stage}\n")
            sys.stdout.flush()
            return

        self._thread = threading.Thread(target=self._spin_loop, daemon=True)
        self._thread.start()

    def update_stage(self, stage_text: str) -> None:
        """Transitions to next stage (e.g. '🤖 Agent Coding', '🧪 Verifier', '🧐 Judge')."""
        self.current_stage = stage_text
        if not self._is_tty:
            sys.stdout.write(f"{self.prefix} -> {self.current_stage}\n")
            sys.stdout.flush()

    def _spin_loop(self) -> None:
        frame_idx = 0
        while self._running:
            try:
                term_cols = shutil.get_terminal_size((80, 24)).columns
            except Exception:
                term_cols = 80

            elapsed = time.perf_counter() - self._start_time
            spinner = self.SPINNER_FRAMES[frame_idx % len(self.SPINNER_FRAMES)]

            # Clean short line format to strictly prevent wrapping
            line = f"\r\x1b[2K{self.prefix} \x1b[36m{spinner}\x1b[0m [\x1b[33m{elapsed:4.1f}s\x1b[0m] {self.current_stage}"
            
            # Truncate if exceeds terminal width
            if len(line) > term_cols + 20: # +20 for invisible ANSI codes
                # Safe truncate
                line = line[:term_cols + 15] + "..."

            sys.stdout.write(line)
            sys.stdout.flush()
            frame_idx += 1
            time.sleep(0.12)

    def stop(self) -> None:
        """Stops the animated spinner and clears the line."""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=0.2)
        if self._is_tty:
            sys.stdout.write("\r\x1b[2K")
            sys.stdout.flush()
