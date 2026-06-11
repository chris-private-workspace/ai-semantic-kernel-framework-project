# 📝 JSDoc 標準模板庫

> **用途**: 提供各種文件類型的 JSDoc 註釋標準模板
> **語言**: 繁體中文
> **格式**: JSDoc Style
> **路徑格式**: 相對路徑 (從專案根目錄)

---

## 📋 目錄

1. [API Router 模板](#1-api-router-模板)
2. [React Page 模板](#2-react-page-模板)
3. [React Component 模板](#3-react-component-模板)
4. [UI Component 模板](#4-ui-component-模板)
5. [Utility/Lib 模板](#5-utilitylib-模板)
6. [Hook 模板](#6-hook-模板)
7. [Type Definition 模板](#7-type-definition-模板)
8. [Auth/Config 模板](#8-authconfig-模板)

---

## 1. API Router 模板

### 完整範例: `budgetPool.ts`

```typescript
/**
 * @fileoverview Budget Pool Router - 預算池管理 API
 *
 * @description
 * 提供預算池的完整 CRUD 操作和查詢功能。
 * 預算池是整個專案流程的起點，用於管理財年預算分配。
 * 支援自動建立預算類別、即時使用率計算和級聯刪除檢查。
 *
 * @module api/routers/budgetPool
 *
 * @features
 * - 建立預算池並自動建立預算類別
 * - 查詢預算池列表（支援分頁、排序、搜尋）
 * - 查詢單一預算池詳情（包含使用率計算）
 * - 更新預算池資訊和預算類別
 * - 刪除預算池（級聯刪除檢查）
 * - 即時計算預算使用率和健康狀態
 *
 * @procedures
 * - create: 建立新預算池
 * - getAll: 查詢預算池列表
 * - getById: 查詢單一預算池
 * - update: 更新預算池
 * - delete: 刪除預算池
 *
 * @dependencies
 * - Prisma Client: 資料庫操作
 * - Zod: 輸入驗證和類型推斷
 * - tRPC: API 框架和類型安全
 *
 * @related
 * - packages/db/prisma/schema.prisma - BudgetPool 資料模型
 * - packages/api/src/routers/project.ts - 關聯的專案 Router
 * - apps/web/src/app/[locale]/budget-pools/page.tsx - 預算池列表頁面
 * - apps/web/src/components/budget-pool/BudgetPoolForm.tsx - 預算池表單組件
 *
 * @author IT Department
 * @since Epic 3 - Budget and Project Setup
 * @lastModified 2025-11-14
 */

import { z } from "zod";
import { createTRPCRouter, protectedProcedure } from "../trpc";

export const budgetPoolRouter = createTRPCRouter({
  // ... router implementation
});
```

### 簡化模板 (複製使用)

```typescript
/**
 * @fileoverview [功能名稱] Router - [簡短描述]
 *
 * @description
 * [詳細功能說明 2-3 行]
 *
 * @module api/routers/[fileName]
 *
 * @features
 * - [主要功能 1]
 * - [主要功能 2]
 * - [主要功能 3]
 *
 * @procedures
 * - [procedure1]: [說明]
 * - [procedure2]: [說明]
 *
 * @dependencies
 * - Prisma Client: 資料庫操作
 * - Zod: 輸入驗證
 * - tRPC: API 框架
 *
 * @related
 * - packages/db/prisma/schema.prisma - [Model] 資料模型
 * - packages/api/src/routers/[related].ts - 相關 Router
 * - apps/web/src/app/[locale]/[module]/page.tsx - 列表頁面
 *
 * @author IT Department
 * @since Epic X - [功能名稱]
 * @lastModified YYYY-MM-DD
 */
```

---

## 2. React Page 模板

### 完整範例: `projects/page.tsx`

```typescript
/**
 * @fileoverview Projects List Page - 專案列表頁面
 *
 * @description
 * 顯示用戶有權訪問的所有專案列表，支援搜尋、過濾、排序和分頁功能。
 * Project Manager 只能看到自己管理的專案，Supervisor 可以看到所有專案。
 * 整合 tRPC 查詢和 React Query 進行資料快取和即時更新。
 *
 * @page /[locale]/projects
 *
 * @features
 * - 專案列表展示（卡片或表格視圖）
 * - 即時搜尋（專案名稱、描述）
 * - 多條件過濾（預算池、狀態、財年）
 * - 排序功能（名稱、建立日期、預算）
 * - 分頁導航（每頁 10/20/50 項）
 * - 快速操作（查看詳情、編輯、刪除）
 * - 角色權限控制（RBAC）
 *
 * @permissions
 * - ProjectManager: 查看自己的專案
 * - Supervisor: 查看所有專案
 * - Admin: 查看所有專案 + 管理權限
 *
 * @routing
 * - 列表頁: /projects
 * - 建立頁: /projects/new
 * - 詳情頁: /projects/[id]
 * - 編輯頁: /projects/[id]/edit
 *
 * @stateManagement
 * - URL Query Params: 搜尋、過濾、排序、分頁狀態
 * - React Query: 資料快取和即時更新
 * - Zustand: 視圖模式（卡片/表格）
 *
 * @dependencies
 * - next-intl: 國際化支援
 * - @tanstack/react-query: tRPC 查詢和快取
 * - shadcn/ui: Table, Card, Input, Select, Pagination
 *
 * @related
 * - packages/api/src/routers/project.ts - 專案 API Router
 * - apps/web/src/components/project/ProjectForm.tsx - 專案表單組件
 * - apps/web/src/app/[locale]/projects/[id]/page.tsx - 專案詳情頁面
 *
 * @author IT Department
 * @since Epic 2 - Project Management
 * @lastModified 2025-10-20
 */

import { Suspense } from 'react';
import { getTranslations } from 'next-intl/server';
// ... imports

export default async function ProjectsPage() {
  // ... page implementation
}
```

### 簡化模板

```typescript
/**
 * @fileoverview [功能名稱] Page - [頁面說明]
 *
 * @description
 * [詳細功能說明 2-3 行]
 *
 * @page /[locale]/[route]
 *
 * @features
 * - [主要功能 1]
 * - [主要功能 2]
 * - [主要功能 3]
 *
 * @permissions (如需要)
 * - [角色]: [權限說明]
 *
 * @routing (如有多個相關路由)
 * - [描述]: [路由]
 *
 * @dependencies
 * - next-intl: 國際化
 * - @tanstack/react-query: tRPC 查詢
 * - shadcn/ui: [使用的組件]
 *
 * @related
 * - packages/api/src/routers/[router].ts - API Router
 * - apps/web/src/components/[module]/[Component].tsx - 主要組件
 *
 * @author IT Department
 * @since Epic X - [功能名稱]
 * @lastModified YYYY-MM-DD
 */
```

---

## 3. React Component 模板

### 完整範例: `ProjectForm.tsx`

```typescript
/**
 * @fileoverview Project Form Component - 專案建立/編輯表單
 *
 * @description
 * 統一的專案表單組件，支援建立新專案和編輯現有專案兩種模式。
 * 使用 React Hook Form + Zod 進行表單驗證，整合 shadcn/ui 設計系統。
 * 提供即時驗證、自動儲存草稿、錯誤處理和成功提示功能。
 *
 * @component ProjectForm
 *
 * @features
 * - 表單模式切換（建立 vs 編輯）
 * - 即時表單驗證（Zod schema）
 * - 預算池選擇（Combobox 組件）
 * - 專案經理和主管選擇（User Combobox）
 * - 日期範圍選擇（Date Picker）
 * - 國際化支援（繁中/英文）
 * - 錯誤處理和成功提示（Toast）
 * - 自動儲存草稿（可選）
 *
 * @props
 * @param {Object} props - 組件屬性
 * @param {'create' | 'edit'} props.mode - 表單模式
 * @param {Project} [props.defaultValues] - 編輯模式的預設值
 * @param {() => void} [props.onSuccess] - 成功回調函數
 * @param {() => void} [props.onCancel] - 取消回調函數
 *
 * @example
 * ```tsx
 * // 建立模式
 * <ProjectForm mode="create" onSuccess={() => router.push('/projects')} />
 *
 * // 編輯模式
 * <ProjectForm
 *   mode="edit"
 *   defaultValues={project}
 *   onSuccess={handleUpdateSuccess}
 * />
 * ```
 *
 * @dependencies
 * - react-hook-form: 表單狀態管理和驗證
 * - @hookform/resolvers/zod: Zod 整合
 * - @tanstack/react-query: tRPC 查詢和 mutation
 * - shadcn/ui: Form, Input, Select, Button
 * - next-intl: 國際化
 *
 * @related
 * - packages/api/src/routers/project.ts - 專案 API Router
 * - apps/web/src/components/ui/combobox.tsx - Combobox 組件
 * - apps/web/src/app/[locale]/projects/new/page.tsx - 建立頁面
 * - apps/web/src/app/[locale]/projects/[id]/edit/page.tsx - 編輯頁面
 *
 * @author IT Department
 * @since Epic 2 - Project Management
 * @lastModified 2025-11-13 (FIX-093: 修復 Combobox 選取功能)
 */

'use client';

import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
// ... imports

export function ProjectForm({ mode, defaultValues, onSuccess, onCancel }: ProjectFormProps) {
  // ... component implementation
}
```

### 簡化模板

```typescript
/**
 * @fileoverview [組件名稱] - [簡短說明]
 *
 * @description
 * [詳細功能說明 2-3 行]
 *
 * @component [ComponentName]
 *
 * @features
 * - [主要功能 1]
 * - [主要功能 2]
 * - [主要功能 3]
 *
 * @props
 * @param {Object} props - 組件屬性
 * @param {Type} props.propName - 屬性說明
 *
 * @example (可選)
 * ```tsx
 * <ComponentName prop1="value" prop2={data} />
 * ```
 *
 * @dependencies
 * - [依賴1]: [用途]
 * - [依賴2]: [用途]
 *
 * @related
 * - [相對路徑] - [文件說明]
 *
 * @author IT Department
 * @since Epic X - [功能名稱]
 * @lastModified YYYY-MM-DD
 */
```

---

## 4. UI Component 模板

### 完整範例: `combobox.tsx`

```typescript
/**
 * @fileoverview Combobox Component - 可搜尋下拉選單組件
 *
 * @description
 * 支援搜尋和鍵盤導航的下拉選單組件，使用 Radix UI Popover 實現。
 * 移除了原本的 cmdk 依賴，改用原生 HTML + React 狀態管理，
 * 提供更穩定的 UUID 值選取功能和更好的性能。
 *
 * @component Combobox
 *
 * @features
 * - 即時搜尋過濾（客戶端過濾）
 * - 鍵盤導航支援（上下鍵、Enter 選取）
 * - 支援 UUID 值和字串值
 * - 可自訂佔位符和空狀態文字
 * - 整合 Radix UI Popover
 * - 使用 useMemo 優化過濾性能
 *
 * @props
 * @param {Object} props - 組件屬性
 * @param {Array<{value: string, label: string}>} props.options - 選項列表
 * @param {string} props.value - 當前選中的值
 * @param {(value: string) => void} props.onChange - 值變更回調
 * @param {string} [props.placeholder] - 佔位符文字
 * @param {string} [props.emptyText] - 無結果時顯示的文字
 *
 * @example
 * ```tsx
 * <Combobox
 *   options={budgetPools.map(bp => ({ value: bp.id, label: bp.name }))}
 *   value={selectedId}
 *   onChange={setSelectedId}
 *   placeholder="選擇預算池"
 *   emptyText="找不到預算池"
 * />
 * ```
 *
 * @dependencies
 * - @radix-ui/react-popover: Popover 彈出視窗
 * - lucide-react: 圖示庫 (ChevronsUpDown, Check)
 * - React: useMemo, useState
 *
 * @related
 * - apps/web/src/components/ui/popover.tsx - Popover 組件
 * - apps/web/src/components/ui/button.tsx - Button 組件
 * - apps/web/src/components/project/ProjectForm.tsx - 使用範例
 *
 * @author IT Department
 * @since Epic 3 - Budget and Project Setup
 * @lastModified 2025-11-13 (FIX-093: 完全重寫，移除 cmdk 依賴)
 */

'use client';

import * as React from "react";
import { Popover, PopoverContent, PopoverTrigger } from "./popover";
// ... imports

export function Combobox({ options, value, onChange, placeholder, emptyText }: ComboboxProps) {
  // ... component implementation
}
```

### 簡化模板 (shadcn/ui 組件)

```typescript
/**
 * @fileoverview [組件名稱] - shadcn/ui [組件類型]
 *
 * @description
 * 基於 Radix UI 的 [組件類型] 組件，提供 [主要功能]。
 * 遵循 shadcn/ui 設計系統規範，支援主題切換和無障礙性。
 *
 * @component [ComponentName]
 *
 * @features
 * - [主要功能 1]
 * - [主要功能 2]
 * - 主題支援 (Light/Dark/System)
 * - 完整的無障礙性支援
 *
 * @props
 * @param {Object} props - 組件屬性 (繼承自 Radix UI)
 *
 * @example
 * ```tsx
 * <ComponentName>...</ComponentName>
 * ```
 *
 * @dependencies
 * - @radix-ui/react-[component]: 底層 Radix UI 組件
 * - class-variance-authority: 樣式變體管理
 *
 * @related
 * - apps/web/src/lib/utils.ts - cn() 工具函數
 *
 * @author IT Department
 * @since Post-MVP - Design System Migration
 * @lastModified YYYY-MM-DD
 */
```

---

## 5. Utility/Lib 模板

### 完整範例: `utils.ts`

```typescript
/**
 * @fileoverview Utility Functions - 通用工具函數庫
 *
 * @description
 * 提供跨專案使用的通用工具函數，包含樣式處理、日期格式化、
 * 數據轉換等功能。所有函數都經過單元測試驗證。
 *
 * @module lib/utils
 *
 * @functions
 * - cn(): Tailwind CSS 類別合併工具
 * - formatCurrency(): 貨幣格式化（支援多語言）
 * - formatDate(): 日期格式化（支援多時區）
 * - debounce(): 防抖函數
 * - calculateBudgetUtilization(): 預算使用率計算
 *
 * @example
 * ```typescript
 * // 合併 CSS 類別
 * const className = cn('base-class', isActive && 'active-class');
 *
 * // 格式化貨幣
 * const price = formatCurrency(12345.67, 'zh-TW'); // "NT$ 12,345.67"
 *
 * // 格式化日期
 * const date = formatDate(new Date(), 'yyyy-MM-dd'); // "2025-11-14"
 * ```
 *
 * @dependencies
 * - clsx: 類別名稱處理
 * - tailwind-merge: Tailwind CSS 衝突解決
 * - date-fns: 日期處理
 *
 * @testing
 * - 單元測試: lib/utils.test.ts
 * - 測試覆蓋率: >90%
 *
 * @related
 * - apps/web/src/components/ui/*.tsx - UI 組件 (使用 cn)
 *
 * @author IT Department
 * @since Epic 1 - Platform Foundation
 * @lastModified 2025-10-15
 */

import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * 合併 Tailwind CSS 類別名稱
 * @param inputs - 類別名稱或條件類別
 * @returns 合併後的類別字串
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// ... other utility functions
```

### 簡化模板

```typescript
/**
 * @fileoverview [工具名稱] - [簡短說明]
 *
 * @description
 * [詳細功能說明 2-3 行]
 *
 * @module [模組路徑]
 *
 * @functions
 * - [function1](): [說明]
 * - [function2](): [說明]
 *
 * @example
 * ```typescript
 * // 使用範例
 * ```
 *
 * @dependencies
 * - [依賴1]: [用途]
 *
 * @related
 * - [相對路徑] - [文件說明]
 *
 * @author IT Department
 * @since Epic X - [功能名稱]
 * @lastModified YYYY-MM-DD
 */
```

---

## 6. Hook 模板

### 完整範例: `useDebounce.ts`

```typescript
/**
 * @fileoverview useDebounce Hook - 防抖 Hook
 *
 * @description
 * 提供值的防抖功能，在使用者停止輸入後延遲更新值。
 * 常用於搜尋輸入框，減少 API 請求頻率，提升性能。
 *
 * @hook useDebounce
 *
 * @features
 * - 自訂延遲時間（預設 500ms）
 * - 自動清理定時器（避免記憶體洩漏）
 * - TypeScript 泛型支援（任意值類型）
 * - 即時值和防抖值同步
 *
 * @params
 * @param {T} value - 需要防抖的值
 * @param {number} [delay=500] - 延遲時間（毫秒）
 * @returns {T} 防抖後的值
 *
 * @example
 * ```typescript
 * const SearchInput = () => {
 *   const [search, setSearch] = useState('');
 *   const debouncedSearch = useDebounce(search, 500);
 *
 *   useEffect(() => {
 *     // 只在停止輸入 500ms 後觸發
 *     if (debouncedSearch) {
 *       fetchResults(debouncedSearch);
 *     }
 *   }, [debouncedSearch]);
 *
 *   return <input value={search} onChange={(e) => setSearch(e.target.value)} />;
 * };
 * ```
 *
 * @dependencies
 * - React: useState, useEffect
 *
 * @related
 * - apps/web/src/components/budget-pool/BudgetPoolFilters.tsx - 使用範例
 * - apps/web/src/components/project/ProjectFilters.tsx - 使用範例
 *
 * @author IT Department
 * @since Epic 3 - Budget and Project Setup
 * @lastModified 2025-10-15
 */

import { useState, useEffect } from 'react';

export function useDebounce<T>(value: T, delay: number = 500): T {
  // ... hook implementation
}
```

### 簡化模板

```typescript
/**
 * @fileoverview [Hook 名稱] - [簡短說明]
 *
 * @description
 * [詳細功能說明 2-3 行]
 *
 * @hook [hookName]
 *
 * @features
 * - [主要功能 1]
 * - [主要功能 2]
 *
 * @params
 * @param {Type} paramName - 參數說明
 * @returns {Type} 回傳值說明
 *
 * @example
 * ```typescript
 * const result = useHookName(param);
 * ```
 *
 * @dependencies
 * - React: [使用的 Hooks]
 *
 * @related
 * - [相對路徑] - [使用範例]
 *
 * @author IT Department
 * @since Epic X - [功能名稱]
 * @lastModified YYYY-MM-DD
 */
```

---

## 7. Type Definition 模板

### 完整範例: `project.types.ts`

```typescript
/**
 * @fileoverview Project Types - 專案相關類型定義
 *
 * @description
 * 定義專案模組使用的所有 TypeScript 類型、介面和類型守衛。
 * 這些類型與 Prisma schema 保持同步，並擴展前端特定的需求。
 *
 * @module types/project
 *
 * @types
 * - Project: 專案基礎類型（同步 Prisma）
 * - ProjectWithRelations: 包含關聯資料的專案類型
 * - ProjectFormData: 表單輸入資料類型
 * - ProjectStatus: 專案狀態枚舉
 * - ProjectFilters: 列表過濾條件類型
 * - ProjectSortOptions: 排序選項類型
 *
 * @typeGuards
 * - isProject(): 類型守衛函數
 * - isValidProjectStatus(): 狀態驗證函數
 *
 * @example
 * ```typescript
 * // 使用類型定義
 * const project: ProjectWithRelations = {
 *   id: '123',
 *   name: 'New Project',
 *   budgetPool: { ... },
 *   manager: { ... }
 * };
 *
 * // 使用類型守衛
 * if (isProject(data)) {
 *   console.log(data.name);
 * }
 * ```
 *
 * @dependencies
 * - Prisma Client: 基礎類型來源
 * - Zod: 運行時驗證（可選）
 *
 * @related
 * - packages/db/prisma/schema.prisma - Prisma Project 模型
 * - packages/api/src/routers/project.ts - 專案 API
 * - apps/web/src/components/project/ProjectForm.tsx - 專案表單
 *
 * @author IT Department
 * @since Epic 2 - Project Management
 * @lastModified 2025-10-15
 */

import type { Project as PrismaProject, BudgetPool, User } from '@itpm/db';

/**
 * 專案基礎類型（繼承 Prisma 生成的類型）
 */
export type Project = PrismaProject;

// ... more type definitions
```

### 簡化模板

```typescript
/**
 * @fileoverview [模組] Types - [類型定義說明]
 *
 * @description
 * [詳細功能說明 2-3 行]
 *
 * @module types/[moduleName]
 *
 * @types
 * - [TypeName]: [說明]
 *
 * @typeGuards (可選)
 * - [guardName](): [說明]
 *
 * @example
 * ```typescript
 * const data: TypeName = { ... };
 * ```
 *
 * @dependencies
 * - [依賴]: [用途]
 *
 * @related
 * - [相對路徑] - [文件說明]
 *
 * @author IT Department
 * @since Epic X - [功能名稱]
 * @lastModified YYYY-MM-DD
 */
```

---

## 8. Auth/Config 模板

### 完整範例: `auth/index.ts`

```typescript
/**
 * @fileoverview NextAuth Configuration - 認證系統配置
 *
 * @description
 * NextAuth.js 認證配置，整合 Azure AD B2C SSO 和 Email/Password 雙認證。
 * 提供完整的用戶認證、會話管理和權限控制功能。
 *
 * @module auth
 *
 * @features
 * - Azure AD B2C SSO 整合
 * - Email/Password 本地認證
 * - JWT 會話管理（24 小時）
 * - 自動用戶同步（Azure AD → 本地資料庫）
 * - 角色權限映射（RBAC）
 * - 會話延長和自動登出
 *
 * @providers
 * - AzureADB2C: Azure AD B2C SSO
 * - Credentials: Email/Password 認證
 *
 * @callbacks
 * - signIn: 登入驗證和用戶同步
 * - jwt: JWT token 更新
 * - session: 會話資料注入
 *
 * @environment
 * - NEXTAUTH_SECRET: JWT 簽名密鑰
 * - NEXTAUTH_URL: 應用程式 URL
 * - AZURE_AD_B2C_*: Azure AD B2C 配置
 *
 * @dependencies
 * - next-auth: 認證框架
 * - @prisma/client: 資料庫操作
 * - bcryptjs: 密碼加密
 *
 * @related
 * - packages/db/prisma/schema.prisma - User, Account, Session 模型
 * - packages/api/src/trpc.ts - 認證中介軟體
 * - apps/web/src/app/[locale]/login/page.tsx - 登入頁面
 *
 * @author IT Department
 * @since Epic 1 - Azure AD B2C Authentication
 * @lastModified 2025-09-15
 */

import { type NextAuthOptions } from "next-auth";
import AzureADB2CProvider from "next-auth/providers/azure-ad-b2c";
// ... imports

export const authOptions: NextAuthOptions = {
  // ... configuration
};
```

### 簡化模板

```typescript
/**
 * @fileoverview [配置名稱] - [簡短說明]
 *
 * @description
 * [詳細功能說明 2-3 行]
 *
 * @module [moduleName]
 *
 * @features
 * - [主要功能 1]
 * - [主要功能 2]
 *
 * @environment (如需要)
 * - [ENV_VAR]: [說明]
 *
 * @dependencies
 * - [依賴]: [用途]
 *
 * @related
 * - [相對路徑] - [文件說明]
 *
 * @author IT Department
 * @since Epic X - [功能名稱]
 * @lastModified YYYY-MM-DD
 */
```

---

## 📝 使用指南

### 選擇模板
1. 根據文件類型選擇對應的模板
2. 複製「簡化模板」到文件頂部
3. 替換所有 `[佔位符]` 為實際內容

### 填寫要點
- **@fileoverview**: 簡短標題，格式：`[名稱] - [類型/用途]`
- **@description**: 2-4 行詳細說明，描述主要功能和職責
- **@features**: 3-6 個主要功能點，使用 bullet list
- **@related**: 列出 2-5 個最相關的文件，使用相對路徑
- **@since**: 參考 `MASTER-ROADMAP.md` 確認 Epic 名稱
- **@lastModified**: 使用 `YYYY-MM-DD` 格式

### 質量檢查
- [ ] JSDoc 位於文件最頂部（import 之前）
- [ ] 所有必要欄位都已填寫
- [ ] 中文描述清晰準確
- [ ] @related 路徑正確且文件存在
- [ ] 格式符合 JSDoc 標準

---

**維護者**: AI Assistant
**創建日期**: 2025-11-14
**版本**: V1.0
