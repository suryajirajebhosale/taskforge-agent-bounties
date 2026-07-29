from services.oracle_service.sandbox_executor import SubprocessSandboxExecutor


def test_successful_script_passes():
    executor = SubprocessSandboxExecutor()
    result = executor.run(script="print('ok')", timeout_seconds=5)
    assert result.passed
    assert "ok" in result.stdout
    assert result.exit_code == 0


def test_script_raising_an_exception_fails():
    executor = SubprocessSandboxExecutor()
    result = executor.run(script="raise ValueError('boom')", timeout_seconds=5)
    assert not result.passed
    assert result.exit_code != 0
    assert "boom" in result.stderr


def test_script_that_hangs_times_out():
    executor = SubprocessSandboxExecutor()
    result = executor.run(script="import time; time.sleep(5)", timeout_seconds=0.5)
    assert result.timed_out
    assert not result.passed


def test_explicit_nonzero_exit_fails():
    executor = SubprocessSandboxExecutor()
    result = executor.run(script="import sys; sys.exit(1)", timeout_seconds=5)
    assert not result.passed
    assert result.exit_code == 1
