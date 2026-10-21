"""Structural ECO and CLI validation tests with synthetic files."""
import json
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from hardwarecheck.cadence import build_design
from hardwarecheck.eco import compare_designs

BASE = Path(__file__).parent / "fixtures"


class EcoTests(unittest.TestCase):
    def test_changed_network_members(self):
        source = (BASE/"pstxnet.dat").read_text()
        changed = source.replace("NODE_NAME J2 1", "NODE_NAME J3 1")
        with TemporaryDirectory() as folder:
            new_path = Path(folder)/"pstxnet.dat"
            new_path.write_text(changed)
            old = build_design(BASE/"pstxnet.dat")
            new = build_design(new_path)
        diff = compare_designs(old, new)
        self.assertIn("J3", diff["added_components"])
        self.assertIn("J2", diff["removed_components"])
        self.assertEqual(diff["modified_nets"][0]["net"], "UART_TX")
        self.assertEqual(diff["status"], "STRUCTURAL_DIFF_ONLY")

    def test_validate_findings_cli(self):
        with TemporaryDirectory() as folder:
            candidates = Path(folder)/"findings.json"
            candidates.write_text(json.dumps([
                {
                    "rule_id":"TEST-1",
                    "status":"SUSPECTED",
                    "subject":{"net":"UART_TX"},
                    "evidence":[{"kind":"netlist","net":"UART_TX"}]
                },
                {
                    "rule_id":"TEST-2",
                    "status":"SUSPECTED",
                    "subject":{"net":"MADE_UP_NET"},
                    "evidence":[]
                }
            ]))
            command = [
                sys.executable, "-m", "hardwarecheck",
                "validate-findings", "--netlist",
                str(BASE/"pstxnet.dat"), "--findings", str(candidates)
            ]
            result = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(len(payload["accepted"]), 1)
        self.assertEqual(len(payload["quarantined"]), 1)


if __name__ == "__main__":
    unittest.main()
