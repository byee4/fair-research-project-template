import json
import subprocess
import sys

import pytest
from conftest import ROOT

GUARD = ROOT / ".agent/hooks/pre_tool_guard.py"


def run(payload=None, args=()):
    return subprocess.run(
        [sys.executable, str(GUARD), *args],
        input=json.dumps(payload) if payload else None,
        capture_output=True,
        text=True,
        cwd=ROOT,
    )


@pytest.mark.parametrize("path", ["data/raw/CTRL_1_R1.fastq.gz", "results/counts/counts_matrix.tsv", ".env"])
def test_deny_writes(path):
    r = run({"tool_name": "Write", "tool_input": {"file_path": str(ROOT / path)}})
    assert r.returncode == 2, r.stderr


@pytest.mark.parametrize("cmd", ["git push origin main", "rm -rf data/raw", "aws s3 rm s3://b/x"])
def test_deny_commands(cmd):
    assert run({"tool_name": "Bash", "tool_input": {"command": cmd}}).returncode == 2


@pytest.mark.parametrize("cmd", ["sbatch run.sh", "aws s3 sync results s3://b/", "pip install foo"])
def test_ask_commands(cmd):
    r = run({"tool_name": "Bash", "tool_input": {"command": cmd}})
    assert r.returncode == 0 and json.loads(r.stdout)["hookSpecificOutput"]["permissionDecision"] == "ask"


def test_ask_scientific_config():
    r = run({"tool_name": "Edit", "tool_input": {"file_path": str(ROOT / "config/config.yaml")}})
    assert json.loads(r.stdout)["hookSpecificOutput"]["permissionDecision"] == "ask"


def test_allow_tests_and_code():
    assert run({"tool_name": "Bash", "tool_input": {"command": "pytest -q"}}).returncode == 0
    assert run({"tool_name": "Edit", "tool_input": {"file_path": str(ROOT / "scripts/qc_summary.py")}}).stdout == ""


def test_cli_mode_for_other_agents():
    assert run(args=["--command", "sbatch x.sh"]).returncode == 3
    assert run(args=["--write", "data/raw/x"]).returncode == 2
