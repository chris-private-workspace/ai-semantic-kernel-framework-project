/**
 * File: frontend/src/pages/auth/mfa/index.tsx
 * Purpose: Two-factor verification — verbatim re-point per mockup AuthMFA (Sprint 57.35 US-D2).
 * Category: Frontend / pages / auth
 * Scope: Phase 57 / Sprint 57.23 US-D2 (initial NEW route) → Sprint 57.35 US-D2 (Phase-2 verbatim-CSS re-point)
 *
 * Description:
 *   Sprint 57.35 US-D2 verbatim re-point per `reference/design-mockups/page-auth-extras.jsx:248-371`:
 *     - Drop shadcn Card/CardContent/Button + lucide-react Clock/KeyRound/ShieldCheck/AlertTriangle/ArrowRight
 *     - Use mockup-ui Card + Button + Icon (keys/shield/clock/warn/arrow_right)
 *     - Verbatim .col + .row + .muted + .mono + .hr + .input classes
 *     - 48×48 warning-alpha key avatar + tab selector + 6-digit TOTP grid +
 *       WebAuthn 88×88 conic-gradient ring — all inline-style literals verbatim per mockup
 *     - Preserve Sprint 57.23 US-D2 Q3 roll-own UI behavior:
 *       · 6 input refs with useRef array + auto-focus advance + Backspace step-back +
 *         onPaste split + filled-state visual primary border (var(--primary) bg + border)
 *       · WebAuthn Simulate button → POST /api/v1/mfa/verify {simulated: true}
 *
 *   Backend wired (Sprint 57.112 — closes AD-Auth-MFA-Backend-IAM-Block-C TOTP leg):
 *     - POST /api/v1/mfa/verify is real (challenge-gated): reached after a
 *       password-login on an mfa_enabled user (the SPA holds the v2_mfa_challenge
 *       cookie). A valid TOTP → 200 + v2_jwt session → /auth/callback; a wrong code
 *       → 401 → errorInvalid. The demo banner is gone (the endpoint is no longer a stub).
 *     - WebAuthn is NOT supported this release: the Simulate button hits the endpoint,
 *       which returns 400 → webauthnUnavailable (honest, not a faked success).
 *
 *   Inline-style escape hatch instances (STYLE.md §1, all verbatim mockup literals):
 *     - 48×48 key avatar circle
 *     - Tab selector buttons
 *     - 6-digit input boxes (44×52 mono 22px + filled-state primary tint)
 *     - 88×88 WebAuthn conic-gradient spinning ring (Sprint 57.23 §3 hatch retained)
 *
 * Created: 2026-05-18 (Sprint 57.23 US-D2)
 * Last Modified: 2026-05-24
 *
 * Modification History:
 *   - 2026-06-13: Sprint 57.112 — wire real backend: drop demo banner; errorInvalid/webauthnUnavailable copy; redirectOn401:false on verify (a wrong code is an inline error, not a session-expiry SSO bounce — caught by drive-through)
 *   - 2026-05-24: Sprint 57.35 US-D2 — verbatim re-point per page-auth-extras.jsx:248-371 (closes Sprint 57.23 vintage HSL-translation drift)
 *   - 2026-05-18: Initial creation (Sprint 57.23 US-D2) — mockup-direct port of AuthMFA
 *
 * Related:
 *   - backend/src/api/v1/mfa.py (Phase 58+ NEW; AD-IAM-Block-C-Phase58)
 *   - frontend/src/components/AuthShell.tsx (Sprint 57.35 verbatim re-point)
 *   - frontend/src/components/mockup-ui.tsx (Card/Button/Icon)
 *   - frontend/src/i18n/locales/{en,zh-TW}/auth.json (auth.mfa.* namespace)
 *   - reference/design-mockups/page-auth-extras.jsx:248-371 (AuthMFA canonical visual source)
 */

/* eslint-disable no-restricted-syntax -- verbatim re-point: inline-style literals (avatar + tab selector + TOTP grid + WebAuthn conic spinner) copied byte-for-byte from mockup page-auth-extras.jsx:248-371 (STYLE.md §1 escape hatch + frontend-mockup-fidelity.md verbatim-CSS rule) */

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
import { Button, Card, Icon } from "@/components/mockup-ui";
import { fetchWithAuth } from "@/features/auth/services/authService";

