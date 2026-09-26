"""
Unit Tests for Evidence Record Schema & Serialization (Phase 1)
Validates evidence_record.schema.json and example_rcv_record.json.
"""

import json
import sys
import unittest
from pathlib import Path

agent_root = Path(__file__).resolve().parent.parent
if str(agent_root) not in sys.path:
    sys.path.insert(0, str(agent_root))

from core.models import EvidenceRecord
from pydantic import ValidationError


class TestEvidenceSchema(unittest.TestCase):
    def setUp(self):
        self.repo_root = agent_root.parent
        self.schema_path = self.repo_root / "contract" / "evidence_record.schema.json"
        self.example_path = self.repo_root / "contract" / "example_rcv_record.json"

    def test_schema_structure(self):
        self.assertTrue(self.schema_path.exists(), "Schema file must exist")
        with open(self.schema_path, "r", encoding="utf-8") as f:
            schema = json.load(f)

        self.assertEqual(schema.get("$schema"), "https://json-schema.org/draft/2020-12/schema")
        self.assertIn("required", schema)
        required_fields = [
            "record_id",
            "unit_id",
            "org_id",
            "operator_id",
            "captured_at",
            "po_header",
            "expected_values",
            "observed_values",
            "individual_checks",
            "final_verdict",
            "verdict_reason",
            "evidence_references",
        ]
        for field in required_fields:
            self.assertIn(field, schema["required"])

    def test_example_record_validity(self):
        self.assertTrue(self.example_path.exists(), "Example file must exist")
        with open(self.example_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Validate with Pydantic EvidenceRecord model
        record = EvidenceRecord.model_validate(data)
        self.assertEqual(record.record_id, "RCV-0005")
        self.assertEqual(record.unit_id, "UNIT-0005")
        self.assertEqual(record.final_verdict.value, "FAIL")
        self.assertEqual(record.individual_checks.quantity_check.verdict.value, "FAIL")
        self.assertEqual(record.individual_checks.identity_check.verdict.value, "PASS")
        self.assertEqual(record.individual_checks.quantity_check.discrepancy, -2)
        self.assertEqual(len(record.evidence_references), 2)

    def test_invalid_record_rejection(self):
        with open(self.example_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Corrupt the record: missing PO header
        corrupted = data.copy()
        del corrupted["po_header"]
        with self.assertRaises(ValidationError):
            EvidenceRecord.model_validate(corrupted)

        # Corrupt the record: invalid verdict
        corrupted2 = data.copy()
        corrupted2["final_verdict"] = "INVALID_VERDICT"
        with self.assertRaises(ValidationError):
            EvidenceRecord.model_validate(corrupted2)


if __name__ == "__main__":
    unittest.main()
