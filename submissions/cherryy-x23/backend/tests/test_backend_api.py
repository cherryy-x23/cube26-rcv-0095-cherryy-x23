"""
Backend API Unit and Integration Tests for CUBE Receiving Manager (Pod 01)
Phase 4: Tests all endpoints, tenant isolation, fail-open behavior, and operator overrides.
"""

import os
import sys
import unittest
from pathlib import Path

# Configure paths
backend_dir = Path(__file__).resolve().parent.parent
agent_dir = backend_dir.parent / "agent"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))
if str(agent_dir) not in sys.path:
    sys.path.insert(0, str(agent_dir))

from fastapi.testclient import TestClient
from app.main import app
from app.api.inspections import get_inspection_service
from app.services.repository import get_repository
from app.services.inspection_service import InspectionService
from core.models import DamageType, VisualObservation
from core.vision_extractor import MockVisionExtractor


class TestBackendAPI(unittest.TestCase):
    def setUp(self):
        self.repo = get_repository()
        self.repo.clear()
        app.dependency_overrides.clear()
        self.client = TestClient(app)

        self.sample_payload = {
            "org_id": "org_demo_alpha",
            "unit_id": "UNIT-DEMO-001",
            "operator_id": "operator-001",
            "po_number": "PO-1001",
            "po_line": 1,
            "supplier": "Demo Supplier",
            "expected": {
                "sku": "BLUE-BOTTLE-001",
                "asin": "B000DEMO",
                "product_title": "Blue Water Bottle",
                "spec_colour": "blue",
                "spec_variant": "standard",
                "spec_components": ["bottle", "cap"],
                "cartons_ordered": 2,
                "units_per_carton_ordered": 12,
                "qty_ordered": 24,
            },
            "photo_references": [
                "fixtures/unit-001/pallet.jpg",
                "fixtures/unit-001/carton.jpg",
                "fixtures/unit-001/unit.jpg",
            ],
        }

    def tearDown(self):
        app.dependency_overrides.clear()

    # Test 1: Health endpoint works
    def test_01_health_endpoint(self):
        res = self.client.get("/health")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["service"], "cube-receiving-manager")

    # Test 2: Create inspection
    def test_02_create_inspection(self):
        res = self.client.post("/api/v1/inspections", json=self.sample_payload)
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertTrue(data["inspection_id"].startswith("INSP-"))
        self.assertEqual(data["status"], "pending")
        self.assertEqual(data["org_id"], "org_demo_alpha")
        self.assertEqual(data["unit_id"], "UNIT-DEMO-001")

    # Test 3: Get inspection
    def test_03_get_inspection(self):
        create_res = self.client.post("/api/v1/inspections", json=self.sample_payload)
        iid = create_res.json()["inspection_id"]

        res = self.client.get(f"/api/v1/inspections/{iid}?org_id=org_demo_alpha")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["inspection_id"], iid)
        self.assertEqual(data["status"], "pending")
        self.assertIsNone(data["verdict"])
        self.assertEqual(data["expected"]["sku"], "BLUE-BOTTLE-001")

    # Test 4: Run inspection using mock provider
    def test_04_run_inspection_mock_provider(self):
        create_res = self.client.post("/api/v1/inspections", json=self.sample_payload)
        iid = create_res.json()["inspection_id"]

        run_res = self.client.post(f"/api/v1/inspections/{iid}/run?org_id=org_demo_alpha")
        self.assertEqual(run_res.status_code, 200)
        data = run_res.json()
        self.assertEqual(data["inspection_id"], iid)
        self.assertEqual(data["status"], "completed")
        self.assertIn("evidence_record", data)

    # Test 5: Successful inspection returns expected deterministic result
    def test_05_successful_deterministic_pass(self):
        create_res = self.client.post("/api/v1/inspections", json=self.sample_payload)
        iid = create_res.json()["inspection_id"]

        obs = VisualObservation(
            identified_sku="BLUE-BOTTLE-001",
            barcode="B000DEMO",
            cartons_counted=2,
            units_per_carton_counted=12,
            quantity_counted=24,
            carton_damage=DamageType.NONE,
            unit_damage=DamageType.NONE,
            observed_colour="blue",
            observed_variant="standard",
            observed_components=["bottle", "cap"],
            image_clarity=0.99,
        )
        custom_service = InspectionService(extractor=MockVisionExtractor(preset_observation=obs))
        app.dependency_overrides[get_inspection_service] = lambda: custom_service

        run_res = self.client.post(f"/api/v1/inspections/{iid}/run?org_id=org_demo_alpha")
        self.assertEqual(run_res.status_code, 200)
        data = run_res.json()
        self.assertEqual(data["verdict"], "PASS")
        self.assertEqual(data["status"], "completed")

        # Verify through GET
        get_res = self.client.get(f"/api/v1/inspections/{iid}?org_id=org_demo_alpha")
        self.assertEqual(get_res.json()["verdict"], "PASS")

    # Test 6: Vision provider timeout results in PENDING_REVIEW and does not crash
    def test_06_provider_timeout_fails_open(self):
        create_res = self.client.post("/api/v1/inspections", json=self.sample_payload)
        iid = create_res.json()["inspection_id"]

        timeout_extractor = MockVisionExtractor(simulate_timeout=True, error_message="Vision API timeout >30000ms")
        custom_service = InspectionService(extractor=timeout_extractor)
        app.dependency_overrides[get_inspection_service] = lambda: custom_service

        run_res = self.client.post(f"/api/v1/inspections/{iid}/run?org_id=org_demo_alpha")
        self.assertEqual(run_res.status_code, 200)
        data = run_res.json()
        self.assertEqual(data["status"], "pending_review")
        self.assertEqual(data["verdict"], "PENDING_REVIEW")
        self.assertIn("review required", data["message"].lower())

    # Test 7: Invalid vision response results in PENDING_REVIEW
    def test_07_invalid_vision_response_fails_open(self):
        create_res = self.client.post("/api/v1/inspections", json=self.sample_payload)
        iid = create_res.json()["inspection_id"]

        invalid_extractor = MockVisionExtractor(simulate_invalid_json=True)
        custom_service = InspectionService(extractor=invalid_extractor)
        app.dependency_overrides[get_inspection_service] = lambda: custom_service

        run_res = self.client.post(f"/api/v1/inspections/{iid}/run?org_id=org_demo_alpha")
        self.assertEqual(run_res.status_code, 200)
        data = run_res.json()
        self.assertEqual(data["status"], "pending_review")
        self.assertEqual(data["verdict"], "PENDING_REVIEW")

    # Test 8: Cross-tenant GET is denied (404 Not Found)
    def test_08_cross_tenant_get_denied(self):
        create_res = self.client.post("/api/v1/inspections", json=self.sample_payload)
        iid = create_res.json()["inspection_id"]

        # Attempt to access alpha's record as bravo
        res = self.client.get(f"/api/v1/inspections/{iid}?org_id=org_demo_bravo")
        self.assertEqual(res.status_code, 404)
        self.assertEqual(res.json()["detail"], "Inspection not found")

    # Test 9: Cross-tenant RUN is denied (404 Not Found)
    def test_09_cross_tenant_run_denied(self):
        create_res = self.client.post("/api/v1/inspections", json=self.sample_payload)
        iid = create_res.json()["inspection_id"]

        res = self.client.post(f"/api/v1/inspections/{iid}/run?org_id=org_demo_bravo")
        self.assertEqual(res.status_code, 404)
        self.assertEqual(res.json()["detail"], "Inspection not found")

    # Test 10: Cross-tenant OVERRIDE is denied (404 Not Found)
    def test_10_cross_tenant_override_denied(self):
        create_res = self.client.post("/api/v1/inspections", json=self.sample_payload)
        iid = create_res.json()["inspection_id"]

        override_payload = {
            "operator_id": "operator-attacker",
            "override_verdict": "PASS",
            "reason": "Unauthorized cross tenant override attempt",
        }
        res = self.client.post(f"/api/v1/inspections/{iid}/override?org_id=org_demo_bravo", json=override_payload)
        self.assertEqual(res.status_code, 404)
        self.assertEqual(res.json()["detail"], "Inspection not found")

    # Test 11: Organization list only returns requesting organization's records
    def test_11_organization_list_isolation(self):
        # Create 2 records for alpha
        self.client.post("/api/v1/inspections", json=self.sample_payload)
        payload_alpha_2 = self.sample_payload.copy()
        payload_alpha_2["unit_id"] = "UNIT-DEMO-002"
        self.client.post("/api/v1/inspections", json=payload_alpha_2)

        # Create 1 record for bravo
        payload_bravo = self.sample_payload.copy()
        payload_bravo["org_id"] = "org_demo_bravo"
        payload_bravo["unit_id"] = "UNIT-BRAVO-001"
        self.client.post("/api/v1/inspections", json=payload_bravo)

        # Alpha queries list
        res_alpha = self.client.get("/api/v1/inspections?org_id=org_demo_alpha")
        self.assertEqual(res_alpha.status_code, 200)
        self.assertEqual(len(res_alpha.json()), 2)
        for item in res_alpha.json():
            self.assertEqual(item["org_id"], "org_demo_alpha")

        # Bravo queries list
        res_bravo = self.client.get("/api/v1/inspections?org_id=org_demo_bravo")
        self.assertEqual(res_bravo.status_code, 200)
        self.assertEqual(len(res_bravo.json()), 1)
        self.assertEqual(res_bravo.json()[0]["org_id"], "org_demo_bravo")

    # Test 12: Operator override preserves original verdict
    def test_12_operator_override_preserves_original_verdict(self):
        create_res = self.client.post("/api/v1/inspections", json=self.sample_payload)
        iid = create_res.json()["inspection_id"]

        # Run with short quantity -> original verdict is FAIL
        short_obs = VisualObservation(
            identified_sku="BLUE-BOTTLE-001",
            cartons_counted=2,
            units_per_carton_counted=10,  # 20 instead of 24
            quantity_counted=20,
            carton_damage=DamageType.NONE,
            unit_damage=DamageType.NONE,
        )
        custom_service = InspectionService(extractor=MockVisionExtractor(preset_observation=short_obs))
        app.dependency_overrides[get_inspection_service] = lambda: custom_service

        run_res = self.client.post(f"/api/v1/inspections/{iid}/run?org_id=org_demo_alpha")
        self.assertEqual(run_res.json()["verdict"], "FAIL")

        # Apply human override to PASS
        override_payload = {
            "operator_id": "operator-002",
            "override_verdict": "PASS",
            "reason": "Physical count confirmed 4 additional promotional units bundled in carton 2.",
        }
        ov_res = self.client.post(f"/api/v1/inspections/{iid}/override?org_id=org_demo_alpha", json=override_payload)
        self.assertEqual(ov_res.status_code, 200)
        data = ov_res.json()
        self.assertEqual(data["original_verdict"], "FAIL")
        self.assertEqual(data["override_verdict"], "PASS")
        self.assertEqual(data["operator_id"], "operator-002")

        # Verify inspection state reflects both
        get_res = self.client.get(f"/api/v1/inspections/{iid}?org_id=org_demo_alpha")
        get_data = get_res.json()
        self.assertEqual(get_data["verdict"], "PASS")
        self.assertIsNotNone(get_data["operator_override"])
        self.assertEqual(get_data["operator_override"]["original_verdict"], "FAIL")
        self.assertEqual(get_data["operator_override"]["override_verdict"], "PASS")

    # Test 13: Override requires a non-empty reason
    def test_13_override_requires_reason(self):
        create_res = self.client.post("/api/v1/inspections", json=self.sample_payload)
        iid = create_res.json()["inspection_id"]

        invalid_override = {
            "operator_id": "operator-002",
            "override_verdict": "PASS",
            "reason": "",  # Empty reason rejected
        }
        res = self.client.post(f"/api/v1/inspections/{iid}/override?org_id=org_demo_alpha", json=invalid_override)
        self.assertEqual(res.status_code, 422)

    # Test 14: Invalid override verdict is rejected (PENDING_REVIEW rejected)
    def test_14_invalid_override_verdict_rejected(self):
        create_res = self.client.post("/api/v1/inspections", json=self.sample_payload)
        iid = create_res.json()["inspection_id"]

        invalid_override = {
            "operator_id": "operator-002",
            "override_verdict": "PENDING_REVIEW",  # Must be PASS, FAIL, or UNCERTAIN
            "reason": "Attempting to reset to pending review",
        }
        res = self.client.post(f"/api/v1/inspections/{iid}/override?org_id=org_demo_alpha", json=invalid_override)
        self.assertEqual(res.status_code, 422)

    # Test 15: Photo references remain preserved in inspection and evidence record
    def test_15_photo_references_preserved(self):
        create_res = self.client.post("/api/v1/inspections", json=self.sample_payload)
        iid = create_res.json()["inspection_id"]

        self.client.post(f"/api/v1/inspections/{iid}/run?org_id=org_demo_alpha")
        get_res = self.client.get(f"/api/v1/inspections/{iid}?org_id=org_demo_alpha")
        data = get_res.json()

        self.assertEqual(len(data["photo_references"]), 3)
        self.assertIn("fixtures/unit-001/pallet.jpg", data["photo_references"])
        evidence = data.get("evidence_record")
        self.assertIsNotNone(evidence)
        self.assertGreaterEqual(len(evidence.get("evidence_references", [])), 1)

    # Test 16: Demo seed and reset endpoints work
    def test_16_demo_seed_and_reset(self):
        seed_res = self.client.post("/api/v1/demo/seed")
        self.assertEqual(seed_res.status_code, 201)
        data = seed_res.json()
        self.assertEqual(len(data["scenarios"]), 4)

        # Check repository has 4 inspections for org_demo_alpha
        list_res = self.client.get("/api/v1/inspections?org_id=org_demo_alpha")
        self.assertEqual(len(list_res.json()), 4)

        # Reset repository
        reset_res = self.client.post("/api/v1/demo/reset")
        self.assertEqual(reset_res.status_code, 200)

        # Verify repository is cleared
        list_after = self.client.get("/api/v1/inspections?org_id=org_demo_alpha")
        self.assertEqual(len(list_after.json()), 0)

    # Test 17: Demo scenarios produce all 4 required verdicts deterministically
    def test_17_demo_scenarios_all_verdicts(self):
        seed_res = self.client.post("/api/v1/demo/seed")
        self.assertEqual(seed_res.status_code, 201)
        scenarios = {s["unit_id"]: s for s in seed_res.json()["scenarios"]}

        # 1. PASS
        self.assertEqual(scenarios["DEMO-PASS-001"]["verdict"], "PASS")

        # 2. FAIL
        self.assertEqual(scenarios["DEMO-FAIL-001"]["verdict"], "FAIL")
        fail_insp = self.client.get(f"/api/v1/inspections/{scenarios['DEMO-FAIL-001']['inspection_id']}?org_id=org_demo_alpha").json()
        ind_checks = fail_insp["evidence_record"]["individual_checks"]
        self.assertEqual(ind_checks["quantity_check"]["verdict"], "FAIL")
        self.assertEqual(ind_checks["quantity_check"]["discrepancy"], -2)
        self.assertEqual(ind_checks["carton_condition_check"]["verdict"], "FAIL")

        # 3. UNCERTAIN
        self.assertEqual(scenarios["DEMO-UNCERTAIN-001"]["verdict"], "UNCERTAIN")

        # 4. PENDING_REVIEW (fail-open)
        self.assertEqual(scenarios["DEMO-PENDING-001"]["verdict"], "PENDING_REVIEW")
        self.assertEqual(scenarios["DEMO-PENDING-001"]["status"], "pending_review")

    # Test 18: CORS headers properly configured for http://localhost:5174 and local Vite origins
    def test_18_cors_headers_localhost_5174(self):
        # 1. GET /health with Origin: http://localhost:5174
        health_res = self.client.get("/health", headers={"Origin": "http://localhost:5174"})
        self.assertEqual(health_res.status_code, 200)
        self.assertEqual(health_res.headers.get("access-control-allow-origin"), "http://localhost:5174")

        # 2. Preflight OPTIONS request for inspections with X-Org-ID and Content-Type
        options_res = self.client.options(
            "/api/v1/inspections?org_id=org_demo_alpha",
            headers={
                "Origin": "http://localhost:5174",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "content-type, x-org-id",
            },
        )
        self.assertEqual(options_res.status_code, 200)
        self.assertEqual(options_res.headers.get("access-control-allow-origin"), "http://localhost:5174")
        allowed_methods = options_res.headers.get("access-control-allow-methods", "")
        self.assertIn("GET", allowed_methods)

        # 3. GET /api/v1/inspections?org_id=org_demo_alpha from http://localhost:5174
        insp_res = self.client.get(
            "/api/v1/inspections?org_id=org_demo_alpha",
            headers={"Origin": "http://localhost:5174", "X-Org-ID": "org_demo_alpha"},
        )
        self.assertEqual(insp_res.status_code, 200)
        self.assertEqual(insp_res.headers.get("access-control-allow-origin"), "http://localhost:5174")

        # 4. Disallowed origin does NOT receive Access-Control-Allow-Origin
        untrusted_res = self.client.get("/health", headers={"Origin": "http://malicious-untrusted-site.com"})
        self.assertIsNone(untrusted_res.headers.get("access-control-allow-origin"))


if __name__ == "__main__":
    unittest.main()

