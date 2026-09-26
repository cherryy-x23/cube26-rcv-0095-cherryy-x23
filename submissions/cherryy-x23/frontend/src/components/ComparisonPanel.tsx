import React from 'react';
import { ExpectedValues, EvidenceRecord } from '../types/inspection';

interface ComparisonPanelProps {
  expected: ExpectedValues;
  evidenceRecord?: EvidenceRecord | null;
}

export const ComparisonPanel: React.FC<ComparisonPanelProps> = ({ expected, evidenceRecord }) => {
  const obs = evidenceRecord?.observed_values;
  const indChecks = evidenceRecord?.individual_checks;

  const getObservedFor = (checkTypePrefix: string): string => {
    if (obs) {
      if (checkTypePrefix === 'sku') {
        return obs.identified_sku || 'Uncertain / Not Identified';
      }
      if (checkTypePrefix === 'quantity') {
        return obs.quantity_counted !== null && obs.quantity_counted !== undefined
          ? `${obs.quantity_counted} units`
          : 'Uncertain / Not Counted';
      }
      if (checkTypePrefix === 'damage') {
        return `Carton: ${obs.carton_damage || 'none'} | Unit: ${obs.unit_damage || 'none'}`;
      }
      if (checkTypePrefix === 'spec') {
        return `${obs.observed_colour || '—'} / ${obs.observed_variant || '—'}`;
      }
    }

    if (evidenceRecord?.checks) {
      const check = evidenceRecord.checks.find((c) => c.check_type.includes(checkTypePrefix));
      if (check?.observed_value) return check.observed_value;
    }

    return 'Not verified';
  };

  const getCheckVerdict = (checkTypePrefix: string): string | null => {
    if (indChecks) {
      if (checkTypePrefix === 'sku') return indChecks.identity_check?.verdict || null;
      if (checkTypePrefix === 'quantity') return indChecks.quantity_check?.verdict || null;
      if (checkTypePrefix === 'damage') return indChecks.carton_condition_check?.verdict || null;
      if (checkTypePrefix === 'spec') return indChecks.specification_check?.verdict || null;
    }

    if (evidenceRecord?.checks) {
      const check = evidenceRecord.checks.find((c) => c.check_type.includes(checkTypePrefix));
      return check?.verdict || null;
    }

    return null;
  };

  const skuVerdict = getCheckVerdict('sku');
  const qtyVerdict = getCheckVerdict('quantity');
  const damageVerdict = getCheckVerdict('damage');
  const specVerdict = getCheckVerdict('spec');

  return (
    <div className="card">
      <div className="card-title">
        <span>PO Expected vs Visual Evidence Comparison</span>
        <span style={{ fontSize: '12px', color: '#64748b' }}>Deterministic Verification</span>
      </div>

      <div className="comparison-grid">
        <div className="comparison-box">
          <h4>Expected (Purchase Order)</h4>
          <div className="comparison-row">
            <span className="comparison-key">SKU</span>
            <span className="comparison-val font-mono">{expected.sku}</span>
          </div>
          <div className="comparison-row">
            <span className="comparison-key">Quantity Ordered</span>
            <span className="comparison-val font-mono">{expected.qty_ordered} units</span>
          </div>
          <div className="comparison-row">
            <span className="comparison-key">Packaging Breakdown</span>
            <span className="comparison-val font-mono">
              {expected.cartons_ordered ?? '-'} cartons × {expected.units_per_carton_ordered ?? '-'} units
            </span>
          </div>
          <div className="comparison-row">
            <span className="comparison-key">Product Title</span>
            <span className="comparison-val">{expected.product_title || '—'}</span>
          </div>
          <div className="comparison-row">
            <span className="comparison-key">Colour / Variant</span>
            <span className="comparison-val">
              {expected.spec_colour || '—'} / {expected.spec_variant || '—'}
            </span>
          </div>
          <div className="comparison-row">
            <span className="comparison-key">Components</span>
            <span className="comparison-val">
              {expected.spec_components ? expected.spec_components.join(', ') : '—'}
            </span>
          </div>
        </div>

        <div className="comparison-box">
          <h4>Observed (Visual Evidence)</h4>
          <div className="comparison-row">
            <span className="comparison-key">SKU Observed</span>
            <span
              className={`comparison-val font-mono ${skuVerdict === 'FAIL' ? 'comparison-mismatch' : ''}`}
            >
              {getObservedFor('sku')}
            </span>
          </div>
          <div className="comparison-row">
            <span className="comparison-key">Quantity Observed</span>
            <span
              className={`comparison-val font-mono ${qtyVerdict === 'FAIL' ? 'comparison-mismatch' : ''}`}
            >
              {getObservedFor('quantity')}
            </span>
          </div>
          <div className="comparison-row">
            <span className="comparison-key">Damage Assessment</span>
            <span
              className={`comparison-val ${damageVerdict === 'FAIL' ? 'comparison-mismatch' : ''}`}
            >
              {getObservedFor('damage')}
            </span>
          </div>
          <div className="comparison-row">
            <span className="comparison-key">Specifications & Variant</span>
            <span
              className={`comparison-val ${specVerdict === 'FAIL' ? 'comparison-mismatch' : ''}`}
            >
              {getObservedFor('spec')}
            </span>
          </div>
          <div className="comparison-row">
            <span className="comparison-key">Evidence Record ID</span>
            <span className="comparison-val font-mono">
              {evidenceRecord?.record_id || evidenceRecord?.rcv_number || 'Pending execution'}
            </span>
          </div>
          <div className="comparison-row">
            <span className="comparison-key">Decision Method</span>
            <span className="comparison-val" style={{ color: '#0284c7' }}>
              Deterministic Engine
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
