#!/usr/bin/env python3
"""Run one explicitly requested command with live logs and bounded lifetime.

POSIX only. No shell, NPU discovery, process-name killing, or automatic retry.
"""
import argparse
import datetime
import json
import math
import os
from pathlib import Path
import selectors
import signal
import subprocess
import sys
import time


def signal_group(proc, sig):
    try:
        os.killpg(proc.pid, sig)
    except ProcessLookupError:
        pass


def run(command, output, timeout, cwd=None):
    if os.name != 'posix':
        raise ValueError('run_phase requires POSIX process groups')
    if not command or not math.isfinite(timeout) or timeout <= 0:
        raise ValueError('command and finite positive timeout required')
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    record = dict(schema_version=1, command=command, cwd=str(Path(cwd or '.').resolve()),
                  started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  timeout_seconds=timeout, status='running', exit_code=None,
                  child_returncode=None, cleanup='not_needed', log='output.log')
    proc = None
    selector = selectors.DefaultSelector()
    previous_handlers = {}
    pending_signal = None

    def interrupt(signum, frame):
        nonlocal pending_signal
        pending_signal = signum

    try:
        # CLI runs in the main thread; preserve callers' handlers on return.
        for sig in (signal.SIGINT, signal.SIGTERM):
            previous_handlers[sig] = signal.signal(sig, interrupt)
        with (output / 'output.log').open('wb') as log:
            try:
                proc = subprocess.Popen(command, cwd=cwd, stdout=subprocess.PIPE,
                                        stderr=subprocess.STDOUT, start_new_session=True)
            except OSError as exc:
                message = f'Cannot start command: {exc}\n'.encode()
                log.write(message)
                sys.stderr.buffer.write(message)
                record.update(status='spawn_error', exit_code=127)
                return 127
            selector.register(proc.stdout, selectors.EVENT_READ)
            stop_at = None
            while selector.get_map() or proc.poll() is None:
                now = time.monotonic()
                if stop_at is None and pending_signal is not None:
                    record.update(status='interrupted', exit_code=128 + pending_signal,
                                  interruption_signal=pending_signal)
                    signal_group(proc, signal.SIGTERM)
                    stop_at = now
                if stop_at is None and now - started >= timeout:
                    record.update(status='timeout', exit_code=124)
                    signal_group(proc, signal.SIGTERM)
                    stop_at = now
                if stop_at is not None and now - stop_at >= 1:
                    signal_group(proc, signal.SIGKILL)
                if stop_at is not None and now - stop_at >= 3:
                    break
                for key, _ in selector.select(0.05):
                    data = os.read(key.fileobj.fileno(), 65536)
                    if not data:
                        selector.unregister(key.fileobj)
                        continue
                    log.write(data)
                    log.flush()
                    try:
                        sys.stdout.buffer.write(data)
                        sys.stdout.buffer.flush()
                    except BrokenPipeError:
                        pass  # A closed terminal pipe must not erase the phase log.
            if record['exit_code'] is None:
                rc = proc.wait()
                record.update(status='pass' if rc == 0 else 'fail',
                              exit_code=rc if rc >= 0 else 128 - rc)
    except KeyboardInterrupt:
        record.update(status='interrupted', exit_code=130)
    except Exception as exc:
        record.update(status='runner_error', exit_code=125, error=str(exc))
    finally:
        # A second signal must not interrupt bounded cleanup or erase evidence.
        for sig in previous_handlers:
            signal.signal(sig, signal.SIG_IGN)
        selector.close()
        if proc is not None:
            # Children may outlive a launcher even after closing stdout. Only
            # this phase's dedicated process group is eligible for cleanup.
            try:
                signal_group(proc, signal.SIGTERM)
                try:
                    proc.wait(timeout=1)
                except subprocess.TimeoutExpired:
                    signal_group(proc, signal.SIGKILL)
                    proc.wait(timeout=3)
                signal_group(proc, signal.SIGKILL)
                record['cleanup'] = 'owned_process_group_signalled'
            except (OSError, subprocess.TimeoutExpired) as exc:
                record.update(cleanup='failed', cleanup_error=str(exc))
                if record['exit_code'] in (None, 0):
                    record.update(status='runner_error', exit_code=125)
            record['child_returncode'] = proc.returncode
            proc.stdout.close()
        record['elapsed_seconds'] = round(time.monotonic() - started, 6)
        record['exit_code'] = record['exit_code'] if record['exit_code'] is not None else 125
        try:
            (output / 'phase.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
        finally:
            for sig, handler in previous_handlers.items():
                signal.signal(sig, handler)
    return record['exit_code']


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True, help='new phase directory (must not exist)')
    p.add_argument('--timeout', type=float, required=True)
    p.add_argument('--cwd', type=Path)
    p.add_argument('command', nargs=argparse.REMAINDER, help='-- program arg ...')
    args = p.parse_args(argv)
    command = args.command[1:] if args.command[:1] == ['--'] else args.command
    try:
        return run(command, args.output, args.timeout, args.cwd)
    except (OSError, ValueError) as exc:
        p.error(str(exc))


if __name__ == '__main__':
    sys.exit(main())
