/**
 * File: frontend/src/features/tenant-settings/hooks/useTenantSkills.ts
 * Purpose: TanStack hooks for the per-tenant Skills catalog — read + create/update/delete.
 * Category: Frontend / tenant-settings / hooks
 * Scope: Phase 57 / Sprint 57.114 (Per-Tenant Skills Catalog tab)
 *
 * Description:
 *   One cohesive hooks module (skills is a 4-operation CRUD, unlike the 1-read +
 *   1-save policy tabs that split into two files):
 *     - useTenantSkills(tenantId)        → GET list
 *     - useTenantSkillCreate(tenantId)   → POST create
 *     - useTenantSkillUpdate(tenantId)   → PUT sparse update ({skillId, patch})
 *     - useTenantSkillDelete(tenantId)   → DELETE (skillId)
 *   Each mutation invalidates the read query on success so the list re-fetches.
 *
 * Created: 2026-06-13 (Sprint 57.114)
 *
 * Modification History (newest-first):
 *   - 2026-06-13: Initial creation (Sprint 57.114)
 *
 * Related:
 *   - ../services/tenantSettingsService.ts (fetch/create/update/deleteTenantSkill)
 *   - ../components/tabs/SkillsTab.tsx (consumer)
 */

import {
  keepPreviousData,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

import {
  createTenantSkill,
  deleteTenantSkill,
  fetchTenantSkills,
  updateTenantSkill,
} from "../services/tenantSettingsService";
import type {
  Skill,
  SkillCreateRequest,
  SkillListResponse,
  SkillUpdateRequest,
} from "../types";

export const TENANT_SKILLS_QUERY_KEY_BASE = ["tenant-settings", "skills"] as const;

export function useTenantSkills(tenantId: string) {
  return useQuery<SkillListResponse, Error>({
    queryKey: [...TENANT_SKILLS_QUERY_KEY_BASE, tenantId],
    queryFn: ({ signal }) => fetchTenantSkills(tenantId, signal),
    enabled: Boolean(tenantId),
    placeholderData: keepPreviousData,
  });
}

export function useTenantSkillCreate(tenantId: string) {
  const qc = useQueryClient();
  return useMutation<Skill, Error, SkillCreateRequest>({
    mutationFn: (payload) => createTenantSkill(tenantId, payload),
    onSuccess: () => {
      void qc.invalidateQueries({
        queryKey: [...TENANT_SKILLS_QUERY_KEY_BASE, tenantId],
      });
    },
  });
}

export function useTenantSkillUpdate(tenantId: string) {
  const qc = useQueryClient();
  return useMutation<Skill, Error, { skillId: string; patch: SkillUpdateRequest }>({
    mutationFn: ({ skillId, patch }) => updateTenantSkill(tenantId, skillId, patch),
    onSuccess: () => {
      void qc.invalidateQueries({
        queryKey: [...TENANT_SKILLS_QUERY_KEY_BASE, tenantId],
      });
    },
  });
}

export function useTenantSkillDelete(tenantId: string) {
  const qc = useQueryClient();
  return useMutation<void, Error, string>({
    mutationFn: (skillId) => deleteTenantSkill(tenantId, skillId),
    onSuccess: () => {
      void qc.invalidateQueries({
        queryKey: [...TENANT_SKILLS_QUERY_KEY_BASE, tenantId],
      });
    },
  });
}
