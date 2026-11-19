#!/usr/bin/env python3
"""Hash explicit build inputs; never reuse a build or clean a directory itself."""
import argparse
import hashlib
import json
from pathlib import Path


def fingerprint(root, files, dimensions):
    required = ('soc', 'cann', 'compiler', 'python', 'build_args')
    if not isinstance(dimensions, dict) or any(k not in dimensions for k in required):
        raise ValueError('dimensions must include soc, cann, compiler, python, build_args')
    if any(not isinstance(dimensions[k], str) or not dimensions[k].strip() for k in required[:-1]):
        raise ValueError('soc/cann/compiler/python must be explicit nonempty strings')
    if not isinstance(dimensions['build_args'], list) or any(not isinstance(v, str) for v in dimensions['build_args']):
        raise ValueError('build_args must be a string array')
    root = Path(root).resolve()
    sources = {}
    for item in files:
        path = (root / item).resolve(strict=True)
        if not path.is_relative_to(root) or not path.is_file():
            raise ValueError(f'input outside root or not a file: {item}')
        name = path.relative_to(root).as_posix()
        sources[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    if not sources:
        raise ValueError('at least one source file is required')
    payload = {'schema_version': 1, 'dimensions': dimensions, 'sources': sources}
    canonical = json.dumps(payload, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()
    return {**payload, 'sha256': hashlib.sha256(canonical).hexdigest()}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, default=Path.cwd())
    p.add_argument('--dimensions', type=Path, required=True, help='JSON containing explicit build dimensions')
    p.add_argument('--file', action='append', required=True, help='input relative to root; repeat per source/header/build script')
    p.add_argument('--output', type=Path, help='new manifest file; defaults to stdout')
    args = p.parse_args()
    try:
        result = fingerprint(args.root, args.file, json.loads(args.dimensions.read_text()))
        text = json.dumps(result, ensure_ascii=False, indent=2) + '\n'
        if args.output:
            with args.output.open('x') as handle:
                handle.write(text)
        else:
            print(text, end='')
    except (OSError, ValueError) as exc:
        p.error(str(exc))


if __name__ == '__main__':
    main()
