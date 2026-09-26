import React from 'react';
import { InspectionCheck, IndividualChecks, ExpectedValues, ObservedValues } from '../types/inspection';
import { StatusBadge } from './StatusBadge';

interface ChecksBreakdownProps {
  checks?: InspectionCheck[];
  individualChecks?: IndividualChecks;
  expected?: ExpectedValues;
  observed?: ObservedValues;
}

export const ChecksBreakdown: React.FC<ChecksBreakdownProps> = ({
  checks,
  individualChecks,
  expected,
  observed,
}) => {
  const formatCheckName = (type: string): string => {
    return type
      .split('_')
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  // Build rows from individual_checks if present
  let displayRows: {
    name: string;
    verdict: any;
    expected: string;
    observed: string;
    discrepancy: string;
    notes: string;
    testId: string;
  }[] = [];

  if (individualChecks) {
    if (individualChecks.identity_check) {
      displayRows.push({
        name: 'Identity & SKU Check',
        verdict: individualChecks.identity_check.verdict,
        expected: expected?.sku || '—',
        observed: observed?.identified_sku || 'Uncertain',
        discrepancy: individualChecks.identity_check.verdict === 'PASS' ? '0' : 'Mismatch',
        notes: individualChecks.identity_check.reason,
        testId: 'check-row-sku',
      });
    }
    if (individualChecks.quantity_check) {
      const disc = individualChecks.quantity_check.discrepancy;
      displayRows.push({
        name: 'Quantity Count Check',
        verdict: individualChecks.quantity_check.verdict,
        expected: `${expected?.qty_ordered ?? 0} units`,
        observed: `${observed?.quantity_counted ?? 'Uncounted'} units`,
        discrepancy: disc !== undefined && disc !== null ? (disc > 0 ? `+${disc} units` : `${disc} units`) : '0 units',
        notes: individualChecks.quantity_check.reason,
        testId: 'check-row-quantity',
      });
    }
    if (individualChecks.carton_condition_check) {
      displayRows.push({
        name: 'Master Carton Condition',
        verdict: individualChecks.carton_condition_check.verdict,
        expected: 'Clean / Undamaged',
        observed: observed?.carton_damage || 'None',
        discrepancy: observed?.carton_damage && observed.carton_damage !== 'none' ? observed.carton_damage : '0',
        notes: individualChecks.carton_condition_check.reason,
        testId: 'check-row-carton_damage',
      });
    }
    if (individualChecks.unit_condition_check) {
      displayRows.push({
        name: 'Sellable Unit Condition',
        verdict: individualChecks.unit_condition_check.verdict,
        expected: 'Clean / Undamaged',
        observed: observed?.unit_damage || 'None',
        discrepancy: observed?.unit_damage && observed.unit_damage !== 'none' ? observed.unit_damage : '0',
        notes: individualChecks.unit_condition_check.reason,
        testId: 'check-row-unit_damage',
      });
    }
    if (individualChecks.specification_check) {
      displayRows.push({
        name: 'Specification & Variant Check',
        verdict: individualChecks.specification_check.verdict,
        expected: `${expected?.spec_colour || '—'} / ${expected?.spec_variant || '—'}`,
        observed: `${observed?.observed_colour || '—'} / ${observed?.observed_variant || '—'}`,
        discrepancy: individualChecks.specification_check.verdict === 'PASS' ? '0' : 'Mismatch',
        notes: individualChecks.specification_check.reason,
        testId: 'check-row-spec',
      });
    }
  } else if (checks && checks.length > 0) {
    displayRows = checks.map((c) => ({
      name: formatCheckName(c.check_type),
      verdict: c.verdict,
      expected: c.expected_value || '—',
      observed: c.observed_value || '—',
      discrepancy: c.discrepancy !== undefined && c.discrepancy !== null ? String(c.discrepancy) : '0',
      notes: c.notes || '—',
      testId: `check-row-${c.check_type}`,
    }));
  }

  if (displayRows.length === 0) {
    return (
      <div className="card">
        <div className="card-title">Contractual Inspection Checks</div>
        <p style={{ color: '#64748b', fontSize: '13px' }}>
          No individual checks available yet. Run the inspection to execute checks.
        </p>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="card-title">
        <span>Contractual Inspection Checks ({displayRows.length})</span>
        <span style={{ fontSize: '12px', color: '#64748b' }}>Zero-hallucination deterministic verdicts</span>
      </div>

      <div className="table-container">
        <table className="data-table">
          <thead>
            <tr>
              <th>Check Type</th>
              <th>Verdict</th>
              <th>Expected Value</th>
              <th>Observed Evidence</th>
              <th>Discrepancy</th>
              <th>Notes / Findings</th>
            </tr>
          </thead>
          <tbody>
            {displayRows.map((row, idx) => (
              <tr key={idx} data-testid={row.testId}>
                <td style={{ fontWeight: 600 }}>{row.name}</td>
                <td>
                  <StatusBadge verdict={row.verdict} size="sm" />
                </td>
                <td className="font-mono">{row.expected}</td>
                <td
                  className={`font-mono ${
                    row.verdict === 'FAIL' ? 'comparison-mismatch' : ''
                  }`}
                >
                  {row.observed}
                </td>
                <td style={{ fontWeight: 600, color: row.verdict === 'FAIL' ? '#dc2626' : 'inherit' }}>
                  {row.discrepancy}
                </td>
                <td style={{ color: '#475569', fontSize: '12.5px' }}>{row.notes}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
