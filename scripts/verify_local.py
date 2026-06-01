from __future__ import annotations

import argparse
import shutil
import socket
import subprocess
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SNAPSHOT_DIR = Path("outputs_improved_2026-04-24_upgrade_pass5_release_candidate")


def print_section(title: str) -> None:
    print()
    print("=" * 80)
    print(title)
    print("=" * 80)


def format_command(command: list[str]) -> str:
    return " ".join(command)


def run_required(title: str, command: list[str]) -> None:
    print_section(title)
    print(f"$ {format_command(command)}")
    subprocess.run(command, cwd=REPO_ROOT, check=True)


def run_optional(title: str, command: list[str], *, missing_tool: str | None = None) -> None:
    print_section(title)
    if missing_tool and shutil.which(missing_tool) is None:
        print(f"SKIPPED: {missing_tool} is not available on PATH.")
        return

    print(f"$ {format_command(command)}")
    completed = subprocess.run(
        command,
        cwd=REPO_ROOT,
        check=False,
        text=True,
        capture_output=True,
    )
    if completed.stdout:
        print(completed.stdout, end="")
    if completed.stderr:
        print(completed.stderr, end="", file=sys.stderr)

    if completed.returncode == 0:
        return
    if missing_tool and completed.returncode == 1:
        print("No matches found.")
        return
    print(f"Optional check exited with status {completed.returncode}.")


def report_generated_status() -> None:
    print_section("Generated/Release Path Status")
    if shutil.which("git") is None:
        print("SKIPPED: git is not available on PATH.")
        return

    command = [
        "git",
        "status",
        "--short",
        "--",
        "docs",
        "outputs",
        "outputs_*",
        "audits",
    ]
    print(f"$ {format_command(command)}")
    completed = subprocess.run(
        command,
        cwd=REPO_ROOT,
        check=False,
        text=True,
        capture_output=True,
    )
    if completed.stdout:
        print(completed.stdout, end="")
        print("WARNING: generated/release paths have local modifications.")
    else:
        print("No local modifications detected under docs, outputs, outputs_*, or audits.")
    if completed.stderr:
        print(completed.stderr, end="", file=sys.stderr)
    if completed.returncode != 0:
        print(f"Optional git status check exited with status {completed.returncode}.")


def run_dangerous_operation_scan() -> None:
    pattern = r"shutil\.rmtree|Remove-Item|rm -r|del /s|copytree|shell=True|eval\(|exec\("
    command = [
        "rg",
        "-n",
        pattern,
        "-g",
        "*.py",
        "-g",
        "*.ps1",
        "-g",
        "!outputs*/**",
        "-g",
        "!outputs/**",
        "-g",
        "!audits/**",
        "-g",
        "!docs/plotly.min.js",
    ]
    run_optional("Optional Destructive-Operation Scan", command, missing_tool="rg")


def resolve_repo_path(path: Path) -> Path:
    return path if path.is_absolute() else REPO_ROOT / path


def snapshot_requirement_flags(snapshot_dir: Path) -> list[str]:
    flags: list[str] = []
    if (
        (snapshot_dir / "derived_scoring" / "commander_model_stability.csv").exists()
        and (snapshot_dir / "derived_scoring" / "commander_tiers.csv").exists()
        and (snapshot_dir / "derived_scoring" / "page_type_score_contributions.csv").exists()
        and (snapshot_dir / "audits" / "high_ranked_commander_flags.csv").exists()
    ):
        flags.append("--require-upgrade-files")
    if (
        (snapshot_dir / "derived_scoring" / "commander_rank_confidence_summary.csv").exists()
        and (snapshot_dir / "derived_scoring" / "commander_tiers_confidence_adjusted.csv").exists()
        and (snapshot_dir / "derived_scoring" / "bootstrap_rank_confidence.csv").exists()
    ):
        flags.append("--require-confidence-files")
    if (
        (snapshot_dir / "derived_scoring" / "role_class_score_contributions.csv").exists()
        and (snapshot_dir / "RANKING_RESULTS_PASS4_ROLE_SENSITIVITY.csv").exists()
        and (snapshot_dir / "verification" / "verified_command_role_classification.csv").exists()
    ):
        flags.append("--require-role-files")
    if (
        (snapshot_dir / "RANKING_RESULTS_SYNTHESIS_TIERED.csv").exists()
        and (snapshot_dir / "DASHBOARD_RELEASE_METADATA.json").exists()
    ):
        flags.append("--require-synthesis-files")
    return flags


