#!/usr/bin/env python
"""
CUBE Buildathon RCV#1 ? Demonstration Scenario Seeder
Phase 6: Seeds all 4 official demonstration scenarios into the active backend service.

Scenarios:
1. Scenario 1 (Clean Pass):           DEMO-PASS-001      -> PASS
2. Scenario 2 (Shortage & Damage):     DEMO-FAIL-001      -> FAIL (22 vs 24 qty, crushing)
3. Scenario 3 (Ambiguous Evidence):    DEMO-UNCERTAIN-001 -> UNCERTAIN (low clarity, unreadable SKU)
4. Scenario 4 (Simulated Timeout):     DEMO-PENDING-001   -> PENDING_REVIEW (fail-open provider outage)

DISCLAIMER:
- DEMO SCENARIOS ONLY for jury presentation and UI walkthrough.
- NOT part of the independent held-out evaluation dataset (agent/eval/).
- Zero model precision, recall, or accuracy metrics are claimed by this script.
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request

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
        print(f"Connection Error: {e.reason}. Please make sure the FastAPI backend is running on {API_BASE}.", file=sys.stderr)
        raise


def run():
    parser = argparse.ArgumentParser(description="Seed or reset CUBE Receiving Manager demo scenarios.")
    parser.add_argument("--reset", action="store_true", help="Clear all in-memory demo records before seeding.")
    parser.add_argument("--org", default="org_demo_alpha", help="Tenant organization ID (default: org_demo_alpha)")
    args = parser.parse_args()

    print("=" * 72)
    print("CUBE RECEIVING MANAGER -- PHASE 6 DEMO SCENARIO SEEDER")
    print(f"Target API: {API_BASE} | Tenant: {args.org}")
    print("=" * 72)

    # 1. Health check
    try:
        health = make_request("/health")
        print(f"[✓] Backend Service Connected: {health.get('service')} (status: {health.get('status')})")
    except Exception:
        sys.exit(1)

    # 2. Reset if requested
    if args.reset:
        try:
            res = make_request("/api/v1/demo/reset", method="POST")
            print(f"[✓] Repository Reset: {res.get('message')}")
        except Exception:
            print("[!] Note: Could not reset via /demo/reset endpoint.")

    # 3. Seed scenarios via /api/v1/demo/seed
    print("\nSeeding 4 Official CUBE Demonstration Scenarios...")
    try:
        seed_result = make_request("/api/v1/demo/seed", method="POST", org_id=args.org)
        print(f"[✓] {seed_result.get('message')}\n")

        print(f"{'Scenario':<35} | {'Inspection ID':<18} | {'Unit ID':<18} | {'Verdict'}")
        print("-" * 82)
        for s in seed_result.get("scenarios", []):
            print(f"{s['scenario']:<35} | {s['inspection_id']:<18} | {s['unit_id']:<18} | {s['verdict']}")

        print("-" * 82)
        print("\nAll 4 scenarios staged and verified:")
        print("  1. Scenario 1 -> PASS (Matched PO)")
        print("  2. Scenario 2 -> FAIL (Short shipment: 22 observed vs 24 ordered, carton crushed)")
        print("  3. Scenario 3 -> UNCERTAIN (Ambiguous evidence, unreadable barcode)")
        print("  4. Scenario 4 -> PENDING_REVIEW (Simulated vision timeout, fail-open active)")
        print("\nOpen frontend at http://localhost:5173 to inspect records and demonstrate operator override.")
    except Exception as e:
        print(f"[X] Failed to seed scenarios: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    run()
