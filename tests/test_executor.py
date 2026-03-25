"""Executor Protocol 合規性測試。"""

from src.executor import CommandResult, Executor
from src.local_executor import LocalExecutor
from src.remote_executor import RemoteExecutor


def test_command_result_success():
    r = CommandResult(exit_code=0, stdout="ok", stderr="")
    assert r.success is True


def test_command_result_failure():
    r = CommandResult(exit_code=1, stdout="", stderr="fail")
    assert r.success is False


def test_command_result_frozen():
    r = CommandResult(exit_code=0, stdout="", stderr="")
    try:
        r.exit_code = 1  # type: ignore[misc]
        assert False, "Should be frozen"
    except AttributeError:
        pass


def test_local_executor_is_executor():
    assert isinstance(LocalExecutor(), Executor)


def test_remote_executor_is_executor():
    """RemoteExecutor 符合 Executor Protocol（結構型檢查，不需實際連線）。"""
    # runtime_checkable Protocol 只檢查方法存在性
    assert issubclass(RemoteExecutor, Executor)
