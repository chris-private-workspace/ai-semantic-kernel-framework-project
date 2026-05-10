/**
 * File: frontend/tests/unit/i18n/i18n.test.ts
 * Purpose: Unit tests for the i18n bundle — locale parity (en ≡ zh-TW key sets) + changeLanguage().
 * Category: Tests / i18n
 * Scope: Phase 57 / Sprint 57.13 US-B5
 *
 * Created: 2026-05-10 (Sprint 57.13 Day 7)
 */

import { afterAll, describe, expect, it } from "vitest";

import i18n, { SUPPORTED_LOCALES, resources } from "@/i18n";

/** Flatten a nested resource object to dotted leaf keys (sorted). */
function leafKeys(obj: Record<string, unknown>, prefix = ""): string[] {
  const out: string[] = [];
  for (const [k, v] of Object.entries(obj)) {
    const path = prefix ? `${prefix}.${k}` : k;
    if (v !== null && typeof v === "object" && !Array.isArray(v)) {
      out.push(...leafKeys(v as Record<string, unknown>, path));
    } else {
      out.push(path);
    }
  }
  return out.sort();
}

describe("i18n bundle", () => {
  afterAll(async () => {
    // Leave the singleton on the default locale for any later test files.
    await i18n.changeLanguage("en");
  });

  it("exposes exactly the two supported locales", () => {
    expect(SUPPORTED_LOCALES.map((l) => l.id)).toEqual(["en", "zh-TW"]);
    expect(Object.keys(resources).sort()).toEqual(["en", "zh-TW"]);
  });

  it("en and zh-TW have identical key sets per namespace", () => {
    for (const ns of ["common", "auth"] as const) {
      const en = leafKeys(resources.en[ns] as Record<string, unknown>);
      const zh = leafKeys(resources["zh-TW"][ns] as Record<string, unknown>);
      expect(zh).toEqual(en);
      expect(en.length).toBeGreaterThan(0);
    }
  });

  it("every leaf value is a non-empty string in both locales", () => {
    for (const loc of ["en", "zh-TW"] as const) {
      for (const ns of ["common", "auth"] as const) {
        const bundle = resources[loc][ns] as Record<string, unknown>;
        for (const key of leafKeys(bundle)) {
          const value = key.split(".").reduce<unknown>((acc, k) => (acc as Record<string, unknown>)[k], bundle);
          expect(typeof value, `${loc}/${ns}:${key}`).toBe("string");
          expect((value as string).length, `${loc}/${ns}:${key}`).toBeGreaterThan(0);
        }
      }
    }
  });

  it("changeLanguage switches resolved translations", async () => {
    await i18n.changeLanguage("en");
    expect(i18n.t("nav.costDashboard", { ns: "common" })).toBe("Cost Dashboard");
    expect(i18n.t("loginWithWorkOS", { ns: "auth" })).toBe("Login with WorkOS");

    await i18n.changeLanguage("zh-TW");
    expect(i18n.t("nav.costDashboard", { ns: "common" })).toBe("成本儀表板");
    expect(i18n.t("loginWithWorkOS", { ns: "auth" })).toBe("使用 WorkOS 登入");
  });

  it("interpolates the dev-login error template", async () => {
    await i18n.changeLanguage("en");
    expect(i18n.t("devSection.errorFailed", { ns: "auth", status: 503 })).toBe("dev-login failed (503)");
  });

  it("falls back to en for an unknown locale", async () => {
    await i18n.changeLanguage("fr");
    expect(i18n.t("nav.costDashboard", { ns: "common" })).toBe("Cost Dashboard");
  });
});
