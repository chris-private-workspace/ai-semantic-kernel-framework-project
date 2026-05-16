/* global React */
// i18n aligned to react-i18next + common.json namespace from the IPA Platform repo.
// Keys follow shell.tsx / Sidebar.tsx convention: common.nav.* / common.shell.*

const LOCALES = {
  // Shell (matches frontend/src/i18n/locales/{en,zh-TW}/common.json)
  "shell.brand":           { en: "IPA Platform",    zh: "IPA 平台" },
  "shell.brandSub":        { en: "V2 · loop-first", zh: "V2 · 迴圈優先" },
  "shell.comingSoon":      { en: "Coming soon",     zh: "即將推出" },
  "shell.primaryNavigation": { en: "Primary navigation", zh: "主導覽" },
  "shell.expandSidebar":   { en: "Expand sidebar",  zh: "展開側邊欄" },
  "shell.collapseSidebar": { en: "Collapse sidebar", zh: "收合側邊欄" },
  "shell.search":          { en: "Search runs, sessions, audit_id…", zh: "搜尋 run / session / audit_id…" },
  "shell.proposalsBadge":  { en: "Design proposals", zh: "設計提案" },
  // Category headers
  "nav.category.operations":    { en: "Operations",    zh: "操作" },
  "nav.category.business":      { en: "Business",      zh: "業務" },
  "nav.category.governance":    { en: "Governance",    zh: "治理" },
  "nav.category.observability": { en: "Observability", zh: "可觀測性" },
  "nav.category.resources":     { en: "Resources",     zh: "資源" },
  "nav.category.admin":         { en: "Admin",         zh: "管理" },
  // Operations
  "nav.overview":         { en: "Overview",        zh: "總覽" },
  "nav.chatV2":           { en: "Chat (V2)",       zh: "對話 V2" },
  "nav.costDashboard":    { en: "Cost Dashboard",  zh: "成本儀表板" },
  "nav.slaDashboard":     { en: "SLA Dashboard",   zh: "SLA 儀表板" },
  // Admin
  "nav.tenants":          { en: "Tenants",         zh: "租戶" },
  "nav.tenantSettings":   { en: "Tenant Settings", zh: "租戶設定" },
  "nav.auditLog":         { en: "Audit Log",       zh: "稽核日誌" },
  "nav.featureFlags":     { en: "Feature Flags",   zh: "功能開關" },
  "nav.governance":       { en: "Governance",      zh: "治理" },
  "nav.verification":     { en: "Verification",    zh: "驗證" },
  "nav.loopDebug":        { en: "Loop Debug",      zh: "Loop 偵錯" },
  "nav.memory":           { en: "Memory",          zh: "記憶" },
  // Settings
  "nav.userProfile":      { en: "User Profile",    zh: "個人資料" },
  "nav.mfaSettings":      { en: "MFA Settings",    zh: "多因素驗證" },
  // Proposals (out of registry — design proposals)
  "nav.incidents":        { en: "Business Domains", zh: "業務領域" },
  "nav.tools":            { en: "Tool Registry",   zh: "工具註冊表" },
  "nav.sseInspector":     { en: "SSE Inspector",   zh: "SSE 檢視" },
  "nav.subagentTree":     { en: "Subagent Tree",   zh: "子代理樹" },
  "nav.devui":            { en: "Dev UI",          zh: "開發者 UI" },
  "nav.stateInspector":   { en: "State Inspector", zh: "狀態檢視" },
  "nav.compaction":       { en: "Compaction",      zh: "上下文壓縮" },
  "nav.workflows":        { en: "Workflows",       zh: "工作流程" },
  "nav.errorPolicy":      { en: "Error Policy",    zh: "錯誤策略" },
  "nav.rbac":             { en: "RBAC",            zh: "權限控制" },
  "nav.jitRetrieval":     { en: "JIT Retrieval",   zh: "即時檢索" },
  "nav.cacheManager":     { en: "Cache Manager",   zh: "快取管理" },
  "nav.redaction":        { en: "Redaction",       zh: "敏感資料遮罩" },
  "nav.tenantOnboarding": { en: "Onboard Tenant",  zh: "新增租戶" },
  "nav.pricing":          { en: "Pricing",         zh: "計價模型" },
  "nav.orchestrator":     { en: "Orchestrator",    zh: "編排主代理" },
  "nav.subagents":        { en: "Subagents",       zh: "子代理註冊" },
  "nav.models":           { en: "LLM Models",      zh: "LLM 模型" },
  // Page titles (used by Topbar crumb)
  "page.chatV2.title":         { en: "Operator Chat",   zh: "操作員對話" },
  "page.costDashboard.title":  { en: "Cost Ledger",     zh: "成本帳本" },
  "page.slaDashboard.title":   { en: "SLA Dashboard",   zh: "SLA 儀表板" },
  "page.tenants.title":        { en: "Tenants",         zh: "租戶" },
  "page.tenantSettings.title": { en: "Tenant Settings", zh: "租戶設定" },
  "page.auditLog.title":       { en: "Audit Chain",     zh: "稽核鏈" },
  "page.featureFlags.title":   { en: "Feature Flags",   zh: "功能開關" },
  "page.governance.title":     { en: "HITL Governance", zh: "HITL 治理" },
  "page.verification.title":   { en: "Verification",    zh: "驗證" },
  "page.loopDebug.title":      { en: "Loop Visualizer", zh: "Loop 視覺化" },
  "page.memory.title":         { en: "Memory Layers",   zh: "記憶層" },
  "page.profile.title":        { en: "User Profile",    zh: "個人資料" },
  "page.mfa.title":            { en: "MFA Settings",    zh: "多因素驗證" },
  // Proposals
  "page.incidents.title":      { en: "Business Domains", zh: "業務領域" },
  "page.tools.title":          { en: "Tool Registry",    zh: "工具註冊表" },
  "page.sseInspector.title":   { en: "SSE Inspector",    zh: "SSE 串流檢視" },
  "page.subagentTree.title":   { en: "Subagent Tree",    zh: "子代理樹" },
  "page.devui.title":          { en: "Developer UI",     zh: "開發者 UI" },
  "page.stateInspector.title": { en: "State Inspector",  zh: "狀態檢視" },
  "page.compaction.title":     { en: "Context Compaction", zh: "上下文壓縮" },
  "page.workflows.title":      { en: "Workflows",        zh: "工作流程" },
  "page.errorPolicy.title":    { en: "Error Policy",     zh: "錯誤策略" },
  "page.rbac.title":           { en: "RBAC",             zh: "權限控制" },
  "page.jitRetrieval.title":   { en: "JIT Retrieval",    zh: "即時檢索" },
  "page.cacheManager.title":   { en: "Cache Manager",    zh: "快取管理" },
  "page.redaction.title":      { en: "Observation Masker", zh: "觀察遮罩" },
  "page.tenantOnboarding.title": { en: "Onboard Tenant", zh: "新增租戶" },
  "page.pricing.title":        { en: "Pricing Model",    zh: "計價模型" },
  "page.domain.title":         { en: "Domain Detail",    zh: "領域詳情" },
  "page.orchestrator.title":   { en: "Orchestrator Agent", zh: "編排主代理" },
  "page.subagents.title":      { en: "Subagent Registry", zh: "子代理註冊" },
  "page.models.title":         { en: "LLM Models",       zh: "LLM 模型管理" },

  // Overview dashboard
  "page.overview.title":               { en: "Overview",                       zh: "總覽" },
  "page.overview.subtitle":            { en: "Cross-cut view across all 12 categories",  zh: "12 範疇全景視圖" },
  "page.overview.export":              { en: "Export snapshot",                zh: "匯出快照" },
  "page.overview.newChat":             { en: "New chat",                       zh: "新對話" },
  "page.overview.kpi.activeSessions":  { en: "Active sessions",                zh: "進行中 session" },
  "page.overview.kpi.hitlPending":     { en: "HITL pending",                   zh: "待審批" },
  "page.overview.kpi.costMtd":         { en: "Cost · MTD",                     zh: "本月成本" },
  "page.overview.kpi.slaP95":          { en: "Loop p95",                       zh: "Loop p95" },
  "page.overview.activeLoops.title":   { en: "Active agent loops",             zh: "進行中 Agent Loop" },
  "page.overview.activeLoops.subtitle": { en: "click row to inspect",          zh: "點列檢視" },
  "page.overview.openLoopDebug":       { en: "Open loop debug",                zh: "開啟 Loop 偵錯" },
  "page.overview.hitlQueue.title":     { en: "HITL approvals queue",           zh: "HITL 審批佇列" },
  "page.overview.review":              { en: "Review",                         zh: "審批" },
  "page.overview.costBurn.title":      { en: "Cost burn vs budget",            zh: "成本進度 vs 預算" },
  "page.overview.costBurn.subtitle":   { en: "30-day window · acme-prod",      zh: "30 日窗口 · acme-prod" },
  "page.overview.providers.title":     { en: "LLM provider health",            zh: "LLM 供應商狀態" },
  "page.overview.details":             { en: "Details",                        zh: "詳情" },
  "page.overview.incidents.title":     { en: "Recent incidents",               zh: "近期事件" },
  "page.overview.allIncidents":        { en: "All incidents",                  zh: "所有事件" },
  "page.overview.errors.title":        { en: "Error rate · 24h",               zh: "錯誤率 · 24 小時" },
  "page.overview.errors.subtitle":     { en: "errors per hour, all loops",     zh: "每小時錯誤數,所有 loop" },
  "page.overview.errorPolicy":         { en: "Error policy",                   zh: "錯誤策略" },
  "page.overview.quick.newChat":       { en: "Start new chat",                 zh: "開始新對話" },
  "page.overview.quick.newChatSub":    { en: "Operator chat with default agent",  zh: "以預設 agent 對話" },
  "page.overview.quick.review":        { en: "Review pending HITL",            zh: "審批待處理 HITL" },
  "page.overview.quick.reviewSub":     { en: "3 approvals · 1 critical",       zh: "3 個審批 · 1 件 critical" },
  "page.overview.quick.tenants":       { en: "Manage tenants",                 zh: "管理租戶" },
  "page.overview.quick.tenantsSub":    { en: "3 active tenants",               zh: "3 個 active 租戶" },
  "page.overview.quick.verification":  { en: "Verification results",           zh: "驗證結果" },
  "page.overview.quick.verificationSub":{ en: "Rules + LLM-judge outcomes",    zh: "規則與 LLM-judge 結果" },

  // Auth — shared
  "auth.back":                         { en: "Back",          zh: "上一步" },
  "auth.continue":                     { en: "Continue",      zh: "繼續" },
  // Auth — register
  "auth.register.title":               { en: "Create your workspace",        zh: "建立工作區" },
  "auth.register.subtitle":            { en: "Self-serve onboarding · 5 mins · no credit card",  zh: "自助申請 · 5 分鐘 · 免綁卡" },
  "auth.register.step1":               { en: "Identity",      zh: "身分" },
  "auth.register.step2":               { en: "Organization",  zh: "組織" },
  "auth.register.step3":               { en: "Plan",          zh: "方案" },
  "auth.register.step4":               { en: "Confirm",       zh: "確認" },
  "auth.register.workEmail":           { en: "Work email",    zh: "工作信箱" },
  "auth.register.fullName":            { en: "Full name",     zh: "姓名" },
  "auth.register.companyName":         { en: "Company name",  zh: "公司名稱" },
  "auth.register.tenantSlug":          { en: "Tenant subdomain",  zh: "租戶子網域" },
  "auth.register.tenantSlugHelp":      { en: "Letters / digits / hyphens · cannot change later",  zh: "字母 / 數字 / 連字號 · 之後無法修改" },
  "auth.register.region":              { en: "Data residency region",  zh: "資料駐留地區" },
  "auth.register.size":                { en: "Company size",  zh: "公司規模" },
  "auth.register.almostDone":          { en: "Review and create",  zh: "確認並建立" },
  "auth.register.terms":               { en: "I agree to the Terms of Service and Privacy Policy",  zh: "我同意服務條款與隱私政策" },
  "auth.register.verifyHint":          { en: "We'll send a verification link to your work email before activating the tenant.",  zh: "啟用租戶前,系統會寄出驗證連結到您的工作信箱。" },
  "auth.register.create":              { en: "Create workspace",  zh: "建立工作區" },
  "auth.register.alreadyHave":         { en: "Already have a workspace?",  zh: "已經有工作區?" },
  "auth.register.signIn":              { en: "Sign in",       zh: "登入" },
  "auth.register.ssoHint":             { en: "After tenant creation, you can configure SAML / OIDC SSO.",  zh: "建立租戶後可設定 SAML / OIDC SSO。" },
  // Auth — invite
  "auth.invite.title":                 { en: "You're invited to acme-prod",  zh: "您被邀請加入 acme-prod" },
  "auth.invite.subtitle":              { en: "Finish setting up your account to start.",  zh: "完成帳戶設定即可開始。" },
  "auth.invite.fullName":              { en: "Full name",     zh: "姓名" },
  "auth.invite.password":              { en: "Set password",  zh: "設定密碼" },
  "auth.invite.passwordHint":          { en: "12+ chars · used only if SSO is unavailable",  zh: "12 字元以上 · 僅在 SSO 不可用時使用" },
  "auth.invite.accept":                { en: "Accept invitation",  zh: "接受邀請" },
  "auth.invite.mfaHint":               { en: "MFA is required by tenant policy — set it up next.",  zh: "依租戶政策需設定 MFA — 下一步即可完成。" },
  "auth.invite.foot":                  { en: "Need to forward this invite? Ask dan@acme.com to resend.",  zh: "需要轉發邀請?請聯絡 dan@acme.com 重發。" },
  // Auth — MFA
  "auth.mfa.title":                    { en: "Two-factor verification",  zh: "二階段驗證" },
  "auth.mfa.totpSub":                  { en: "Enter the 6-digit code from your authenticator app.",  zh: "輸入驗證器 App 的 6 位數字。" },
  "auth.mfa.webauthnSub":              { en: "Touch your security key when it lights up.",  zh: "安全金鑰閃爍時請觸碰。" },
  "auth.mfa.verify":                   { en: "Verify and continue",  zh: "驗證並繼續" },
  "auth.mfa.webauthnHint":             { en: "Insert your YubiKey or use the platform authenticator on your device.",  zh: "插入 YubiKey 或使用裝置內建驗證器。" },
  "auth.mfa.simulate":                 { en: "Simulate success (prototype)",  zh: "模擬成功(原型)" },
  "auth.mfa.recoveryCode":             { en: "Use recovery code instead",  zh: "改用復原碼" },
  "auth.mfa.foot":                     { en: "Lost your device?",  zh: "遺失裝置?" },
  "auth.mfa.help":                     { en: "Contact your admin",  zh: "聯絡管理員" },
  // Auth — expired
  "auth.expired.title":                { en: "Your session expired",  zh: "登入逾時" },
  "auth.expired.subtitle":             { en: "For security, the platform signs you out after 24 hours of inactivity. Sign in again to resume.",  zh: "為了安全,連續 24 小時無操作會自動登出。重新登入即可繼續。" },
  "auth.expired.signInAgain":          { en: "Sign in again",  zh: "重新登入" },
  "auth.expired.resume":               { en: "Resume session",  zh: "繼續 session" },
  "auth.expired.dataHint":             { en: "Your in-flight chats and pending HITL approvals are preserved.",  zh: "進行中的對話與待審批的 HITL 都已保留。" },

  // Command palette
  "cmdk.placeholder":                  { en: "Search pages, tenants, sessions, run commands…",  zh: "搜尋頁面 / 租戶 / session / 執行指令…" },
  "cmdk.group.actions":                { en: "Actions",   zh: "動作" },
  "cmdk.group.pages":                  { en: "Pages",     zh: "頁面" },
  "cmdk.group.tenants":                { en: "Tenants",   zh: "租戶" },
  "cmdk.group.sessions":               { en: "Sessions",  zh: "Session" },
  "cmdk.noResults":                    { en: "No results — try a different query",  zh: "沒有結果 — 換個關鍵字試試" },

  // Notifications
  "notif.title":                       { en: "Notifications",  zh: "通知" },
  "notif.new":                         { en: "new",            zh: "新" },
  "notif.markAll":                     { en: "Mark all as read",  zh: "全部標為已讀" },
  "notif.tab.all":                     { en: "All",            zh: "全部" },
  "notif.tab.unread":                  { en: "Unread",         zh: "未讀" },
  "notif.empty":                       { en: "You're all caught up.",  zh: "目前沒有未讀通知。" },
  "notif.viewAll":                     { en: "View in audit log",  zh: "在稽核日誌中查看" },
  "notif.prefs":                       { en: "Preferences",    zh: "通知偏好" },

  // User menu
  "usermenu.switchTenant":             { en: "Switch tenant",  zh: "切換租戶" },
  "usermenu.profile":                  { en: "Profile",        zh: "個人資料" },
  "usermenu.mfa":                      { en: "MFA settings",   zh: "MFA 設定" },
  "usermenu.preferences":              { en: "Preferences",    zh: "偏好設定" },
  "usermenu.help":                     { en: "Help & shortcuts",  zh: "說明與快捷鍵" },
  "usermenu.role":                     { en: "Role",           zh: "角色" },
  "usermenu.region":                   { en: "Region",         zh: "區域" },
  "usermenu.logout":                   { en: "Sign out",       zh: "登出" },
};

const locale = () => document.documentElement.dataset.locale || "en";

function t(key) {
  const e = LOCALES[key];
  if (!e) return key;
  return e[locale()] || e.en || key;
}

function Tr({ k, en, zh }) {
  if (k) return t(k);
  return (locale() === "zh" ? zh : en) || en || zh || "";
}

Object.assign(window, { LOCALES, t, Tr });
