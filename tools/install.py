#!/usr/bin/env python3
"""Install reference-only guidance; explicit standalone skill registration is optional.

Local platform markers are a conservative conflict check, not a complete
inventory. Missing markers cannot establish that no global plugin is active.
"""
import argparse
import json
from pathlib import Path
import sys

PACKAGE = Path(__file__).resolve().parents[1]


def platform_markers(target):
    """Return local ownership signals without modifying or loading platform code."""
    markers = []
    for relative in ('.cannbot', '.codex/cannbot-plugin.json', '.opencode/cannbot-plugin.json',
                     '.codex/cannbot-manifest.json', '.opencode/cannbot-manifest.json'):
        path = target / relative
        if path.exists() or path.is_symlink():
            markers.append(path)
    for folder in ('.codex', '.opencode'):
        for path in sorted((target / folder).glob('*-manifest.json')):
            if path in markers or not path.is_file():
                continue
            try:
                data = json.loads(path.read_text())
            except (OSError, ValueError):
                continue
            if isinstance(data, dict) and data.get('brand') == 'CANNBot':
                markers.append(path)
    for relative in ('AGENTS.md', 'CLAUDE.md'):
        path = target / relative
        if path.is_file() and '<!-- CANNBOT:' in path.read_text(errors='replace'):
            markers.append(path)
    return markers


def preflight_mode(target, package, register_skills):
    if register_skills:
        markers = platform_markers(target)
        if markers:
            raise ValueError('CANNBot owns this project integration; refusing --register-skills. '
                             'Use reference-only mode. Local markers: '
                             + ', '.join(str(path) for path in markers))
        return
    active = []
    for skill in sorted((package / 'skills').glob('*/SKILL.md')):
        path = target / '.agents/skills' / skill.parent.name
        if path.exists() or path.is_symlink():
            active.append(path)
    if active:
        raise ValueError('active or legacy Harness skill registrations remain: '
                         + ', '.join(str(path) for path in active)
                         + '. Reference-only installation cannot deactivate these. Review and '
                         'relocate only verified Harness-owned registrations before retrying; '
                         'unknown user content and platform files must be preserved. No files changed.')


def plan(target, package=PACKAGE, *, register_skills=False):
    target = Path(target).resolve(strict=True)
    if not target.is_dir():
        raise ValueError('target must be a directory')
    package = Path(package)
    preflight_mode(target, package, register_skills)
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
            if folder == 'skills' and register_skills:
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


def install(target, apply=False, package=PACKAGE, *, register_skills=False):
    files = plan(target, package, register_skills=register_skills)
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
    p.add_argument('--register-skills', action='store_true',
                   help='standalone projects only: register .agents/skills instead of keeping .harness/skills references')
    args = p.parse_args()
    try:
        count = install(args.target, args.apply, register_skills=args.register_skills)
        print(f'{count} files; root AGENTS.md and project settings are never overwritten.')
        if args.register_skills:
            print('Standalone registration selected. Local checks cannot detect every global plugin; '
                  'absence of markers does not establish absence of CANNBot. Applicable CANNBot workflows take precedence.')
        else:
            print('Reference-only mode: skills remain in .harness/skills and are not registered for automatic discovery.')
        print('Adapt .harness/templates/AGENTS.project.md as project supplements; '
              'preserve CANNBot instructions, manifests and workflow ownership.')
    except (OSError, ValueError) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
