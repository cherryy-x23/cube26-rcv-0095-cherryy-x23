# Held-Out Evaluation Fixtures Directory

## Status: AWAITING HELD-OUT PHYSICAL DATASET

> **HONESTY NOTICE (CUBE Engineering Rules):**  
> No real-world evaluation photographs are bundled in this starter repository. Per CUBE Buildathon guidelines, **no fake photographs or synthetic images have been generated or passed off as real-world evaluation evidence**. This directory defines the required organizational layout and will receive the 50 held-out evaluation units when captured.

---

## Required Directory Layout

When the physical 50-unit held-out receiving dataset is assembled, each unit must be placed in a dedicated subdirectory named after the unit ID:

```text
fixtures/
??? UNIT-E001/
?   ??? pallet.jpg       # High-angle full pallet view showing wrapping and master cartons
?   ??? carton.jpg       # Close-up of target master shipping carton showing labels and condition
?   ??? unit.jpg         # Top-down view of open carton or individual sellable retail unit
?   ??? barcode.jpg      # High-resolution close-up of SKU label / UPC / FNSKU barcode
??? UNIT-E002/
?   ??? pallet.jpg
?   ??? carton.jpg
?   ??? unit.jpg
?   ??? barcode.jpg
...
??? UNIT-E050/
    ??? pallet.jpg
    ??? carton.jpg
    ??? unit.jpg
    ??? barcode.jpg
```

---

## Technical Specifications for Incoming Captures

1. **Format:** Standard JPEG or PNG (`.jpg`, `.jpeg`, `.png`).
2. **Resolution:** Minimum $1920 \times 1080$ recommended to allow reliable label OCR.
3. **Lighting & Angles:**
   - Standard dock door warehouse lighting.
   - Natural operational imperfections (e.g. slight glare, shrink-wrap reflections, transit scuffs) should be preserved to test robust failure-mode handling (`UNCERTAIN`).
4. **Integrity Verification:**
   - The evaluation runner (`run_eval.py`) automatically computes SHA-256 hashes for all fixture files upon execution.
