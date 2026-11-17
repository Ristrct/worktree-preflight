"""Check which Git checkout a terminal can read."""

import argparse
import os
from pathlib import Path
import subprocess


REDIRECT_VARIABLES = ('GIT_DIR', 'GIT_WORK_TREE', 'GIT_COMMON_DIR', 'GIT_INDEX_FILE')


def run_git(directory: Path, env: dict[str, str], *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ['git', '--no-optional-locks', '-c', 'core.fsmonitor=false', '-C', str(directory), *args],
        env=env, capture_output=True, check=False, timeout=10,
    )


def failure(result: subprocess.CompletedProcess) -> str:
    message = result.stderr.lower()
    for fragment, explanation in (
        (b'must be run in a work tree', 'Git requires a working tree'),
        (b'permission denied', 'access denied'),
        (b'access is denied', 'access denied'),
        (b'dubious ownership', 'Git rejected repository ownership'),
        (b'not a git repository', 'Git could not find a repository'),
    ):
        if fragment in message:
            return explanation
    return f'Git exited with code {result.returncode}'


def probe(directory: Path, expected: Path, env: dict[str, str]) -> tuple[bool | None, str]:
    try:
        return inspect_checkout(directory, expected, env)
    except subprocess.TimeoutExpired:
        return None, 'Git probe timed out'
    except (OSError, RuntimeError) as error:
        return None, f'probe unavailable ({type(error).__name__})'


def inspect_checkout(directory: Path, expected: Path, env: dict[str, str]) -> tuple[bool, str]:
    root = run_git(directory, env, 'rev-parse', '--show-toplevel')
    status = run_git(directory, env, 'status', '--porcelain', '--untracked-files=no', '--ignore-submodules=all')
    if root.returncode:
        root_state = failure(root)
        matches = False
    else:
        raw_path = root.stdout.removesuffix(b'\n')
        if os.name == 'nt':
            raw_path = raw_path.removesuffix(b'\r')
        matches = Path(os.fsdecode(raw_path)).resolve() == expected
        root_state = 'expected checkout' if matches else 'DIFFERENT checkout'
    status_state = failure(status) if status.returncode else 'OK'
    return matches and status.returncode == 0, f'root={root_state} | status={status_state}'


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--expected', required=True, type=Path, help='Root of the checkout you intended to use.')
    args = parser.parse_args()
    try:
        expected = args.expected.resolve(strict=True)
        cwd = Path.cwd()
        if not expected.is_dir():
            parser.error('--expected must be a directory')
        inherited = dict(os.environ)
        present = sorted(key for key in inherited if key.upper() in REDIRECT_VARIABLES)
        clean = {key: value for key, value in inherited.items() if key not in present}
        current_ok, current = probe(cwd, expected, inherited)
        explicit_ok, explicit = probe(expected, expected, inherited)
        clean_ok, clean_result = probe(expected, expected, clean)
    except (OSError, RuntimeError, subprocess.TimeoutExpired) as error:
        print(f'Could not complete Git probe ({type(error).__name__}). Check Git and the expected directory.')
        return 2

    print(f'Git override variables present: {", ".join(present) or "none"}')
    print(f'Current directory: {current}')
    print(f'Explicit checkout: {explicit}')
    print(f'Explicit checkout without listed overrides: {clean_result}')
    if explicit_ok is False and clean_ok and present:
        print('Git works when the listed overrides are removed from the child process.')
    elif current_ok is False and explicit_ok:
        print('Git works when pointed directly at the expected checkout.')
    elif explicit_ok is False:
        print('Git also failed or selected a different checkout with an explicit path. Compare this report inside and outside the agent.')
    if None in (current_ok, explicit_ok, clean_ok):
        return 2
    return 0 if current_ok and explicit_ok else 1


if __name__ == '__main__':
    raise SystemExit(main())
