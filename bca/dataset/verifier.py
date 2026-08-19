"""Verification and automated grading engine for benchmark tasks."""

import time
from pathlib import Path
from typing import Optional

from bca.core.types import Verdict
from bca.core.trial import VerifierResult
from bca.sandbox.base import BaseSandbox, ProcessResult


class TaskVerifier:
    """
    Executes task verification scripts (e.g. verify.py, verify.sh, pytest)
    within the sandbox to empirically prove solution correctness.
    """

    def __init__(self, timeout_seconds: int = 60):
        self.timeout_seconds = timeout_seconds

    def verify(self, verifier_script: Path, sandbox: BaseSandbox) -> VerifierResult:
        """
        Runs the verification script against the current sandbox workspace state.
        """
        if not verifier_script.exists():
            return VerifierResult(
                verdict=Verdict.ERROR,
                exit_code=1,
                error_message=f"Verifier script not found: {verifier_script}",
            )

        start_time = time.perf_counter()

        # Copy verifier script into sandbox workspace temporarily if outside
        script_name = verifier_script.name
        temp_dest = sandbox.workspace_path / f".bca_{script_name}"

        try:
            temp_dest.write_bytes(verifier_script.read_bytes())

            if script_name.endswith(".py"):
                cmd = f"python3 .bca_{script_name}"
            elif script_name.endswith(".sh"):
                cmd = f"bash .bca_{script_name}"
            else:
                cmd = f"./.bca_{script_name}"

            proc_res: ProcessResult = sandbox.exec(
                cmd=cmd,
                timeout_seconds=self.timeout_seconds,
            )
            duration = time.perf_counter() - start_time

            if proc_res.timed_out:
                verdict = Verdict.TIMEOUT
            elif proc_res.exit_code == 0:
                verdict = Verdict.PASS
            else:
                verdict = Verdict.FAIL

            return VerifierResult(
                verdict=verdict,
                exit_code=proc_res.exit_code,
                stdout=proc_res.stdout,
                stderr=proc_res.stderr,
                duration_seconds=round(duration, 3),
                error_message=proc_res.stderr if verdict != Verdict.PASS else None,
            )

        finally:
            # Clean up the verifier script from workspace to avoid leaving artifacts
            if temp_dest.exists():
                temp_dest.unlink(missing_ok=True)
