#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import importlib
import re
import sys
from pathlib import Path

MODULE_TO_REQUIREMENT = {
    'yaml': 'pyyaml',
    'pydantic_settings': 'pydantic-settings',
}
IGNORE_DIR_NAMES = {'.git', '.venv', '__pycache__'}
PYTHON_FILE_SUFFIX = '.py'


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            'Check third-party imports used by repository Python files and confirm '
            'they are covered by a requirements manifest and importable in the current interpreter.'
        )
    )
    parser.add_argument('--root', default='.', help='Repository root to scan.')
    parser.add_argument('--requirements-file', required=True, help='Path to requirements file.')
    parser.add_argument(
        '--skip-runtime-imports',
        action='store_true',
        help='Only validate manifest coverage. Do not import the discovered modules.',
    )
    parser.add_argument('--strict', action='store_true', help='Exit non-zero on any problem.')
    return parser.parse_args()


def iter_python_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob(f'*{PYTHON_FILE_SUFFIX}'):
        if any(part in IGNORE_DIR_NAMES for part in path.parts):
            continue
        files.append(path)
    return sorted(files)


def discover_first_party_roots(root: Path) -> set[str]:
    first_party: set[str] = {'tests'}
    for path in root.iterdir():
        if path.name in IGNORE_DIR_NAMES:
            continue
        if path.is_dir() and (path / '__init__.py').exists():
            first_party.add(path.name)
        elif path.suffix == '.py':
            first_party.add(path.stem)
    for candidate in root.glob('packages/*/src/*'):
        first_party.add(candidate.name)
    return first_party


def parse_imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name.split('.', 1)[0])
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0 and node.module:
                imports.add(node.module.split('.', 1)[0])
    return imports


def load_requirements(path: Path) -> set[str]:
    names: set[str] = set()
    for raw_line in path.read_text(encoding='utf-8').splitlines():
        line = raw_line.strip()
        if not line or line.startswith('#'):
            continue
        line = re.split(r'\s+#', line, maxsplit=1)[0].strip()
        name = re.split(r'[<>=!~\[]', line, maxsplit=1)[0].strip().lower().replace('_', '-')
        if name:
            names.add(name)
    return names


def normalize_requirement_name(module_name: str) -> str:
    return MODULE_TO_REQUIREMENT.get(module_name, module_name).lower().replace('_', '-')


def main() -> int:
    args = parse_args()
    root = Path(args.root).resolve()
    requirements_path = Path(args.requirements_file).resolve()
    if not requirements_path.exists():
        print(f'[ERROR] Requirements file not found: {requirements_path}', file=sys.stderr)
        return 2

    stdlib_modules = set(sys.stdlib_module_names)
    first_party = discover_first_party_roots(root)
    requirements = load_requirements(requirements_path)

    third_party_modules: set[str] = set()
    for path in iter_python_files(root):
        try:
            imports = parse_imports(path)
        except SyntaxError as exc:
            print(f'[ERROR] Could not parse {path}: {exc}', file=sys.stderr)
            return 2
        for module_name in imports:
            if module_name in stdlib_modules or module_name in first_party:
                continue
            third_party_modules.add(module_name)

    missing_from_requirements = sorted(
        module_name
        for module_name in third_party_modules
        if normalize_requirement_name(module_name) not in requirements
    )

    missing_runtime_modules: list[str] = []
    if not args.skip_runtime_imports:
        for module_name in sorted(third_party_modules):
            try:
                importlib.import_module(module_name)
            except ModuleNotFoundError:
                missing_runtime_modules.append(module_name)

    print('[INFO] Third-party modules discovered:')
    for module_name in sorted(third_party_modules):
        print(f'  - {module_name} -> {normalize_requirement_name(module_name)}')

    if missing_from_requirements:
        print('[ERROR] Missing from requirements file:', file=sys.stderr)
        for module_name in missing_from_requirements:
            print(f'  - {module_name} -> {normalize_requirement_name(module_name)}', file=sys.stderr)

    if missing_runtime_modules:
        print('[ERROR] Not importable in the current interpreter:', file=sys.stderr)
        for module_name in missing_runtime_modules:
            print(f'  - {module_name}', file=sys.stderr)

    if not missing_from_requirements and not missing_runtime_modules:
        print('[INFO] Import coverage check passed.')
        return 0

    if args.strict:
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
