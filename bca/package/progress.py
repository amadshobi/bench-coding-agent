"""Live Terminal Multi-Stage Progress Tracker & Elapsed Timer for BCA."""

import sys
import threading
import time
from typing import Optional


class LiveProgressTracker:
    """
    Renders live animated spinner, active stage description, and elapsed timer
    in-place without cluttering terminal logs.
    """

    SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

    def __init__(self, prefix: str = ""):
        self.prefix = prefix
        self.current_stage = "Initializing..."
        self._start_time = time.perf_counter()
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def start(self, initial_stage: str = "Starting...") -> None:
        self.current_stage = initial_stage
        self._start_time = time.perf_counter()
        self._running = True
        self._thread = threading.Thread(target=self._spin_loop, daemon=True)
        self._thread.start()

    def update_stage(self, stage_text: str) -> None:
        """Transitions to next stage (e.g. '🤖 Agent Coding', '🧪 Verifier', '🧐 Judge')."""
        self.current_stage = stage_text

    def _spin_loop(self) -> None:
        frame_idx = 0
        while self._running:
            elapsed = time.perf_counter() - self._start_time
            spinner = self.SPINNER_FRAMES[frame_idx % len(self.SPINNER_FRAMES)]
            # In-place terminal update: \r + clear line \x1b[2K
            sys.stdout.write(f"\r\x1b[2K{self.prefix} \x1b[36m{spinner}\x1b[0m [\x1b[33m{elapsed:4.1f}s\x1b[0m] {self.current_stage}")
            sys.stdout.flush()
            frame_idx += 1
            time.sleep(0.08)

    def stop(self) -> None:
        """Stops the animated spinner and clears the line."""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=0.2)
        sys.stdout.write("\r\x1b[2K")
        sys.stdout.flush()
