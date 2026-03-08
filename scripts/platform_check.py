"""
Local quality gate for the platform repository.

This gate is intentionally stdlib-only so it can run in a fresh clone after
`uv sync`, without adding dedicated lint/type/test tool dependencies yet.
"""

from __future__ import annotations

import ast
import importlib
import inspect
import subprocess
import sys
from pathlib import Path
from typing import get_type_hints

PLATFORM_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_DIR = PLATFORM_ROOT / "scripts"
TEST_DIR = PLATFORM_ROOT / "tests"
PYTHON_MODULES = [
    "scripts.constants",
    "scripts.platform_up",
    "scripts.platform_down",
    "scripts.platform_status",
    "scripts.platformctl",
    "scripts.platform_check",
    "scripts.infra_only",
    "scripts.sync_shared_secrets",
    "scripts.sync_platform_configs",
]


def _iter_python_files() -> list[Path]:
    paths: list[Path] = []
    for base in (SCRIPT_DIR, TEST_DIR):
        if not base.exists():
            continue
        for path in sorted(base.rglob("*.py")):
            if "__pycache__" in path.parts:
                continue
            paths.append(path)
    return paths


def _run_lint_phase() -> bool:
    print("[lint] parsing Python sources...")
    ok = True
    for path in _iter_python_files():
        try:
            source = path.read_text(encoding="utf-8")
            ast.parse(source, filename=str(path))
        except SyntaxError as exc:
            ok = False
            print(f"  [FAIL] {path.relative_to(PLATFORM_ROOT)}:{exc.lineno}: {exc.msg}")
    if ok:
        print("  [OK] syntax checks passed")
    return ok


def _run_type_phase() -> bool:
    print("[type] resolving annotations for platform modules...")
    ok = True
    module_names = PYTHON_MODULES + _discover_control_plane_modules()
    for module_name in module_names:
        try:
            module = importlib.import_module(module_name)
            for _, obj in inspect.getmembers(module):
                if inspect.isfunction(obj) and obj.__module__ == module.__name__:
                    get_type_hints(obj, globalns=vars(module))
        except Exception as exc:  # pragma: no cover - defensive gate output
            ok = False
            print(f"  [FAIL] {module_name}: {exc}")
    if ok:
        print("  [OK] annotation resolution passed")
    return ok


def _discover_control_plane_modules() -> list[str]:
    modules: list[str] = []
    base = SCRIPT_DIR / "control_plane"
    if not base.exists():
        return modules

    for path in sorted(base.rglob("*.py")):
        if path.name == "__init__.py":
            continue
        rel = path.relative_to(PLATFORM_ROOT).with_suffix("")
        modules.append(".".join(rel.parts))
    return modules


def _run_test_phase() -> bool:
    print("[test] running unittest suite...")
    cmd = [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py", "-v"]
    result = subprocess.run(cmd)
    if result.returncode == 0:
        print("  [OK] tests passed")
        return True
    print(f"  [FAIL] unittest exited with code {result.returncode}")
    return False


def main() -> int:
    print("Card Fraud Platform - Local Quality Gate")
    print()

    results = [
        _run_lint_phase(),
        _run_type_phase(),
        _run_test_phase(),
    ]

    print()
    if all(results):
        print("Quality gate passed.")
        return 0

    print("Quality gate failed.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
