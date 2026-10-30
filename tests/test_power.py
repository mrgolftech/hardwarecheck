"""V0.4 power tree synthetic tests: graph is annotated, never guessed."""
import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path

from hardwarecheck.cadence import build_design
from hardwarecheck.power import analyze_power_tree

BASE = Path(__file__).parent / "fixtures"


class PowerTreeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.design = build_design(BASE / "power_tree_net.dat", BASE / "power_tree_parts.dat")
        cls.spec = json.loads((BASE / "power_tree_spec.json").read_text(encoding="utf-8"))

    def test_no_manifest_candidates_not_verified_tree(self):
        data = analyze_power_tree(self.design)
        self.assertEqual(data["mode"], "candidate_only")
        self.assertEqual(data["converters"], [])
        self.assertIn("VDD_3V3", {x["net"] for x in data["candidate_rails"]})
        self.assertNotIn("GND", {x["net"] for x in data["candidate_rails"]})

    def test_declared_multilevel_tree(self):
        data = analyze_power_tree(self.design, self.spec)
        self.assertEqual(data["annotation_errors"], [])
        self.assertEqual(data["findings"], [])
        self.assertEqual(
            [(x["input_net"], x["output_net"]) for x in data["converters"]],
            [("+12V", "+5V"), ("+5V", "VDD_3V3"), ("VDD_3V3", "VDD_1V8")]
        )
        rails = {x["net"]: x for x in data["rails"]}
        self.assertAlmostEqual(rails["VDD_3V3"]["declared_direct_load_current_sum_a"], .4)
        self.assertIn("U3", rails["VDD_3V3"]["downstream_converter_inputs_unbudgeted"])
        self.assertEqual(rails["VDD_1V8"]["declared_voltage_v"], 1.8)

    def test_budget_over_limit_suspected(self):
        spec = copy.deepcopy(self.spec)
        spec["loads"][0]["max_current_a"] = 1.5
        out = analyze_power_tree(self.design, spec)
        self.assertIn("PWR-CURRENT-001", [x["check_id"] for x in out["findings"]])

    def test_voltage_and_dropout_checks(self):
        spec = copy.deepcopy(self.spec)
        spec["converters"][2]["min_input_v"] = 3.6
        spec["converters"][2]["kind"] = "LDO"
        spec["converters"][2]["dropout_v"] = 2.0
        spec["loads"][1]["max_voltage_v"] = 1.7
        out = analyze_power_tree(self.design, spec)
        ids = {x["check_id"] for x in out["findings"]}
        self.assertTrue({"PWR-VIN-001", "PWR-LDO-001", "PWR-LOAD-001"} <= ids)

    def test_invalid_mapping_is_not_converted_into_fake_edge(self):
        spec = copy.deepcopy(self.spec)
        spec["converters"][0]["output_pin"] = "999"
        out = analyze_power_tree(self.design, spec)
        self.assertEqual(len(out["converters"]), 2)
        self.assertTrue(any("pin 999" in e for e in out["annotation_errors"]))

    def test_invalid_schema_and_numeric(self):
        with self.assertRaises(ValueError):
            analyze_power_tree(self.design, {"schema_version": "2"})
        bad = copy.deepcopy(self.spec)
        bad["loads"][0]["max_current_a"] = "1.5"
        res = analyze_power_tree(self.design, bad)
        self.assertTrue(res["annotation_errors"])
        self.assertTrue(all(x["status"] == "SUSPECTED" for x in res["findings"]))

    def test_duplicate_source_and_cycle(self):
        bad = copy.deepcopy(self.spec)
        bad["sources"].append({"net": "+12V", "voltage_v": 11.0})
        bad["converters"].append({
            "refdes": "U6", "input_pin": "1", "output_pin": "2",
            "output_voltage_v": 12.0
        })
        res = analyze_power_tree(self.design, bad)
        self.assertIn("PWR-VOLT-001", [x["check_id"] for x in res["findings"]])
        self.assertIn("PWR-CYCLE-001", [x["check_id"] for x in res["findings"]])

    def test_cli_power_tree_and_checklist(self):
        cmd = [sys.executable, "-m", "hardwarecheck", "power-tree", "--netlist",
               str(BASE / "power_tree_net.dat"), "--parts", str(BASE / "power_tree_parts.dat"),
               "--power-spec", str(BASE / "power_tree_spec.json")]
        r = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(json.loads(r.stdout)["mode"], "annotated_power_tree")
        r = subprocess.run([sys.executable, "-m", "hardwarecheck", "checklist",
                            "--category", "POWER"], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        data = json.loads(r.stdout)
        self.assertGreaterEqual(data["count"], 20)
        self.assertTrue(all(x["category"] == "POWER" for x in data["checks"]))


if __name__ == "__main__":
    unittest.main()
