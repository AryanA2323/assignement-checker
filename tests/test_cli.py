import subprocess
import sys
from pathlib import Path

def test_cli_execution():
    cmd = [
        sys.executable,
        "cli.py",
        "--master", "demo_data/master_solution.json",
        "--students", "demo_data/students",
        "--mock",
        "--output", "reports/test_output.csv"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode == 0
    assert "STUDENT EVALUATION SUMMARY REPORT" in result.stdout
    assert "Alice Johnson" in result.stdout
    assert "Charlie Davis" in result.stdout
    assert Path("reports/test_output.csv").exists()
