/**
 * File: frontend/tests/unit/setup.ts
 * Purpose: Vitest global setup — registers @testing-library/jest-dom matchers.
 * Category: Frontend / tests / unit
 * Scope: Phase 57 / Sprint 57.1 US-1 (per Day 0 D11 — first frontend Vitest infra)
 *
 * Created: 2026-05-06 (Sprint 57.1 Day 1)
 * Last Modified: 2026-05-06
 *
 * Modification History:
 *   - 2026-05-10: Sprint 57.13 US-B3 — jsdom polyfills for Radix (pointer capture / scrollIntoView / ResizeObserver)
 *   - 2026-05-06: Initial creation (Sprint 57.1 Day 1 / US-1 — Vitest setup)
 */

import "@testing-library/jest-dom/vitest";

// --- jsdom polyfills for Radix UI primitives (Dialog / DropdownMenu) ---
// Radix uses Pointer Capture + scrollIntoView + ResizeObserver, none of which
// jsdom implements. Without these, opening a Radix menu/dialog under @testing-library
// throws (e.g. "target.hasPointerCapture is not a function"). Sprint 57.13 US-B3.
if (!Element.prototype.hasPointerCapture) {
  Element.prototype.hasPointerCapture = () => false;
}
if (!Element.prototype.setPointerCapture) {
  Element.prototype.setPointerCapture = () => {};
}
if (!Element.prototype.releasePointerCapture) {
  Element.prototype.releasePointerCapture = () => {};
}
if (!Element.prototype.scrollIntoView) {
  Element.prototype.scrollIntoView = () => {};
}
if (typeof globalThis.ResizeObserver === "undefined") {
  globalThis.ResizeObserver = class {
    observe(): void {}
    unobserve(): void {}
    disconnect(): void {}
  };
}
