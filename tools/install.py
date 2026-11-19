#!/usr/bin/env python3
"""Install portable guidance into an existing repository; plan by default."""
import argparse
from pathlib import Path
import sys

PACKAGE = Path(__file__).resolve().parents[1]


def plan(target, package=PACKAGE):
    target = Path(target).resolve(strict=True)
    if not target.is_dir():
        raise ValueError('target must be a directory')
    files = []
    for folder in ('guides', 'templates', 'tools', 'skills', 'provenance'):
        for source in sorted((package / folder).rglob('*')):
            if not source.is_file() or '__pycache__' in source.parts or source.suffix == '.pyc':
                continue
            if source.is_symlink():
                raise ValueError(f'symlink in package: {source}')
            relative = source.relative_to(package)
            if relative.as_posix() == 'tools/install.py':
                continue  # Updates must run from the complete original package.
            if folder == 'skills':
                destination = target / '.agents' / relative
            else:
                destination = target / '.harness' / relative
            for parent in (destination, *destination.parents):
                if parent == target:
                    break
                if parent.is_symlink():
                    raise ValueError(f'refusing target symlink: {parent}')
            if destination.exists():
                if not destination.is_file() or destination.read_bytes() != source.read_bytes():
                    raise ValueError(f'conflicting existing file; merge manually: {destination}')
                continue
            files.append((source, destination))
    return files


def install(target, apply=False, package=PACKAGE):
    files = plan(target, package)
    for _, destination in files:
        print(('WRITE ' if apply else 'PLAN  ') + str(destination))
    if apply:
        created = []
        try:
            for source, destination in files:
                destination.parent.mkdir(parents=True, exist_ok=True)
                with destination.open('xb') as handle:
                    created.append(destination)
                    handle.write(source.read_bytes())
        except Exception:
            for destination in reversed(created):
                destination.unlink()
            raise
    return len(files)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('target', type=Path)
    p.add_argument('--apply', action='store_true', help='write the displayed files; never overwrite')
    args = p.parse_args()
    try:
        count = install(args.target, args.apply)
        print(f'{count} files; root AGENTS.md and project settings are never overwritten.')
        print('Merge .harness/templates/AGENTS.project.md into your project instructions and adapt its configuration.')
    except (OSError, ValueError) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
