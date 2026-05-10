/**
 * File: frontend/src/i18n/index.ts
 * Purpose: i18next bootstrap — English + Traditional Chinese (zh-TW), localStorage-persisted locale.
 * Category: Frontend / i18n (Sprint 57.13 US-B5 — internationalization)
 * Scope: Phase 57 / Sprint 57.13 US-B5
 *
 * Description:
 *   Initializes i18next with react-i18next + the browser language detector.
 *   Resources are bundled statically (imported JSON, two namespaces: `common`
 *   and `auth`) so there's no async load — `init()` resolves synchronously and
 *   no <Suspense> boundary is needed (we also set react.useSuspense=false to be
 *   explicit). Detection order: localStorage key `ipa-locale` first, then the
 *   navigator language; fallbackLng is `en`. The UserMenu locale switcher writes
 *   `ipa-locale` + calls i18n.changeLanguage(), so the choice survives reload.
 *
 *   Import this once from main.tsx (`import "./i18n"`) before render.
 *
 * Key Components:
 *   - SUPPORTED_LOCALES — the two locales the switcher offers (id + native label)
 *   - default export — the configured i18next instance (use via useTranslation())
 *
 * Created: 2026-05-10 (Sprint 57.13 Day 7)
 *
 * Related:
 *   - frontend/src/i18n/locales/{en,zh-TW}/{common,auth}.json (resource bundles)
 *   - frontend/src/main.tsx (imports this before render)
 *   - frontend/src/components/UserMenu.tsx (locale switcher writes ipa-locale)
 *   - frontend/src/components/Sidebar.tsx + routes.config.ts (nav labels via t())
 */

import i18n from "i18next";
import LanguageDetector from "i18next-browser-languagedetector";
import { initReactI18next } from "react-i18next";

import authEn from "./locales/en/auth.json";
import commonEn from "./locales/en/common.json";
import authZhTW from "./locales/zh-TW/auth.json";
import commonZhTW from "./locales/zh-TW/common.json";

/** localStorage key the detector reads + the switcher writes. */
export const LOCALE_STORAGE_KEY = "ipa-locale";

export interface SupportedLocale {
  /** BCP-47-ish id used by i18next (`en` | `zh-TW`). */
  id: string;
  /** Native label shown in the switcher. */
  label: string;
}

export const SUPPORTED_LOCALES: SupportedLocale[] = [
  { id: "en", label: "English" },
  { id: "zh-TW", label: "繁體中文" },
];

export const resources = {
  en: { common: commonEn, auth: authEn },
  "zh-TW": { common: commonZhTW, auth: authZhTW },
};

void i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources,
    fallbackLng: "en",
    supportedLngs: SUPPORTED_LOCALES.map((l) => l.id),
    ns: ["common", "auth"],
    defaultNS: "common",
    detection: {
      order: ["localStorage", "navigator"],
      lookupLocalStorage: LOCALE_STORAGE_KEY,
      caches: ["localStorage"],
    },
    interpolation: { escapeValue: false },
    react: { useSuspense: false },
  });

export default i18n;
