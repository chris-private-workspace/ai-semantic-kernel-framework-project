/**
 * File: frontend/src/pages/auth/mfa/index.tsx
 * Purpose: Two-factor verification — TOTP 6-digit + WebAuthn UI (Roll-own per Sprint 57.23 Q3).
 * Category: Frontend / pages / auth
 * Scope: Phase 57 / Sprint 57.23 US-D2 (NEW route)
 *
 * Description:
 *   Sprint 57.23 US-D2 NEW per `reference/design-mockups/page-auth-extras.jsx:249-371`:
 *     - AuthShell wrapped with footer ("Locked out? Use recovery code")
 *     - 48×48 warning-alpha key-icon avatar + title "Two-factor verification" + dynamic subtitle
 *     - Tab selector: Authenticator (default) / Security Key
 *     - TOTP tab: 6-digit input grid (44×52 mono 22px) with useRef auto-focus advance,
 *       Backspace step-back, paste-6-digits split, filled boxes get primary/10 border-primary,
 *       static "code refreshes in 23s" countdown, Verify button disabled until full
 *     - WebAuthn tab: 88×88 conic-gradient spinning ring + Shield icon + hint + Simulate button
 *     - Recovery code link (pointer-events-none + tooltip — Phase 58+ AD-Auth-MFA-Recovery)
 *
 *   Backend stub:
 *     - POST /api/v1/mfa/verify expected 501; surfaces demo-banner error
 *     - AD-Auth-MFA-Backend-IAM-Block-C-Phase58 carryover for real implementation
 *     - "MFA backend wire pending Phase 58+ IAM Block C" demo banner above tabs
 *
 *   On success (Phase 58+): navigate to /auth/callback.
 *
 *   Inline-style escape hatch (1 instance — STYLE.md §3):
 *     - WebAuthn conic-gradient spinning ring (Tailwind cannot express conic-gradient
 *       with --primary token + custom animation duration)
 *
 * Created: 2026-05-18 (Sprint 57.23 US-D2)
 *
 * Modification History:
 *   - 2026-05-18: Initial creation (Sprint 57.23 US-D2) — mockup-direct port of AuthMFA
 *
 * Related:
 *   - backend/src/api/v1/mfa.py (Phase 58+ NEW; AD-IAM-Block-C-Phase58)
 *   - frontend/src/components/AuthShell.tsx (Sprint 57.23 mockup full-screen centered)
 *   - frontend/src/i18n/locales/{en,zh-TW}/auth.json (auth.mfa.* namespace)
 *   - reference/design-mockups/page-auth-extras.jsx:249-371 (AuthMFA canonical visual source)
 */

import { AlertTriangle, ArrowRight, Clock, KeyRound, ShieldCheck } from "lucide-react";
import {
  type ChangeEvent,
  type ClipboardEvent,
  type FormEvent,
  type KeyboardEvent,
  useRef,
  useState,
} from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";

import { AuthShell } from "@/components/AuthShell";
import { Button, Card, CardContent } from "@/components/ui";
import { fetchWithAuth } from "@/features/auth/services/authService";

type Method = "totp" | "webauthn";

