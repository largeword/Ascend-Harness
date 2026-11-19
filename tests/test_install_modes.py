"""Exercise coexistence without installing or invoking any external platform."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('install_modes_under_test', ROOT / 'tools/install.py')
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class InstallModesTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.target = self.root / 'target'
        self.target.mkdir()
        self.package = self.root / 'package'
        self.skill = self.package / 'skills/ascend-demo/SKILL.md'
        self.skill.parent.mkdir(parents=True)
        self.skill.write_text('name: ascend-demo\nStandalone fixture only\n')
        guide = self.package / 'guides/example.md'
        guide.parent.mkdir()
        guide.write_text('Project evidence supplement\n')

    def test_default_is_reference_only_even_without_platform_markers(self):
        self.assertEqual(installer.install(self.target, package=self.package), 2)
        self.assertEqual(list(self.target.iterdir()), [])
        self.assertEqual(installer.install(self.target, True, self.package), 2)
        self.assertEqual((self.target / '.harness/skills/ascend-demo/SKILL.md').read_bytes(), self.skill.read_bytes())
        self.assertFalse((self.target / '.agents').exists())
        self.assertEqual(installer.install(self.target, True, self.package), 0)

    def test_default_preserves_platform_metadata_links_and_existing_instructions(self):
        external = self.root / 'platform-skill'
        external.mkdir()
        (external / 'SKILL.md').write_text('Platform-owned skill\n')
        skill_link = self.target / '.agents/skills/platform-demo'
        skill_link.parent.mkdir(parents=True)
        skill_link.symlink_to(external, target_is_directory=True)
        protected = {
            'AGENTS.md': '<!-- CANNBOT:demo:begin -->\nexisting rules\n',
            '.codex/cannbot-plugin.json': '{"schemaVersion":2}\n',
            '.opencode/demo-manifest.json': '{"brand":"CANNBot"}\n',
            '.cannbot/plugins/demo/asset.txt': 'Platform asset\n',
        }
        for relative, content in protected.items():
            path = self.target / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
        workflow_link = self.target / '.codex/workflows'
        workflow_link.symlink_to(external, target_is_directory=True)
        installer.install(self.target, True, self.package)
        for relative, content in protected.items():
            self.assertEqual((self.target / relative).read_text(), content)
        self.assertEqual(skill_link.readlink(), external)
        self.assertEqual(workflow_link.readlink(), external)
        self.assertFalse((self.target / '.agents/skills/ascend-demo').exists())

    def test_legacy_registration_blocks_before_any_write_without_deleting_content(self):
        active = self.target / '.agents/skills/ascend-demo'
        active.mkdir(parents=True)
        (active / 'SKILL.md').write_text('User-modified legacy Harness skill\n')
        for apply in (False, True):
            with self.assertRaisesRegex(ValueError, 'active or legacy Harness'):
                installer.install(self.target, apply, self.package)
            self.assertFalse((self.target / '.harness').exists())
            self.assertEqual((active / 'SKILL.md').read_text(), 'User-modified legacy Harness skill\n')

    def test_dangling_legacy_registration_is_not_silently_ignored(self):
        active = self.target / '.agents/skills/ascend-demo'
        active.parent.mkdir(parents=True)
        destination = self.root / 'missing-original-skill'
        active.symlink_to(destination, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'active or legacy Harness'):
            installer.install(self.target, True, self.package)
        self.assertEqual(active.readlink(), destination)
        self.assertFalse((self.target / '.harness').exists())

    def test_explicit_standalone_registers_without_modifying_root_instructions(self):
        instructions = self.target / 'AGENTS.md'
        instructions.write_text('User task scope\n')
        installer.install(self.target, True, self.package, register_skills=True)
        self.assertEqual((self.target / '.agents/skills/ascend-demo/SKILL.md').read_bytes(), self.skill.read_bytes())
        self.assertFalse((self.target / '.harness/skills').exists())
        self.assertEqual(instructions.read_text(), 'User task scope\n')
        self.assertEqual(installer.install(self.target, True, self.package, register_skills=True), 0)

    def test_explicit_registration_refuses_local_platform_ownership(self):
        markers = {
            '.codex/cannbot-plugin.json': '{}',
            '.opencode/cannbot-plugin.json': '{}',
            '.codex/cannbot-manifest.json': '{}',
            '.codex/ops-example-manifest.json': json.dumps({'brand': 'CANNBot'}),
            'AGENTS.md': '<!-- CANNBOT:example:begin -->\n',
            '.cannbot/marker.txt': 'owned',
        }
        for relative, content in markers.items():
            with self.subTest(marker=relative), tempfile.TemporaryDirectory(dir=self.root) as folder:
                target = Path(folder)
                marker = target / relative
                marker.parent.mkdir(parents=True, exist_ok=True)
                marker.write_text(content)
                with self.assertRaisesRegex(ValueError, 'refusing --register-skills'):
                    installer.install(target, True, self.package, register_skills=True)
                self.assertFalse((target / '.harness').exists())
                self.assertFalse((target / '.agents').exists())
                self.assertEqual(marker.read_text(), content)

    def test_cli_registration_warns_that_local_detection_is_incomplete(self):
        result = subprocess.run([sys.executable, str(ROOT / 'tools/install.py'), str(self.target),
                                 '--register-skills'], text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('cannot detect every global plugin', result.stdout)
        self.assertFalse((self.target / '.agents').exists())


if __name__ == '__main__':
    unittest.main()