def run_snapshot_integrity_audit(snapshot_arg: Path) -> None:
    snapshot_dir = resolve_repo_path(snapshot_arg).resolve()
    print_section("Full Check: Snapshot Integrity Audit")
    if not snapshot_dir.exists():
        print(f"SKIPPED: snapshot directory does not exist: {snapshot_dir}")
        return

    with tempfile.TemporaryDirectory(prefix="ranking_generals_verify_") as raw_temp_dir:
        output_path = Path(raw_temp_dir) / "snapshot_integrity_audit.json"
        command = [
            sys.executable,
            "audit_snapshot_integrity.py",
            "--snapshot-dir",
            str(snapshot_dir),
            "--output",
            str(output_path),
            *snapshot_requirement_flags(snapshot_dir),
        ]
        print(f"Temporary audit output: {output_path}")
        print(f"$ {format_command(command)}")
        subprocess.run(command, cwd=REPO_ROOT, check=True)


def find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def dashboard_qa_prerequisites(snapshot_dir: Path) -> list[Path]:
    return [
        snapshot_dir / "dashboard" / "index.html",
        snapshot_dir / "dashboard" / "dashboard_data.js",
        snapshot_dir / "dashboard" / "app.js",
        snapshot_dir / "RANKING_BUILD_METRICS.json",
        snapshot_dir / "RANKING_RESULTS_SENSITIVITY.csv",
    ]


def run_dashboard_qa(snapshot_arg: Path) -> None:
    snapshot_dir = resolve_repo_path(snapshot_arg).resolve()
    print_section("Full Check: Dashboard QA")
    if not snapshot_dir.exists():
        print(f"SKIPPED: snapshot directory does not exist: {snapshot_dir}")
        return

    missing = [path for path in dashboard_qa_prerequisites(snapshot_dir) if not path.exists()]
    if missing:
        print("SKIPPED: dashboard QA prerequisites are missing:")
        for path in missing:
            print(f"  - {path}")
        return

    with tempfile.TemporaryDirectory(prefix="ranking_generals_dashboard_qa_") as raw_temp_dir:
        output_path = Path(raw_temp_dir) / "dashboard_qa_summary.json"
        command = [
            sys.executable,
            "qa_dashboard_snapshot.py",
            "--snapshot-dir",
            str(snapshot_dir),
            "--port",
            str(find_free_port()),
            "--output",
            str(output_path),
        ]
        print(f"Temporary dashboard QA output: {output_path}")
        print(f"$ {format_command(command)}")
        subprocess.run(command, cwd=REPO_ROOT, check=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run local verification checks for Ranking Generals.")
    parser.add_argument(
        "--full",
        action="store_true",
        help="Run slower non-destructive checks in addition to the default checks.",
    )
    parser.add_argument(
        "--snapshot-dir",
        type=Path,
        default=DEFAULT_SNAPSHOT_DIR,
        help="Snapshot directory used by --full snapshot integrity checks.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    required_commands = [
        ("Unit Tests", [sys.executable, "-m", "unittest", "discover", "-v"]),
        (
            "Unit Tests With FutureWarning As Error",
            [sys.executable, "-W", "error::FutureWarning", "-m", "unittest", "discover", "-v"],
        ),
        ("Compile Check", [sys.executable, "-m", "compileall", ".", "-q"]),
    ]

    for title, command in required_commands:
        run_required(title, command)

    report_generated_status()
    run_dangerous_operation_scan()

    if args.full:
        run_snapshot_integrity_audit(args.snapshot_dir)
        run_dashboard_qa(args.snapshot_dir)

    print_section("Verification Complete")
    print("Required checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
