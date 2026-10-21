"""Tests are synthetic and DO NOT validate real Cadence export compatibility."""
from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from hardwarecheck.cadence import build_design, get_component, get_net, parse_pstxnet
from hardwarecheck.bom import parse_bom_csv, compare_bom
from hardwarecheck.rules import run_rules
from hardwarecheck.report import validate_findings
from hardwarecheck.pcb import summarize_pcb

BASE = Path(__file__).parent / "fixtures"


class SyntheticNetlistTests(unittest.TestCase):
    def setUp(self):
        self.design = build_design(BASE/"pstxnet.dat", BASE/"pstxprt.dat")

    def test_connectivity(self):
        self.assertEqual(len(self.design["nets"]), 5)
        self.assertEqual(len(self.design["components"]), 5)
        self.assertEqual(self.design["components"]["U1"]["pins"]["5"], "+3V3")
        self.assertEqual(len(get_net(self.design, "GND")["pins"]), 5)
        self.assertEqual(get_component(self.design, "U2")["neighbors"]["2"]["net"], "UART_TX")
        self.assertEqual(self.design["components"]["U1"]["part_name"], "DEMO_LDO")

    def test_bom_inventory(self):
        diff = compare_bom(self.design, parse_bom_csv(BASE/"bom.csv"))
        self.assertEqual(diff["not_in_bom"], ["J2"])
        self.assertEqual(diff["not_in_netlist"], ["MH1"])

    def test_rule_status_and_evidence(self):
        checks = run_rules(self.design, parse_bom_csv(BASE/"bom.csv"))
        good = validate_findings(self.design, checks["findings"])
        self.assertEqual(good["quarantined"], [])
        statuses = {f["rule_id"]: f["status"] for f in good["accepted"]}
        self.assertEqual(statuses["SCH-NET-002"], "SUSPECTED")
        self.assertEqual(statuses["SCH-BOM-001"], "NEEDS_REVIEW")

    def test_unknown_object_fails(self):
        with self.assertRaises(KeyError):
            get_component(self.design, "U999")
        with self.assertRaises(KeyError):
            get_net(self.design, "NOT_A_NET")

    def test_conflicting_physical_pin(self):
        text = (BASE/"pstxnet.dat").read_text()
        text = text.replace("NODE_NAME J2 1", "NODE_NAME U1 1\n'@DEMO': 'VIN':;\nNODE_NAME J2 1")
        with TemporaryDirectory() as folder:
            path = Path(folder)/"pstxnet.dat"
            path.write_text(text)
            design = build_design(path)
        self.assertEqual(design["conflicts"][0]["refdes"], "U1")
        out = run_rules(design)
        self.assertTrue(any(x["rule_id"] == "SCH-NET-001" and x["status"] == "FAIL"
                            for x in out["findings"]))

    def test_reject_incomplete_netlist(self):
        with TemporaryDirectory() as folder:
            path = Path(folder)/"pstxnet.dat"
            path.write_text("NET_NAME\n'FOO';")
            with self.assertRaises(ValueError):
                parse_pstxnet(path)

    def test_quarantine_missing_net(self):
        fake = [{
            "rule_id": "CUSTOM-1", "status": "SUSPECTED",
            "subject": {"net": "INVENTED_NET"}, "evidence": []
        }]
        result = validate_findings(self.design, fake)
        self.assertEqual(len(result["accepted"]), 0)
        self.assertEqual(len(result["quarantined"]), 1)

    def test_pcb_inventory_only(self):
        for filename in ("pcb_sample.json", "pcb_sample.xml"):
            data = summarize_pcb(BASE/filename)
            self.assertEqual(data["capability"], "inventory_only")
        with TemporaryDirectory() as folder:
            path = Path(folder)/"native.brd"
            path.write_bytes(b"binary")
            with self.assertRaises(ValueError):
                summarize_pcb(path)

    def test_cli_smoke(self):
        command = [sys.executable, "-m", "hardwarecheck", "inspect",
                   "--netlist", str(BASE/"pstxnet.dat"),
                   "--parts", str(BASE/"pstxprt.dat")]
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["nets"], 5)
        self.assertEqual(payload["connected_pins"], 13)


if __name__ == "__main__":
    unittest.main()
