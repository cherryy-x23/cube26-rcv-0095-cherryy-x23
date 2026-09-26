"""
Command-Line Interface for CUBE Receiving Manager (Pod 01)
Phase 2: Headless Inbound Receiving Inspection Runner.

Commands:
- inspect: Execute physical shipment inspection using vision AI + deterministic comparison engine.
- verify-observation: Verify structured observation deterministically against PO data.
- validate-record: Validate an Evidence Record JSON against the official schema.
"""

import argparse
import json
import os
import sys
from pathlib import Path

agent_root = Path(__file__).resolve().parent
if str(agent_root) not in sys.path:
    sys.path.insert(0, str(agent_root))

from core.models import (
    EvidenceRecord,
    POExpected,
    POHeader,
    ViewType,
    VisualObservation,
)
from core.comparison_engine import evaluate_all_checks
from core.vision_extractor import (
    GeminiVisionExtractor,
    MockVisionExtractor,
)
from core.agent import ReceivingAgent


def inspect_command(args):
    """
    Executes headless receiving inspection on shipment images.
    """
    po_path = Path(args.po)
    if not po_path.exists():
        print(f"Error: PO file not found at {po_path}", file=sys.stderr)
        sys.exit(1)

    with open(po_path, "r", encoding="utf-8") as f:
        po_raw = json.load(f)

    # Support PO JSON containing either direct expected fields or full PO document structure
    if "expected_values" in po_raw:
        expected = POExpected.model_validate(po_raw["expected_values"])
        header_data = po_raw.get("po_header", {})
        po_header = POHeader(
            po_number=header_data.get("po_number", "PO-AUTO"),
            po_line=header_data.get("po_line", 1),
            supplier=header_data.get("supplier", "Supplier East (DUMMY)"),
        )
    else:
        expected = POExpected.model_validate(po_raw)
        po_header = POHeader(
            po_number=po_raw.get("po_number", "PO-AUTO"),
            po_line=po_raw.get("po_line", 1),
            supplier=po_raw.get("supplier", "Supplier East (DUMMY)"),
        )

    # Collect images
    images = {}
    if args.images:
        img_dir = Path(args.images)
        if img_dir.exists() and img_dir.is_dir():
            for f in img_dir.iterdir():
                fn_lower = f.name.lower()
                if "pallet" in fn_lower:
                    images[ViewType.PALLET] = str(f)
                elif "carton" in fn_lower:
                    images[ViewType.CARTON] = str(f)
                elif "unit" in fn_lower:
                    images[ViewType.UNIT] = str(f)
                elif "barcode" in fn_lower or "label" in fn_lower:
                    images[ViewType.BARCODE] = str(f)
    if args.pallet:
        images[ViewType.PALLET] = args.pallet
    if args.carton:
        images[ViewType.CARTON] = args.carton
    if args.unit:
        images[ViewType.UNIT] = args.unit
    if args.barcode:
        images[ViewType.BARCODE] = args.barcode

    if not images:
        images[ViewType.OVERVIEW] = "placeholder_overview.jpg"

    provider = args.provider.lower()

    # Honesty Check: Do not fabricate live inspections if provider is not configured
    if provider == "gemini":
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("=" * 60)
            print("VISION PROVIDER NOT CONFIGURED")
            print("=" * 60)
            print("Inspection cannot be completed because no real vision provider")
            print("is configured (GEMINI_API_KEY environment variable is not set).")
            print()
            print("No fabricated PASS/FAIL result was generated.")
            print("To run in deterministic test fixture mode, pass: --provider mock")
            print("=" * 60)
            sys.exit(1)
        extractor = GeminiVisionExtractor(api_key=api_key)
    elif provider == "mock":
        extractor = MockVisionExtractor()
    else:
        print(f"Error: Unknown provider '{provider}'", file=sys.stderr)
        sys.exit(1)

    agent = ReceivingAgent(extractor=extractor)
    unit_id = args.unit_id or "UNIT-0001"
    record_id = args.record_id or "RCV-0001"
    org_id = args.org_id or "org_demo_alpha"
    operator_id = args.operator_id or "op_cli"

    record: EvidenceRecord = agent.process_shipment(
        record_id=record_id,
        unit_id=unit_id,
        org_id=org_id,
        operator_id=operator_id,
        po_header=po_header,
        expected=expected,
        images=images,
    )

    print("=" * 60)
    print("CUBE RECEIVING MANAGER - INSPECTION RESULT")
    print("=" * 60)
    print(f"Record ID:      {record.record_id}")
    print(f"Unit ID:        {record.unit_id}")
    print(f"PO Line:        {record.po_header.po_number} line {record.po_header.po_line}")
    print(f"Provider:       {provider.upper()}")
    print("-" * 60)
    print(f"Identity Check: [{record.individual_checks.identity_check.verdict.value}] - {record.individual_checks.identity_check.reason}")
    print(f"Quantity Check: [{record.individual_checks.quantity_check.verdict.value}] - {record.individual_checks.quantity_check.reason}")
    print(f"Carton Damage:  [{record.individual_checks.carton_condition_check.verdict.value}] - {record.individual_checks.carton_condition_check.reason}")
    print(f"Unit Damage:    [{record.individual_checks.unit_condition_check.verdict.value}] - {record.individual_checks.unit_condition_check.reason}")
    print(f"Specification:  [{record.individual_checks.specification_check.verdict.value}] - {record.individual_checks.specification_check.reason}")
    print("-" * 60)
    print(f"FINAL VERDICT:  [{record.final_verdict.value}]")
    print(f"REASON:         {record.verdict_reason}")
    print(f"Evidence Files: {len(record.evidence_references)} photos hashed")
    print("=" * 60)

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(record.model_dump_json(indent=2))
        print(f"Saved Evidence Record to: {out_path}")


