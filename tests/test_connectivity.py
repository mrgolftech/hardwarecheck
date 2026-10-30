"""Synthetic-only regression for Codex hardware-design-review 0-ohm tracing."""
import json
import subprocess
import sys
import unittest
from pathlib import Path

from hardwarecheck.cadence import build_design
from hardwarecheck.bom import parse_bom_csv
from hardwarecheck.connectivity import is_zero_ohm, trace_zero_ohm, zero_ohm_bridges

BASE = Path(__file__).parent / "fixtures"


class TraceZeroTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.design = build_design(BASE / "zero_ohm_net.dat", BASE / "zero_ohm_parts.dat")
        cls.bom = parse_bom_csv(BASE / "zero_ohm_bom.csv")

    def test_value_recognition(self):
        for value in ("0", "0R", "0R0", "0.0", "0 Ω", "0 Ohm", "000", "0OHMS"):
            self.assertTrue(is_zero_ohm(value), value)
        for value in ("10R", "10K", "", "JUMPER", "1R0", "0R1", "DNP"):
            self.assertFalse(is_zero_ohm(value), value)

    def test_assembly_state_separation(self):
        trace = trace_zero_ohm(self.design, "UART_TX", self.bom)
        confirmed = {p["net"] for p in trace["confirmed_reachable"]}
        possible = {p["net"] for p in trace["possible_reachable"]}
        self.assertEqual(confirmed, {"UART_LINK", "FITTED_OUT"})
        self.assertEqual(possible, {"UART_LINK", "SBUS_OUT", "UNKNOWN_OUT", "FITTED_OUT"})
        self.assertNotIn("DNP_OUT", possible)
        self.assertNotIn("CONFLICT_RESISTANCE", possible)
        self.assertNotIn("CONFLICT_POPULATION", possible)
        self.assertNotIn("NON_ZERO_OUT", possible)
        self.assertNotIn("UART_TX", possible)

    def test_evidence_and_paths(self):
        trace = trace_zero_ohm(self.design, "UART_TX", self.bom)
        by_ref = {b["refdes"]: b for b in trace["bridges"]}
        self.assertEqual(by_ref["R10"]["population"], "explicit_fitted")
        self.assertEqual(by_ref["R11"]["population"], "assumed_fitted")
        self.assertEqual(by_ref["R13"]["population"], "unknown")
        self.assertEqual(by_ref["R15"]["population"], "explicit_fitted")
        self.assertEqual(by_ref["R10"]["bom_row"], 3)
        sbus = next(p for p in trace["possible_reachable"] if p["net"] == "SBUS_OUT")
        self.assertEqual([s["refdes"] for s in sbus["path"]], ["R10", "R11"])
        self.assertEqual(sbus["hops"], 2)

    def test_dnp_conflict_and_same_net_exclusion(self):
        res = zero_ohm_bridges(self.design, self.bom)
        exclusions = {x["refdes"]: x["reason"] for x in res["excluded"]}
        self.assertEqual(exclusions["R12"], "not_fitted")
        self.assertEqual(exclusions["R14"], "resistance_value_conflict")
        self.assertEqual(exclusions["R16"], "population_conflict")
        self.assertEqual(exclusions["R17"], "not_two_distinct_pin_nets")

    def test_without_bom_never_assert_confirmed_connection(self):
        trace = trace_zero_ohm(self.design, "UART_TX")
        self.assertEqual(trace["confirmed_reachable"], [])
        self.assertIn("SBUS_OUT", {p["net"] for p in trace["possible_reachable"]})

    def test_unknown_net_fails_closed(self):
        with self.assertRaises(KeyError):
            trace_zero_ohm(self.design, "DOES_NOT_EXIST", self.bom)

    def test_cli_and_skill_discovery(self):
        cmd = [
            sys.executable, "-m", "hardwarecheck", "trace-zero",
            "--netlist", str(BASE / "zero_ohm_net.dat"),
            "--parts", str(BASE / "zero_ohm_parts.dat"),
            "--bom", str(BASE / "zero_ohm_bom.csv"), "--net", "UART_TX",
        ]
        p = subprocess.run(cmd, text=True, capture_output=True, check=False)
        self.assertEqual(p.returncode, 0, p.stderr)
        output = json.loads(p.stdout)
        self.assertEqual(output["start_net"], "UART_TX")
        self.assertEqual(len(output["confirmed_reachable"]), 2)
        skill = BASE.parent.parent / ".agents/skills/hardware-design-review/SKILL.md"
        doc = skill.read_text(encoding="utf-8")
        self.assertTrue(doc.startswith("---\nname: hardware-design-review\n"))
        self.assertIn("description:", doc)
        self.assertIn("trace-zero", doc)


if __name__ == "__main__":
    unittest.main()
