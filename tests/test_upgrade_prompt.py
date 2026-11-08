"""The newest CHANGELOG upgrade prompt must embed the current skill files verbatim."""
import hashlib
import importlib.util
import json
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("upgrade_prompt", ROOT / "scripts" / "upgrade_prompt.py")
up = importlib.util.module_from_spec(spec)
spec.loader.exec_module(up)


class UpgradePromptTest(unittest.TestCase):
    def setUp(self):
        self.changelog = up.CHANGELOG.read_text(encoding="utf-8")

    def test_embedded_files_are_fresh(self):
        self.assertEqual(up.render(self.changelog), self.changelog,
                         "run: python3 scripts/upgrade_prompt.py")

    def test_blocks_round_trip_to_checksums(self):
        region = self.changelog.split(up.START + "\n", 1)[1]
        for f in up.FILES:
            body = re.search(r"^=== BEGIN %s ===\n(.*?)^=== END %s ===$" % (re.escape(f), re.escape(f)),
                             region, re.S | re.M).group(1)
            self.assertEqual(body, (up.SKILL / f).read_text(encoding="utf-8"), f)
            self.assertIn("%s  %s" % (hashlib.sha256(body.encode()).hexdigest(), f), region)

    def test_stale_copy_is_detected(self):
        stale = self.changelog.replace("=== END hooks/guard.py ===", "# drift\n=== END hooks/guard.py ===", 1)
        self.assertNotEqual(up.render(stale), stale)

    def test_prompt_belongs_to_newest_release_and_expectations_match(self):
        newest = self.changelog.split("\n## [", 2)[1]
        self.assertIn(up.START, newest, "the newest release needs its own upgrade prompt")
        version = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text())["version"]
        self.assertTrue(newest.startswith(version + "]"), newest[:20])
        lines = len((up.SKILL / "SKILL.md").read_text().splitlines())
        phases = len(re.findall(r"^## Phase", (up.SKILL / "SKILL.md").read_text(), re.M))
        for want in ("to version %s" % version, "(expect: %d, plus" % lines, 'grep -c "^## Phase" TARGET/SKILL.md (expect: %d)' % phases):
            self.assertIn(want, newest)

    def test_prompt_steps_stay_offline(self):
        steps = self.changelog.split("### Upgrade prompt", 1)[1].split(up.START, 1)[0]
        self.assertIsNone(re.search(r"\b(curl|wget|npm|pip3?|brew|git clone)\b", steps))


if __name__ == "__main__":
    unittest.main()