export default function MFAPage(): JSX.Element {
  const { t } = useTranslation("auth");
  const navigate = useNavigate();
  const [method, setMethod] = useState<Method>("totp");
  const [code, setCode] = useState<string[]>(["", "", "", "", "", ""]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  // useRef array for 6 inputs
  const inputRefs = useRef<Array<HTMLInputElement | null>>([null, null, null, null, null, null]);

  const filled = code.every((v) => v !== "");

  const updateDigit = (i: number, v: string): void => {
    if (!/^\d?$/.test(v)) return;
    const next = [...code];
    next[i] = v;
    setCode(next);
    if (v && i < 5) inputRefs.current[i + 1]?.focus();
  };

  const handleKeyDown = (i: number, e: KeyboardEvent<HTMLInputElement>): void => {
    if (e.key === "Backspace" && !code[i] && i > 0) {
      inputRefs.current[i - 1]?.focus();
    }
  };

  const handlePaste = (e: ClipboardEvent<HTMLInputElement>): void => {
    const pasted = e.clipboardData.getData("text").replace(/\D/g, "").slice(0, 6);
    if (pasted.length === 0) return;
    e.preventDefault();
    const next = ["", "", "", "", "", ""];
    for (let i = 0; i < pasted.length; i++) {
      next[i] = pasted[i];
    }
    setCode(next);
    // Focus the next empty slot (or last)
    const focusIdx = Math.min(pasted.length, 5);
    inputRefs.current[focusIdx]?.focus();
  };

  const verify = async (e: FormEvent): Promise<void> => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const res = await fetchWithAuth("/api/v1/mfa/verify", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ method, code: code.join("") }),
      });
      if (!res.ok) {
        setError(t("mfa.errorStubbed"));
        return;
      }
      navigate("/auth/callback");
    } catch {
      setError(t("mfa.errorStubbed"));
    } finally {
      setBusy(false);
    }
  };

  const simulateWebauthn = async (): Promise<void> => {
    // DEV-only fallback per Q3 Roll-own — simulates platform authenticator success
    setBusy(true);
    setError(null);
    try {
      const res = await fetchWithAuth("/api/v1/mfa/verify", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ method: "webauthn", simulated: true }),
      });
      if (!res.ok) {
        setError(t("mfa.errorStubbed"));
        return;
      }
      navigate("/auth/callback");
    } catch {
      setError(t("mfa.errorStubbed"));
    } finally {
      setBusy(false);
    }
  };

  return (
    <AuthShell
      footer={
        <span>
          {t("mfa.foot")}{" "}
          <a href="#recovery" className="text-primary hover:underline">
            {t("mfa.help")}
          </a>
        </span>
      }
    >
      <Card>
        <CardContent className="p-6">
          <form onSubmit={verify} className="flex flex-col gap-4">
            {/* Header (mockup L264-279) */}
            <div className="flex flex-col items-center gap-2 text-center">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-warning/15 text-warning">
                <KeyRound size={22} aria-hidden />
              </div>
              <div>
                <div className="mb-1 text-base font-semibold">{t("mfa.title")}</div>
                <div className="text-[12.5px] text-fg-muted">
                  {method === "totp" ? t("mfa.totpSub") : t("mfa.webauthnSub")}
                </div>
              </div>
            </div>

            {/* AP-2 demo banner */}
            <div
              role="note"
              className="rounded-md border border-warning/40 bg-warning/10 px-3 py-2 text-[11px] text-warning"
            >
              {t("mfa.demoBanner")}
            </div>

            {/* Tab selector (mockup L281-304) */}
            <div
              role="tablist"
              aria-label={t("mfa.title")}
              className="flex flex-row gap-1.5 rounded-md bg-bg-2 p-1"
            >
              <button
                type="button"
                role="tab"
                aria-selected={method === "totp"}
                onClick={() => setMethod("totp")}
                className={
                  method === "totp"
                    ? "flex flex-1 items-center justify-center gap-1.5 rounded bg-background px-2.5 py-1.5 text-[12px] font-medium text-foreground"
                    : "flex flex-1 items-center justify-center gap-1.5 rounded bg-transparent px-2.5 py-1.5 text-[12px] text-foreground"
                }
              >
                <KeyRound size={11} aria-hidden />
                {t("mfa.tabTotp")}
              </button>
              <button
                type="button"
                role="tab"
                aria-selected={method === "webauthn"}
                onClick={() => setMethod("webauthn")}
                className={
                  method === "webauthn"
                    ? "flex flex-1 items-center justify-center gap-1.5 rounded bg-background px-2.5 py-1.5 text-[12px] font-medium text-foreground"
                    : "flex flex-1 items-center justify-center gap-1.5 rounded bg-transparent px-2.5 py-1.5 text-[12px] text-foreground"
                }
              >
                <ShieldCheck size={11} aria-hidden />
                {t("mfa.tabWebauthn")}
              </button>
            </div>

            {/* Error surface */}
            {error && (
              <div
                role="alert"
                className="flex items-start gap-2 rounded border border-destructive/40 bg-destructive/10 p-3 text-sm text-destructive"
              >
                <AlertTriangle size={16} className="mt-0.5 shrink-0" />
                <span>{error}</span>
              </div>
            )}

            {/* TOTP panel (mockup L306-337) */}
            {method === "totp" && (
              <div className="flex flex-col gap-3" role="tabpanel">
                <div className="flex flex-row justify-center gap-1.5">
                  {code.map((v, i) => (
                    <input
                      key={i}
                      ref={(el) => {
                        inputRefs.current[i] = el;
                      }}
                      value={v}
                      onChange={(e: ChangeEvent<HTMLInputElement>) => updateDigit(i, e.target.value)}
                      onKeyDown={(e) => handleKeyDown(i, e)}
                      onPaste={i === 0 ? handlePaste : undefined}
                      inputMode="numeric"
                      maxLength={1}
                      aria-label={t("mfa.digitLabel", { idx: i + 1 })}
                      className={
                        v
                          ? "h-[52px] w-11 rounded-md border border-primary bg-primary/10 text-center font-mono text-[22px] font-medium focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                          : "h-[52px] w-11 rounded-md border border-border bg-bg-1 text-center font-mono text-[22px] font-medium focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                      }
                    />
                  ))}
                </div>
                <div className="flex flex-row items-center justify-center gap-1 text-[11px] text-fg-subtle">
                  <Clock size={11} aria-hidden />
                  <span className="font-mono">{t("mfa.refreshIn")}</span>
                </div>
                <Button type="submit" disabled={!filled || busy}>
                  {busy ? t("mfa.verifying") : t("mfa.verify")}
                  <ArrowRight size={16} className="ml-1" />
                </Button>
              </div>
            )}

            {/* WebAuthn panel (mockup L339-361) */}
            {method === "webauthn" && (
              <div className="flex flex-col items-center gap-3 py-4" role="tabpanel">
                <div
                  data-testid="webauthn-ring"
                  className="flex h-[88px] w-[88px] items-center justify-center rounded-full"
                  // eslint-disable-next-line no-restricted-syntax -- STYLE.md §3 escape hatch: Tailwind cannot express conic-gradient with --primary token (Sprint 57.23 US-D2 mockup AuthMFA L342-345)
                  style={{
                    background:
                      "conic-gradient(from 0deg, hsl(var(--primary)), hsl(var(--primary) / 0.3))",
                    animation: "spin 2.5s linear infinite",
                  }}
                >
                  <div className="flex h-[76px] w-[76px] items-center justify-center rounded-full bg-bg-1 text-primary">
                    <ShieldCheck size={32} aria-hidden />
                  </div>
                </div>
                <div className="max-w-[280px] text-center text-[12px] text-fg-muted">
                  {t("mfa.webauthnHint")}
                </div>
                <Button
                  type="button"
                  variant="ghost"
                  onClick={() => void simulateWebauthn()}
                  disabled={busy}
                >
                  {t("mfa.simulate")}
                </Button>
              </div>
            )}

            {/* Recovery link (mockup L363-366) */}
            <div className="h-px bg-border" aria-hidden />
            <div className="flex flex-row justify-center text-[11.5px]">
              <span
                title={t("mfa.recoveryTooltip")}
                className="pointer-events-none text-fg-subtle"
              >
                {t("mfa.recoveryCode")}
              </span>
            </div>
          </form>
        </CardContent>
      </Card>
    </AuthShell>
  );
}