type Method = "totp" | "webauthn";

export default function MFAPage(): JSX.Element {
  const { t } = useTranslation("auth");
  const navigate = useNavigate();
  const [method, setMethod] = useState<Method>("totp");
  const [code, setCode] = useState<string[]>(["", "", "", "", "", ""]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
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
    const focusIdx = Math.min(pasted.length, 5);
    inputRefs.current[focusIdx]?.focus();
  };

  const verify = async (e: FormEvent): Promise<void> => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const res = await fetchWithAuth(
        "/api/v1/mfa/verify",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ method, code: code.join("") }),
        },
        // A wrong code returns 401 — surface it inline here, do NOT let
        // fetchWithAuth treat it as an expired session + bounce to SSO.
        { redirectOn401: false },
      );
      if (!res.ok) {
        setError(t("mfa.errorInvalid"));
        return;
      }
      navigate("/auth/callback");
    } catch {
      setError(t("mfa.errorInvalid"));
    } finally {
      setBusy(false);
    }
  };

  const simulateWebauthn = async (): Promise<void> => {
    setBusy(true);
    setError(null);
    try {
      const res = await fetchWithAuth(
        "/api/v1/mfa/verify",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ method: "webauthn", simulated: true }),
        },
        { redirectOn401: false },
      );
      if (!res.ok) {
        // WebAuthn isn't supported yet (backend 400) — surface honestly, no fake success.
        setError(t("mfa.webauthnUnavailable"));
        return;
      }
      navigate("/auth/callback");
    } catch {
      setError(t("mfa.webauthnUnavailable"));
    } finally {
      setBusy(false);
    }
  };

  return (
    <AuthShell
      footer={
        <span>
          {t("mfa.foot")}{" "}
          <a
            href="#recovery"
            style={{ color: "var(--primary)", textDecoration: "none" }}
          >
            {t("mfa.help")}
          </a>
        </span>
      }
    >
      <Card>
        <form onSubmit={verify} className="col" style={{ gap: 16 }}>
          {/* Header — verbatim mockup L264-279 */}
          <div
            className="col"
            style={{ gap: 8, alignItems: "center", textAlign: "center" }}
          >
            <div
              style={{
                width: 48,
                height: 48,
                borderRadius: "50%",
                background: "oklch(from var(--warning) l c h / 0.14)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                color: "var(--warning)",
              }}
              aria-hidden
            >
              <Icon name="keys" size={22} />
            </div>
            <div>
              <div style={{ fontSize: 16, fontWeight: 600, marginBottom: 4 }}>
                {t("mfa.title")}
              </div>
              <div className="muted" style={{ fontSize: 12.5 }}>
                {method === "totp" ? t("mfa.totpSub") : t("mfa.webauthnSub")}
              </div>
            </div>
          </div>

          {/* Tab selector — verbatim mockup L281-304 */}
          <div
            role="tablist"
            aria-label={t("mfa.title")}
            className="row"
            style={{
              gap: 6,
              padding: 4,
              background: "var(--bg-2)",
              borderRadius: "var(--radius-sm)",
            }}
          >
            <button
              type="button"
              role="tab"
              aria-selected={method === "totp"}
              onClick={() => setMethod("totp")}
              style={{
                flex: 1,
                padding: "6px 10px",
                borderRadius: 4,
                background: method === "totp" ? "var(--bg)" : "transparent",
                border: "none",
                cursor: "pointer",
                color: "var(--fg)",
                fontSize: 12,
                fontWeight: method === "totp" ? 500 : 400,
              }}
            >
              <Icon
                name="keys"
                size={11}
                style={{ verticalAlign: -1, marginRight: 4 }}
              />
              {t("mfa.tabTotp")}
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={method === "webauthn"}
              onClick={() => setMethod("webauthn")}
              style={{
                flex: 1,
                padding: "6px 10px",
                borderRadius: 4,
                background: method === "webauthn" ? "var(--bg)" : "transparent",
                border: "none",
                cursor: "pointer",
                color: "var(--fg)",
                fontSize: 12,
                fontWeight: method === "webauthn" ? 500 : 400,
              }}
            >
              <Icon
                name="shield"
                size={11}
                style={{ verticalAlign: -1, marginRight: 4 }}
              />
              {t("mfa.tabWebauthn")}
            </button>
          </div>

          {/* Error surface */}
          {error && (
            <div
              role="alert"
              style={{
                display: "flex",
                alignItems: "flex-start",
                gap: 8,
                padding: 10,
                borderRadius: 6,
                border: "1px solid oklch(from var(--danger) l c h / 0.4)",
                background: "oklch(from var(--danger) l c h / 0.1)",
                color: "var(--danger)",
                fontSize: 12.5,
              }}
            >
              <Icon name="warn" size={14} style={{ marginTop: 1, flexShrink: 0 }} />
              <span>{error}</span>
            </div>
          )}

          {/* TOTP panel — verbatim mockup L306-337 */}
          {method === "totp" && (
            <div className="col" style={{ gap: 12 }} role="tabpanel">
              <div className="row" style={{ gap: 6, justifyContent: "center" }}>
                {code.map((v, i) => (
                  <input
                    key={i}
                    ref={(el) => {
                      inputRefs.current[i] = el;
                    }}
                    value={v}
                    onChange={(e: ChangeEvent<HTMLInputElement>) =>
                      updateDigit(i, e.target.value)
                    }
                    onKeyDown={(e) => handleKeyDown(i, e)}
                    onPaste={i === 0 ? handlePaste : undefined}
                    inputMode="numeric"
                    maxLength={1}
                    aria-label={t("mfa.digitLabel", { idx: i + 1 })}
                    className="input mono"
                    style={{
                      width: 44,
                      height: 52,
                      textAlign: "center",
                      fontSize: 22,
                      fontWeight: 500,
                      background: v
                        ? "oklch(from var(--primary) l c h / 0.10)"
                        : "var(--bg-1)",
                      borderColor: v ? "var(--primary)" : "var(--border)",
                    }}
                  />
                ))}
              </div>
              <div
                className="row"
                style={{
                  justifyContent: "center",
                  fontSize: 11,
                  color: "var(--fg-subtle)",
                  gap: 4,
                }}
              >
                <Icon name="clock" size={11} />
                <span className="mono">{t("mfa.refreshIn")}</span>
              </div>
              <Button
                type="submit"
                variant="primary"
                data-size="lg"
                iconRight="arrow_right"
                disabled={!filled || busy}
              >
                {busy ? t("mfa.verifying") : t("mfa.verify")}
              </Button>
            </div>
          )}

          {/* WebAuthn panel — verbatim mockup L339-361 */}
          {method === "webauthn" && (
            <div
              className="col"
              style={{ gap: 12, alignItems: "center", padding: "16px 0" }}
              role="tabpanel"
            >
              <div
                data-testid="webauthn-ring"
                style={{
                  width: 88,
                  height: 88,
                  borderRadius: "50%",
                  background:
                    "conic-gradient(from 0deg, var(--primary), oklch(from var(--primary) l c h / 0.3))",
                  animation: "spin 2.5s linear infinite",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                }}
              >
                <div
                  style={{
                    width: 76,
                    height: 76,
                    borderRadius: "50%",
                    background: "var(--bg-1)",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    color: "var(--primary)",
                  }}
                >
                  <Icon name="shield" size={32} />
                </div>
              </div>
              <div
                className="muted"
                style={{ fontSize: 12, textAlign: "center", maxWidth: 280 }}
              >
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

          {/* Recovery link — verbatim mockup L363-366 */}
          <div className="hr" style={{ margin: 0 }} />
          <div
            className="row"
            style={{ justifyContent: "center", fontSize: 11.5 }}
          >
            <span
              title={t("mfa.recoveryTooltip")}
              style={{ color: "var(--fg-subtle)", pointerEvents: "none" }}
            >
              {t("mfa.recoveryCode")}
            </span>
          </div>
        </form>
      </Card>
    </AuthShell>
  );
}
