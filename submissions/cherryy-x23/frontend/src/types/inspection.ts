export type Verdict = 'PASS' | 'FAIL' | 'UNCERTAIN' | 'PENDING_REVIEW';
export type OverrideVerdict = 'PASS' | 'FAIL' | 'UNCERTAIN';
export type InspectionStatus = 'pending' | 'completed' | 'pending_review' | 'failed';

export interface ExpectedValues {
  sku: string;
  asin?: string | null;
  product_title?: string | null;
  spec_colour?: string | null;
  spec_variant?: string | null;
  spec_components?: string[] | null;
  cartons_ordered?: number | null;
  units_per_carton_ordered?: number | null;
  qty_ordered: number;
}

export interface PhotoReference {
  photo_id?: string;
  path: string;
  sha256?: string | null;
  notes?: string | null;
}

export interface OperatorOverride {
  original_verdict: Verdict;
  override_verdict: OverrideVerdict;
  operator_id: string;
  reason: string;
  timestamp: string;
}

export interface InspectionCheck {
  check_type: string;
  verdict: Verdict;
  expected_value?: string | null;
  observed_value?: string | null;
  discrepancy?: string | number | null;
  notes?: string | null;
}

export interface IndividualCheckResult {
  verdict: Verdict;
  reason: string;
  confidence?: number | null;
  discrepancy?: number | null;
  damage_type?: string | null;
  flagged_issues?: string[];
}

export interface IndividualChecks {
  identity_check?: IndividualCheckResult;
  quantity_check?: IndividualCheckResult;
  carton_condition_check?: IndividualCheckResult;
  unit_condition_check?: IndividualCheckResult;
  specification_check?: IndividualCheckResult;
}

export interface ObservedValues {
  identified_sku?: string | null;
  barcode?: string | null;
  cartons_counted?: number | null;
  units_per_carton_counted?: number | null;
  quantity_counted?: number | null;
  carton_damage?: string | null;
  unit_damage?: string | null;
  observed_colour?: string | null;
  observed_variant?: string | null;
  observed_components?: string[] | null;
  image_clarity?: number | null;
}

export interface EvidenceRecord {
  record_id?: string;
  rcv_number?: string;
  unit_id: string;
  timestamp?: string;
  captured_at?: string;
  checks?: InspectionCheck[];
  individual_checks?: IndividualChecks;
  observed_values?: ObservedValues;
  final_verdict: Verdict;
  verdict_reason?: string;
  overall_notes?: string | null;
  photos?: PhotoReference[];
  evidence_references?: any[];
}

export interface Inspection {
  inspection_id: string;
  org_id: string;
  unit_id: string;
  operator_id: string;
  po_number: string;
  po_line: number;
  supplier: string;
  expected: ExpectedValues;
  photo_references: PhotoReference[];
  status: InspectionStatus;
  verdict?: Verdict | null;
  evidence_record?: EvidenceRecord | null;
  operator_override?: OperatorOverride | null;
  created_at: string;
  updated_at: string;
}

export interface InspectionCreatePayload {
  org_id: string;
  unit_id: string;
  operator_id: string;
  po_number: string;
  po_line: number;
  supplier: string;
  expected: ExpectedValues;
  photo_references: string[];
}

export interface OverridePayload {
  operator_id: string;
  override_verdict: OverrideVerdict;
  reason: string;
}

export interface HealthResponse {
  status: string;
  service: string;
}
