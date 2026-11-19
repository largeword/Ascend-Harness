import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]


def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'tools' / (name + '.py'))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


class ToolsTest(unittest.TestCase):
    def test_evidence_cannot_promote_compile_to_device(self):
        m = module('check_evidence')
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'build.log').write_text('compiler finished')
            data = {'schema_version': 1, 'subject': {'revision': 'abc', 'scenario': 'short'},
                    'gates': {g: {'status': 'not_run', 'reason': '', 'artifacts': []} for g in m.GATES}, 'claims': []}
            data['gates']['compile'] = {'status': 'pass', 'reason': 'build completed', 'artifacts': ['build.log']}
            self.assertEqual(m.validate(data, root), [])
            self.assertTrue(m.validate(data, root, ['device']))
            data['claims'] = ['device']
            self.assertTrue(m.validate(data, root))
            data['claims'] = []
            data['gates']['device'] = {'status': 'pass', 'reason': 'invented', 'artifacts': []}
            self.assertTrue(m.validate(data, root))
            data['gates']['device']['artifacts'] = ['../outside.log']
            self.assertTrue(m.validate(data, root))

    def test_evidence_rejects_malformed_types(self):
        m = module('check_evidence')
        self.assertTrue(m.validate({'schema_version': True}, ROOT))
        data = json.loads((ROOT / 'templates/evidence.json').read_text())
        data['gates']['source']['status'] = []
        self.assertTrue(m.validate(data, ROOT))

    def test_installer_dry_run_idempotency_and_conflict(self):
        m = module('install')
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            target, package = root / 'target', root / 'package'
            target.mkdir()
            (target / 'AGENTS.md').write_text('existing rules')
            (package / 'skills/demo').mkdir(parents=True)
            (package / 'skills/demo/SKILL.md').write_text('skill')
            (package / 'tools').mkdir()
            (package / 'tools/example.py').write_text('pass')
            self.assertEqual(m.install(target, package=package), 2)
            self.assertFalse((target / '.agents').exists())
            self.assertEqual(m.install(target, True, package), 2)
            self.assertEqual(m.install(target, True, package), 0)
            self.assertEqual((target / 'AGENTS.md').read_text(), 'existing rules')
            (package / 'tools/new.py').write_text('new')
            (target / '.harness/skills/demo/SKILL.md').write_text('user change')
            with self.assertRaises(ValueError):
                m.install(target, True, package)
            self.assertFalse((target / '.harness/tools/new.py').exists())

    def test_installer_does_not_follow_target_symlink(self):
        m = module('install')
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            target, package, external = root / 'target', root / 'package', root / 'external'
            target.mkdir(); external.mkdir()
            (package / 'skills/demo').mkdir(parents=True)
            (package / 'skills/demo/SKILL.md').write_text('skill')
            (target / '.harness').symlink_to(external, target_is_directory=True)
            with self.assertRaises(ValueError):
                m.install(target, True, package)
            self.assertEqual(list(external.iterdir()), [])

    def test_fingerprint_changes_for_content_or_environment_not_file_order(self):
        m = module('fingerprint')
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'kernel.cpp').write_text('first')
            (root / 'header.h').write_text('header')
            dims = dict(soc='test-soc', cann='test-cann', compiler='test-compiler', python='test-python', build_args=['-O2'])
            first = m.fingerprint(root, ['kernel.cpp', 'header.h'], dims)['sha256']
            self.assertEqual(first, m.fingerprint(root, ['header.h', 'kernel.cpp'], dims)['sha256'])
            (root / 'kernel.cpp').write_text('second')
            second = m.fingerprint(root, ['header.h', 'kernel.cpp'], dims)['sha256']
            self.assertNotEqual(first, second)
            dims['soc'] = 'other-soc'
            self.assertNotEqual(second, m.fingerprint(root, ['header.h', 'kernel.cpp'], dims)['sha256'])

    def test_phase_real_exit_code_and_both_streams(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / 'phase'
            proc = subprocess.run([sys.executable, str(ROOT / 'tools/run_phase.py'), '--output', str(output),
                                   '--timeout', '5', '--', sys.executable, '-c',
                                   'import sys; print("out"); print("err",file=sys.stderr); sys.exit(7)'], capture_output=True)
            self.assertEqual(proc.returncode, 7)
            self.assertIn(b'out', proc.stdout); self.assertIn(b'err', proc.stdout)
            data = json.loads((output / 'phase.json').read_text())
            self.assertEqual(data['child_returncode'], 7)
            self.assertEqual(data['status'], 'fail')
            self.assertEqual((output / 'output.log').read_bytes(), proc.stdout)

    def test_timeout_is_not_pass(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / 'phase'
            proc = subprocess.run([sys.executable, str(ROOT / 'tools/run_phase.py'), '--output', str(output),
                                   '--timeout', '0.15', '--', sys.executable, '-c',
                                   'import time; print("started",flush=True); time.sleep(10)'], capture_output=True, timeout=6)
            self.assertEqual(proc.returncode, 124)
            self.assertEqual(json.loads((output / 'phase.json').read_text())['status'], 'timeout')

    def test_spawn_error_has_manifest(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / 'phase'
            proc = subprocess.run([sys.executable, str(ROOT / 'tools/run_phase.py'), '--output', str(output),
                                   '--timeout', '2', '--', '/not-a-real-program-for-test'], capture_output=True)
            self.assertEqual(proc.returncode, 127)
            self.assertEqual(json.loads((output / 'phase.json').read_text())['status'], 'spawn_error')

    def test_phase_rejects_nonfinite_timeout(self):
        m = module('run_phase')
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / 'phase'
            for value in (float('nan'), float('inf'), -1, 0):
                with self.assertRaises(ValueError):
                    m.run([sys.executable, '-c', 'pass'], output, value)
                self.assertFalse(output.exists())

    def test_sigterm_preserves_manifest_and_cleans_child(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / 'phase'
            proc = subprocess.Popen([sys.executable, str(ROOT / 'tools/run_phase.py'), '--output', str(output),
                                     '--timeout', '10', '--', sys.executable, '-c',
                                     'import os,time,signal,sys; '
                                     'signal.signal(signal.SIGTERM, lambda *_: (print("shutdown",flush=True),sys.exit(0))); '
                                     'print(os.getpid(),flush=True); time.sleep(10)'],
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            child_pid = None
            try:
                deadline = time.monotonic() + 5
                while time.monotonic() < deadline:
                    log = output / 'output.log'
                    if log.exists() and log.read_text().strip():
                        child_pid = int(log.read_text().strip())
                        break
                    time.sleep(0.02)
                self.assertIsNotNone(child_pid)
                proc.send_signal(signal.SIGTERM)
                proc.communicate(timeout=6)
                self.assertEqual(proc.returncode, 143)
                data = json.loads((output / 'phase.json').read_text())
                self.assertEqual(data['status'], 'interrupted')
                self.assertIn('shutdown', (output / 'output.log').read_text())
                with self.assertRaises(ProcessLookupError):
                    os.kill(child_pid, 0)
            finally:
                if proc.poll() is None:
                    proc.kill()
                    proc.communicate()
                if child_pid is not None:
                    try:
                        os.kill(child_pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass

    def test_cleanup_failure_keeps_primary_exit_and_writes_evidence(self):
        m = module('run_phase')
        with tempfile.TemporaryDirectory() as folder:
            for child_rc, expected_rc in ((0, 125), (7, 7)):
                output = Path(folder) / str(child_rc)
                with mock.patch.object(m, 'signal_group', side_effect=PermissionError('test denied')):
                    self.assertEqual(m.run([sys.executable, '-c', f'raise SystemExit({child_rc})'], output, 5), expected_rc)
                data = json.loads((output / 'phase.json').read_text())
                self.assertEqual(data['cleanup'], 'failed')
                self.assertEqual(data['child_returncode'], child_rc)


if __name__ == '__main__':
    unittest.main()
