/**
 * File: frontend/tests/unit/chat_v2/components/CompactionMarker.test.tsx
 * Purpose: Vitest render coverage for the Sprint 57.159 compaction timeline marker.
 * Category: Frontend / tests / unit / chat_v2
 * Scope: Sprint 57.159 (Cat 4 L2→L3 + A-5c surface)
 *
 * Created: 2026-07-07 (Sprint 57.159)
 *
 * Modification History:
 *   - 2026-07-07: Initial creation (Sprint 57.159)
 */

import { render, screen } from "@testing-library/react";
import { describe, expect, test } from "vitest";

import { CompactionMarker } from "@/features/chat_v2/components/turns/CompactionMarker";

describe("CompactionMarker (Sprint 57.159 — Cat 4 context compaction)", () => {
  test("renders the token reduction, strategy, and messages-compacted count", () => {
    render(
      <CompactionMarker
        turn={{
          role: "compaction",
          id: "c_1",
          at: "2026-07-07T00:00:00.000Z",
          tokensBefore: 9824,
          tokensAfter: 2679,
          strategy: "hybrid",
          messagesCompacted: 12,
        }}
      />,
    );
    const marker = screen.getByTestId("compaction-marker");
    // Numbers rendered with locale grouping (toLocaleString).
    expect(marker).toHaveTextContent("9,824");
    expect(marker).toHaveTextContent("2,679");
    expect(marker).toHaveTextContent("hybrid");
    expect(marker).toHaveTextContent("12 msgs");
    expect(marker).toHaveTextContent("Context compacted");
  });
});
