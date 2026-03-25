"""LocalExecutor 功能測試。"""

import asyncio
import sys

import pytest

from src.local_executor import LocalExecutor


@pytest.fixture
def executor():
    return LocalExecutor()


@pytest.mark.asyncio
async def test_run_command_echo(executor):
    if sys.platform == "win32":
        result = await executor.run_command(["cmd", "/c", "echo", "hello"])
    else:
        result = await executor.run_command(["echo", "hello"])
    assert result.success
    assert "hello" in result.stdout


@pytest.mark.asyncio
async def test_run_command_failure(executor):
    if sys.platform == "win32":
        result = await executor.run_command(["cmd", "/c", "exit", "1"])
    else:
        result = await executor.run_command(["false"])
    assert not result.success


@pytest.mark.asyncio
async def test_run_command_on_output(executor):
    lines: list[str] = []
    if sys.platform == "win32":
        result = await executor.run_command(
            ["cmd", "/c", "echo", "line1"],
            on_output=lines.append,
        )
    else:
        result = await executor.run_command(
            ["echo", "line1"],
            on_output=lines.append,
        )
    assert result.success
    assert any("line1" in l for l in lines)


@pytest.mark.asyncio
async def test_run_command_timeout(executor):
    if sys.platform == "win32":
        result = await executor.run_command(
            ["cmd", "/c", "ping", "-n", "10", "127.0.0.1"],
            timeout=1,
        )
    else:
        result = await executor.run_command(["sleep", "10"], timeout=1)
    assert not result.success
    assert "[TIMEOUT]" in result.stderr


@pytest.mark.asyncio
async def test_read_write_file(executor, tmp_path):
    p = str(tmp_path / "test.txt")
    data = b"hello world"
    await executor.write_file(p, data)
    assert await executor.read_file(p) == data


@pytest.mark.asyncio
async def test_mkdir(executor, tmp_path):
    p = str(tmp_path / "a" / "b" / "c")
    await executor.mkdir(p)
    assert await executor.file_exists(p)


@pytest.mark.asyncio
async def test_copy_tree(executor, tmp_path):
    src = tmp_path / "src_dir"
    src.mkdir()
    (src / "file.txt").write_bytes(b"data")
    (src / "sub").mkdir()
    (src / "sub" / "nested.txt").write_bytes(b"nested")

    dst = str(tmp_path / "dst_dir")
    await executor.copy_tree(str(src), dst)

    assert await executor.file_exists(f"{dst}/file.txt")
    assert await executor.read_file(f"{dst}/sub/nested.txt") == b"nested"


@pytest.mark.asyncio
async def test_remove_tree(executor, tmp_path):
    d = tmp_path / "to_remove"
    d.mkdir()
    (d / "file.txt").write_bytes(b"x")

    await executor.remove_tree(str(d))
    assert not await executor.file_exists(str(d))


@pytest.mark.asyncio
async def test_list_dir(executor, tmp_path):
    (tmp_path / "a.txt").write_bytes(b"")
    (tmp_path / "b.txt").write_bytes(b"")
    (tmp_path / "c_dir").mkdir()

    entries = await executor.list_dir(str(tmp_path))
    assert "a.txt" in entries
    assert "b.txt" in entries
    assert "c_dir" in entries


@pytest.mark.asyncio
async def test_which_python(executor):
    result = await executor.which("python")
    # python or python3 should be findable
    if result is None:
        result = await executor.which("python3")
    assert result is not None


@pytest.mark.asyncio
async def test_which_nonexistent(executor):
    result = await executor.which("definitely_not_a_real_program_xyz")
    assert result is None


@pytest.mark.asyncio
async def test_file_exists(executor, tmp_path):
    f = tmp_path / "exists.txt"
    f.write_bytes(b"yes")
    assert await executor.file_exists(str(f)) is True
    assert await executor.file_exists(str(tmp_path / "nope.txt")) is False
