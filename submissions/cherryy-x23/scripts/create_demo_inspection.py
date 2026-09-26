"""
Demo Helper Script for CUBE Receiving Manager (Pod 01)
Phase 5: Seeds demonstration inspection records into the in-memory backend service.

EXPLICIT DISCLAIMER:
- This script generates DEMONSTRATION data only for UI and workflow demonstration.
- This data is strictly ISOLATED from the held-out evaluation dataset (agent/eval/).
- Zero real accuracy, precision, or recall metrics are claimed or affected by this script.
"""

import json
import os
import sys
import urllib.request
import urllib.error

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")


def make_request(endpoint: str, method: str = "GET", data: dict = None, org_id: str = "org_demo_alpha"):
    url = f"{API_BASE}{endpoint}"
    headers = {
        "Content-Type": "application/json",
        "X-Org-ID": org_id,
    }
    body = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code}: {e.read().decode('utf-8')}", file=sys.stderr)
        raise
    except urllib.error.URLError as e:
        print(f"Connection Error: {e.reason}. Please make sure the FastAPI backend is running.", file=sys.stderr)
        raise


def seed_demo():
    print("=" * 65)
    print("CUBE RECEIVING MANAGER -- DEMO INSPECTION SEEDER")
    print("NOTICE: Creates session demonstration records only.")
    print("=" * 65)

    # 1. Health check
    try:
        health = make_request("/health")
        print(f"[✓] Backend connected: {health.get('service')} (status: {health.get('status')})")
    except Exception:
        sys.exit(1)

    # 2. Create Demo Inspection 1 (Clean match / PASS)
    demo_pass = {
        "org_id": "org_demo_alpha",
        "unit_id": "UNIT-DEMO-PASS",
        "operator_id": "operator-001",
        "po_number": "PO-1001",
        "po_line": 1,
        "supplier": "Premier Warehousing Supplies",
        "expected": {
            "sku": "BLUE-BOTTLE-001",
            "asin": "B000DEMO",
            "product_title": "Blue Water Bottle 750ml",
            "spec_colour": "blue",
            "spec_variant": "standard",
            "spec_components": ["bottle", "cap"],
            "cartons_ordered": 2,
            "units_per_carton_ordered": 12,
            "qty_ordered": 24,
        },
        "photo_references": [
            "fixtures/unit-001/photo-01.jpg",
            "fixtures/unit-001/photo-02.jpg",
        ],
    }

    res1 = make_request("/api/v1/inspections", method="POST", data=demo_pass, org_id="org_demo_alpha")
    insp_id_1 = res1["inspection_id"]
    print(f"[+] Created staged inspection: {insp_id_1} (unit: UNIT-DEMO-PASS)")

    # Run inspection 1 with mock provider
    run1 = make_request(f"/api/v1/inspections/{insp_id_1}/run?org_id=org_demo_alpha", method="POST")
    print(f"[✓] Executed Receiving Agent on {insp_id_1} -> Verdict: {run1['verdict']}")

    # 3. Create Demo Inspection 2 (Staged / Ready for Manual Run)
    demo_staged = {
        "org_id": "org_demo_alpha",
        "unit_id": "UNIT-DEMO-STAGED",
        "operator_id": "operator-002",
        "po_number": "PO-1002",
        "po_line": 1,
        "supplier": "Hydration Goods Co.",
        "expected": {
            "sku": "GREEN-TUMBLER-002",
            "asin": "B000TUMB",
            "product_title": "Green Stainless Steel Tumbler",
            "spec_colour": "green",
            "spec_variant": "vacuum-insulated",
            "spec_components": ["tumbler", "lid", "straw"],
            "cartons_ordered": 4,
            "units_per_carton_ordered": 10,
            "qty_ordered": 40,
        },
        "photo_references": [
            "fixtures/unit-002/pallet.jpg",
            "fixtures/unit-002/carton.jpg",
        ],
    }

    res2 = make_request("/api/v1/inspections", method="POST", data=demo_staged, org_id="org_demo_alpha")
    insp_id_2 = res2["inspection_id"]
    print(f"[+] Created staged inspection: {insp_id_2} (unit: UNIT-DEMO-STAGED, ready to run in UI)")

    print("\n" + "=" * 65)
    print("DEMO SEED COMPLETE")
    print(f"Open the frontend at http://localhost:5173 to review and run inspections.")
    print("=" * 65)


if __name__ == "__main__":
    seed_demo()
