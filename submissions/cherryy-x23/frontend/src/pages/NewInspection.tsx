import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTenant } from '../context/TenantContext';
import { inspectionApi } from '../api/inspectionApi';
import { InspectionCreatePayload } from '../types/inspection';

export const NewInspection: React.FC = () => {
  const navigate = useNavigate();
  const { currentOrg } = useTenant();

  // PO Fields
  const [unitId, setUnitId] = useState<string>('UNIT-DEMO-001');
  const [operatorId, setOperatorId] = useState<string>('operator-001');
  const [poNumber, setPoNumber] = useState<string>('PO-1001');
  const [poLine, setPoLine] = useState<number>(1);
  const [supplier, setSupplier] = useState<string>('Demo Supplier');

  // Expected Product Fields
  const [sku, setSku] = useState<string>('BLUE-BOTTLE-001');
  const [asin, setAsin] = useState<string>('B000DEMO');
  const [productTitle, setProductTitle] = useState<string>('Blue Water Bottle');
  const [specColour, setSpecColour] = useState<string>('blue');
  const [specVariant, setSpecVariant] = useState<string>('standard');
  const [specComponentsRaw, setSpecComponentsRaw] = useState<string>('bottle, cap');
  const [cartonsOrdered, setCartonsOrdered] = useState<number>(2);
  const [unitsPerCarton, setUnitsPerCarton] = useState<number>(12);
  const [qtyOrdered, setQtyOrdered] = useState<number>(24);

  // Photo References
  const [photoReferences, setPhotoReferences] = useState<string[]>([
    'fixtures/unit-001/photo-01.jpg',
    'fixtures/unit-001/photo-02.jpg',
  ]);
  const [newPhotoRef, setNewPhotoRef] = useState<string>('');

  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleAddPhoto = () => {
    if (newPhotoRef.trim()) {
      setPhotoReferences([...photoReferences, newPhotoRef.trim()]);
      setNewPhotoRef('');
    }
  };

  const handleRemovePhoto = (index: number) => {
    setPhotoReferences(photoReferences.filter((_, idx) => idx !== index));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!sku.trim()) {
      setError('Product SKU is strictly required.');
      return;
    }
    if (!qtyOrdered || qtyOrdered <= 0) {
      setError('Quantity ordered must be greater than zero.');
      return;
    }

    setLoading(true);
    setError(null);

    const components = specComponentsRaw
      .split(',')
      .map((c) => c.trim())
      .filter((c) => c.length > 0);

    const payload: InspectionCreatePayload = {
      org_id: currentOrg,
      unit_id: unitId.trim(),
      operator_id: operatorId.trim(),
      po_number: poNumber.trim(),
      po_line: Number(poLine),
      supplier: supplier.trim(),
      expected: {
        sku: sku.trim(),
        asin: asin.trim() || undefined,
        product_title: productTitle.trim() || undefined,
        spec_colour: specColour.trim() || undefined,
        spec_variant: specVariant.trim() || undefined,
        spec_components: components.length > 0 ? components : undefined,
        cartons_ordered: cartonsOrdered ? Number(cartonsOrdered) : undefined,
        units_per_carton_ordered: unitsPerCarton ? Number(unitsPerCarton) : undefined,
        qty_ordered: Number(qtyOrdered),
      },
      photo_references: photoReferences,
    };

    try {
      const created = await inspectionApi.createInspection(payload);
      navigate(`/inspections/${created.inspection_id}`);
    } catch (err: any) {
      setError(err.message || 'Failed to create inspection.');
      setLoading(false);
    }
  };

  const handleLoadPreset = (preset: string) => {
    if (preset === 'pass') {
      setUnitId('DEMO-PASS-001');
      setPoNumber('PO-DEMO-1001');
      setSupplier('Acme Bottles Ltd');
      setSku('BLUE-BOTTLE-001');
      setProductTitle('Blue Water Bottle 750ml');
      setSpecColour('blue');
      setSpecVariant('standard');
      setSpecComponentsRaw('bottle, cap');
      setCartonsOrdered(2);
      setUnitsPerCarton(12);
      setQtyOrdered(24);
      setPhotoReferences(['fixtures/demo/clean_pallet.jpg', 'fixtures/demo/clean_carton.jpg']);
    } else if (preset === 'fail') {
      setUnitId('DEMO-FAIL-001');
      setPoNumber('PO-DEMO-1002');
      setSupplier('Logistics Freight Global');
      setSku('BLUE-BOTTLE-001');
      setProductTitle('Blue Water Bottle 750ml');
      setSpecColour('blue');
      setSpecVariant('standard');
      setSpecComponentsRaw('bottle, cap');
      setCartonsOrdered(2);
      setUnitsPerCarton(12);
      setQtyOrdered(24);
      setPhotoReferences(['fixtures/demo/crushed_carton.jpg', 'fixtures/demo/damaged_corner.jpg']);
    } else if (preset === 'uncertain') {
      setUnitId('DEMO-UNCERTAIN-001');
      setPoNumber('PO-DEMO-1003');
      setSupplier('Global Ceramics Co');
      setSku('RED-MUG-003');
      setProductTitle('Red Ceramic Mug 350ml');
      setSpecColour('red');
      setSpecVariant('matte');
      setSpecComponentsRaw('mug');
      setCartonsOrdered(1);
      setUnitsPerCarton(12);
      setQtyOrdered(12);
      setPhotoReferences(['fixtures/demo/blurry_label.jpg', 'fixtures/demo/glare_barcode.jpg']);
    } else if (preset === 'pending') {
      setUnitId('DEMO-PENDING-001');
      setPoNumber('PO-DEMO-1004');
      setSupplier('Summit Drinkware');
      setSku('BLACK-TUMBLER-004');
      setProductTitle('Black Insulated Tumbler');
      setSpecColour('black');
      setSpecVariant('matte-finish');
      setSpecComponentsRaw('tumbler, lid, straw');
      setCartonsOrdered(3);
      setUnitsPerCarton(12);
      setQtyOrdered(36);
      setPhotoReferences(['fixtures/demo/dock_pallet.jpg']);
    }
  };

  return (
    <div className="page-container" data-testid="new-inspection-page">
      <div className="page-header">
        <div>
          <h2>Create Receiving Inspection</h2>
          <p>Register inbound purchase order expectations and receiving photographic evidence</p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
          <span style={{ fontSize: '12px', fontWeight: 600, color: '#64748b' }}>Quick Preset:</span>
          <button
            type="button"
            className="btn btn-outline btn-sm"
            onClick={() => handleLoadPreset('pass')}
            data-testid="preset-pass"
          >
            ✓ 1. Clean Pass
          </button>
          <button
            type="button"
            className="btn btn-outline btn-sm"
            onClick={() => handleLoadPreset('fail')}
            data-testid="preset-fail"
          >
            ⚠ 2. Shortage/Damage
          </button>
          <button
            type="button"
            className="btn btn-outline btn-sm"
            onClick={() => handleLoadPreset('uncertain')}
            data-testid="preset-uncertain"
          >
            ? 3. Uncertain Evidence
          </button>
          <button
            type="button"
            className="btn btn-outline btn-sm"
            onClick={() => handleLoadPreset('pending')}
            data-testid="preset-pending"
          >
            ⏳ 4. Provider Failure
          </button>
        </div>
      </div>

      {error && (
        <div className="alert alert-error" role="alert" data-testid="create-error">
          <span>⚠️</span>
          <div>{error}</div>
        </div>
      )}

      <form onSubmit={handleSubmit} noValidate>
        {/* Step 1: PO & Tenant Information */}
        <div className="card">
          <div className="card-title">
            <span>1. Inbound Shipment & PO Context</span>
            <span style={{ fontSize: '12px', color: '#64748b' }}>Organization: {currentOrg}</span>
          </div>

          <div className="form-grid">
            <div className="form-group">
              <label className="form-label" htmlFor="unit-id">
                Receiving Unit ID <span className="req">*</span>
              </label>
              <input
                id="unit-id"
                className="form-input font-mono"
                value={unitId}
                onChange={(e) => setUnitId(e.target.value)}
                required
                disabled={loading}
              />
              <span className="form-hint">Physical pallet or shipment unit identifier</span>
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="operator-id">
                Dock Operator ID <span className="req">*</span>
              </label>
              <input
                id="operator-id"
                className="form-input"
                value={operatorId}
                onChange={(e) => setOperatorId(e.target.value)}
                required
                disabled={loading}
              />
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="po-number">
                Purchase Order # <span className="req">*</span>
              </label>
              <input
                id="po-number"
                className="form-input font-mono"
                value={poNumber}
                onChange={(e) => setPoNumber(e.target.value)}
                required
                disabled={loading}
              />
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="po-line">
                PO Line #
              </label>
              <input
                id="po-line"
                type="number"
                min="1"
                className="form-input"
                value={poLine}
                onChange={(e) => setPoLine(Number(e.target.value))}
                disabled={loading}
              />
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="supplier">
                Supplier Name
              </label>
              <input
                id="supplier"
                className="form-input"
                value={supplier}
                onChange={(e) => setSupplier(e.target.value)}
                disabled={loading}
              />
            </div>
          </div>
        </div>

        {/* Step 2: Expected Product Information */}
        <div className="card">
          <div className="card-title">
            <span>2. Expected Product Specifications</span>
            <span style={{ fontSize: '12px', color: '#64748b' }}>Deterministic match targets</span>
          </div>

          <div className="form-grid">
            <div className="form-group">
              <label className="form-label" htmlFor="sku">
                Expected SKU <span className="req">*</span>
              </label>
              <input
                id="sku"
                className="form-input font-mono"
                value={sku}
                onChange={(e) => setSku(e.target.value)}
                required
                disabled={loading}
              />
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="asin">
                ASIN / Catalog Barcode
              </label>
              <input
                id="asin"
                className="form-input font-mono"
                value={asin}
                onChange={(e) => setAsin(e.target.value)}
                disabled={loading}
              />
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="product-title">
                Product Title
              </label>
              <input
                id="product-title"
                className="form-input"
                value={productTitle}
                onChange={(e) => setProductTitle(e.target.value)}
                disabled={loading}
              />
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="qty-ordered">
                Total Quantity Ordered <span className="req">*</span>
              </label>
              <input
                id="qty-ordered"
                type="number"
                min="1"
                className="form-input font-mono"
                value={qtyOrdered}
                onChange={(e) => setQtyOrdered(Number(e.target.value))}
                required
                disabled={loading}
              />
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="cartons-ordered">
                Master Cartons Ordered
              </label>
              <input
                id="cartons-ordered"
                type="number"
                min="1"
                className="form-input"
                value={cartonsOrdered}
                onChange={(e) => setCartonsOrdered(Number(e.target.value))}
                disabled={loading}
              />
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="units-per-carton">
                Units per Master Carton
              </label>
              <input
                id="units-per-carton"
                type="number"
                min="1"
                className="form-input"
                value={unitsPerCarton}
                onChange={(e) => setUnitsPerCarton(Number(e.target.value))}
                disabled={loading}
              />
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="spec-colour">
                Expected Colour
              </label>
              <input
                id="spec-colour"
                className="form-input"
                value={specColour}
                onChange={(e) => setSpecColour(e.target.value)}
                disabled={loading}
              />
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="spec-variant">
                Expected Variant
              </label>
              <input
                id="spec-variant"
                className="form-input"
                value={specVariant}
                onChange={(e) => setSpecVariant(e.target.value)}
                disabled={loading}
              />
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="spec-components">
                Expected Components (comma-separated)
              </label>
              <input
                id="spec-components"
                className="form-input"
                value={specComponentsRaw}
                onChange={(e) => setSpecComponentsRaw(e.target.value)}
                placeholder="bottle, cap, straw"
                disabled={loading}
              />
            </div>
          </div>
        </div>

        {/* Step 3: Photo References */}
        <div className="card">
          <div className="card-title">
            <span>3. Receiving Evidence (Photo References)</span>
            <span style={{ fontSize: '12px', color: '#64748b' }}>Preserved for audit trail</span>
          </div>

          <div
            style={{
              border: '2px dashed #cbd5e1',
              borderRadius: '8px',
              padding: '20px',
              textAlign: 'center',
              backgroundColor: '#f8fafc',
              marginBottom: '16px',
            }}
          >
            <div style={{ fontSize: '24px', marginBottom: '6px' }}>📷</div>
            <div style={{ fontWeight: 600, fontSize: '13.5px', marginBottom: '4px' }}>
              Dock Photographic Evidence Dropzone
            </div>
            <p style={{ fontSize: '12px', color: '#64748b', maxWidth: '500px', margin: '0 auto 12px auto' }}>
              Reference paths to pallet, carton, unit, and barcode photos. The system computes SHA-256 hashes
              automatically for all locally available files.
            </p>

            <div style={{ display: 'flex', gap: '8px', maxWidth: '600px', margin: '0 auto' }}>
              <input
                className="form-input font-mono"
                placeholder="e.g. fixtures/unit-001/photo-01.jpg"
                value={newPhotoRef}
                onChange={(e) => setNewPhotoRef(e.target.value)}
                disabled={loading}
                id="new-photo-ref-input"
              />
              <button
                type="button"
                className="btn btn-outline"
                onClick={handleAddPhoto}
                disabled={loading || !newPhotoRef.trim()}
              >
                + Add Photo
              </button>
            </div>
          </div>

          <div>
            <div style={{ fontSize: '12.5px', fontWeight: 600, marginBottom: '8px' }}>
              Attached Photo References ({photoReferences.length}):
            </div>
            {photoReferences.length === 0 ? (
              <p style={{ color: '#64748b', fontSize: '12px' }}>No photo references attached.</p>
            ) : (
              <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                {photoReferences.map((ref, idx) => (
                  <li
                    key={idx}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      padding: '8px 12px',
                      background: '#f1f5f9',
                      borderRadius: '4px',
                      fontSize: '12.5px',
                    }}
                  >
                    <span className="font-mono">{ref}</span>
                    <button
                      type="button"
                      onClick={() => handleRemovePhoto(idx)}
                      style={{
                        background: 'none',
                        border: 'none',
                        color: '#ef4444',
                        cursor: 'pointer',
                        fontWeight: 700,
                      }}
                      disabled={loading}
                    >
                      ✕ Remove
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>

        {/* Submit Actions */}
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
          <button
            type="button"
            className="btn btn-outline"
            onClick={() => navigate('/inspections')}
            disabled={loading}
          >
            Cancel
          </button>
          <button
            type="submit"
            className="btn btn-primary btn-lg"
            disabled={loading}
            data-testid="submit-inspection-button"
          >
            {loading ? (
              <>
                <span className="spinner" />
                <span>Creating Inspection...</span>
              </>
            ) : (
              'Create Inspection'
            )}
          </button>
        </div>
      </form>
    </div>
  );
};