def verify_command(args):
    """
    Executes the pure deterministic comparison engine given expected PO data and an observation.
    """
    po_path = Path(args.po)
    obs_path = Path(args.observation)

    if not po_path.exists():
        print(f"Error: PO file not found at {po_path}", file=sys.stderr)
        sys.exit(1)
    if not obs_path.exists():
        print(f"Error: Observation file not found at {obs_path}", file=sys.stderr)
        sys.exit(1)

    with open(po_path, "r", encoding="utf-8") as f:
        po_data = json.load(f)
    with open(obs_path, "r", encoding="utf-8") as f:
        obs_data = json.load(f)

    expected = POExpected.model_validate(po_data)
    obs = VisualObservation.model_validate(obs_data)

    individual, final_verdict, reason = evaluate_all_checks(expected, obs)

    print("=" * 60)
    print("DETERMINISTIC VERIFICATION RESULTS")
    print("=" * 60)
    print(f"Identity Check:          [{individual.identity_check.verdict.value}] - {individual.identity_check.reason}")
    print(f"Quantity Check:          [{individual.quantity_check.verdict.value}] - {individual.quantity_check.reason}")
    print(f"Carton Condition Check:  [{individual.carton_condition_check.verdict.value}] - {individual.carton_condition_check.reason}")
    print(f"Unit Condition Check:    [{individual.unit_condition_check.verdict.value}] - {individual.unit_condition_check.reason}")
    print(f"Specification Check:     [{individual.specification_check.verdict.value}] - {individual.specification_check.reason}")
    print("-" * 60)
    print(f"FINAL VERDICT:           [{final_verdict.value}]")
    print(f"REASON:                  {reason}")
    print("=" * 60)


def validate_record_command(args):
    """
    Validates a generated Evidence Record JSON against the official Pydantic domain models.
    """
    record_path = Path(args.file)
    if not record_path.exists():
        print(f"Error: Record file not found at {record_path}", file=sys.stderr)
        sys.exit(1)

    with open(record_path, "r", encoding="utf-8") as f:
        record_data = json.load(f)

    try:
        record = EvidenceRecord.model_validate(record_data)
        print("SUCCESS: Record conforms to the official Evidence Record schema.")
        print(f"Record ID:     {record.record_id}")
        print(f"Unit ID:       {record.unit_id}")
        print(f"Final Verdict: {record.final_verdict.value}")
        print(f"Reason:        {record.verdict_reason}")
    except Exception as e:
        print(f"VALIDATION FAILED: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="CUBE Receiving Manager CLI (Phase 2 Headless Agent)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # inspect subcommand
    inspect_parser = subparsers.add_parser("inspect", help="Run receiving inspection on images")
    inspect_parser.add_argument("--po", required=True, help="Path to expected PO JSON file")
    inspect_parser.add_argument("--images", help="Path to directory containing shipment photos")
    inspect_parser.add_argument("--pallet", help="Path to pallet photo")
    inspect_parser.add_argument("--carton", help="Path to master carton photo")
    inspect_parser.add_argument("--unit", help="Path to retail unit photo")
    inspect_parser.add_argument("--barcode", help="Path to barcode/label photo")
    inspect_parser.add_argument("--provider", default="gemini", choices=["gemini", "mock"], help="Vision provider (default: gemini)")
    inspect_parser.add_argument("--unit-id", default="UNIT-0001", help="Unit ID (default: UNIT-0001)")
    inspect_parser.add_argument("--record-id", default="RCV-0001", help="Record ID (default: RCV-0001)")
    inspect_parser.add_argument("--org-id", default="org_demo_alpha", help="Tenant org ID")
    inspect_parser.add_argument("--operator-id", default="op_dock", help="Dock operator ID")
    inspect_parser.add_argument("--output", help="Output file path to save Evidence Record JSON")

    # verify subcommand
    verify_parser = subparsers.add_parser("verify-observation", help="Verify structured observation deterministically against PO")
    verify_parser.add_argument("--po", required=True, help="Path to expected PO JSON file")
    verify_parser.add_argument("--observation", required=True, help="Path to structured visual observation JSON file")

    # validate-record subcommand
    val_parser = subparsers.add_parser("validate-record", help="Validate an Evidence Record JSON against schema")
    val_parser.add_argument("--file", required=True, help="Path to evidence record JSON file")

    args = parser.parse_args()
    if args.command == "inspect":
        inspect_command(args)
    elif args.command == "verify-observation":
        verify_command(args)
    elif args.command == "validate-record":
        validate_record_command(args)


if __name__ == "__main__":
    main()
