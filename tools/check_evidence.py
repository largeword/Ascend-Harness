#!/usr/bin/env python3
"""Validate evidence bookkeeping; does not certify numerical or NPU results."""
import argparse
import json
from pathlib import Path

GATES = ('source', 'host', 'compile', 'device', 'graph_capture', 'graph_replay', 'quality', 'performance')
STATES = {'not_run', 'pass', 'fail', 'blocked', 'not_applicable'}


def validate(data, root, required=()):
    errors = []
    if (not isinstance(data, dict) or type(data.get('schema_version')) is not int
            or data['schema_version'] != 1):
        return ['schema_version must be 1']
    subject = data.get('subject', {})
    if not isinstance(subject, dict) or any(not isinstance(subject.get(k), str) or not subject[k].strip()
                                           for k in ('revision', 'scenario')):
        errors.append('subject requires nonempty revision and scenario')
    gates = data.get('gates')
    if not isinstance(gates, dict):
        return errors + ['gates must be an object']
    root = Path(root).resolve()
    for name in GATES:
        gate = gates.get(name)
        if not isinstance(gate, dict):
            errors.append(f'{name}: missing gate')
            continue
        state = gate.get('status')
        if not isinstance(state, str) or state not in STATES:
            errors.append(f'{name}: unknown status {state!r}')
        reason = gate.get('reason')
        if state in ('pass', 'blocked', 'not_applicable') and (not isinstance(reason, str) or not reason.strip()):
            errors.append(f'{name}: {state} needs a reason')
        artifacts = gate.get('artifacts')
        if not isinstance(artifacts, list):
            errors.append(f'{name}: artifacts must be a list')
            continue
        if state == 'pass' and not artifacts:
            errors.append(f'{name}: pass requires an artifact')
        for value in artifacts:
            if not isinstance(value, str) or not value:
                errors.append(f'{name}: artifact must be a nonempty path')
                continue
            path = Path(value)
            full = (root / path).resolve()
            if path.is_absolute() or not full.is_relative_to(root):
                errors.append(f'{name}: artifact escapes evidence root: {value}')
            elif not full.is_file():
                errors.append(f'{name}: artifact missing: {value}')
    claims = data.get('claims', [])
    if not isinstance(claims, list) or any(not isinstance(x, str) for x in claims):
        errors.append('claims must be a list of gate names')
        claims = []
    for name in [*claims, *required]:
        if name not in GATES:
            errors.append(f'unknown gate claim: {name}')
        elif not isinstance(gates.get(name), dict) or gates[name].get('status') != 'pass':
            errors.append(f'{name}: claimed/required gate is not pass')
    return errors


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('evidence', type=Path)
    p.add_argument('--root', type=Path, help='artifact base directory; default: evidence file parent')
    p.add_argument('--require', action='append', choices=GATES, default=[])
    args = p.parse_args()
    try:
        errors = validate(json.loads(args.evidence.read_text()), args.root or args.evidence.parent, args.require)
    except (OSError, ValueError) as exc:
        errors = [str(exc)]
    for error in errors:
        print('ERROR:', error)
    print('Evidence bookkeeping: ' + ('FAIL' if errors else 'VALID (not a hardware/quality certification)'))
    return bool(errors)


if __name__ == '__main__':
    raise SystemExit(main())
