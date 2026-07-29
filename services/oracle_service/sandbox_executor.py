import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class SandboxResult:
    exit_code: int
    stdout: str
    stderr: str
    timed_out: bool

    @property
    def passed(self) -> bool:
        return not self.timed_out and self.exit_code == 0


class SandboxExecutor(Protocol):
    def run(self, *, script: str, timeout_seconds: float) -> SandboxResult: ...


class SubprocessSandboxExecutor:
    """Runs a submitted script in a plain subprocess with a hard timeout.

    THIS IS A LOCAL-DEVELOPMENT STAND-IN ONLY. It provides a timeout and nothing else —
    no container, no filesystem isolation, no network restriction — unlike the
    Docker/Firecracker microVM sandbox the Oracle Verification Service PRD calls for.
    Do not point this at untrusted agent submissions in any real deployment; swap in a
    container-based executor (e.g. running each submission in a locked-down Docker
    container with no network and a read-only filesystem) before this pipeline ever
    grades a real AI Automation & Product Building bounty."""

    def run(self, *, script: str, timeout_seconds: float = 10.0) -> SandboxResult:
        with tempfile.TemporaryDirectory() as tmp:
            script_path = Path(tmp) / "submission.py"
            script_path.write_text(script)
            try:
                result = subprocess.run(
                    ["python3", str(script_path)],
                    capture_output=True,
                    text=True,
                    timeout=timeout_seconds,
                )
            except subprocess.TimeoutExpired as exc:
                return SandboxResult(
                    exit_code=-1, stdout=exc.stdout or "", stderr=exc.stderr or "", timed_out=True
                )
            return SandboxResult(
                exit_code=result.returncode, stdout=result.stdout, stderr=result.stderr, timed_out=False
            )
