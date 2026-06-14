/**
 * File: frontend/src/features/chat_v2/hooks/useChatSkills.ts
 * Purpose: TanStack query for the /skill-name composer picker — the tenant's effective skills.
 * Category: Frontend / chat_v2 / hooks
 * Scope: Phase 57 / Sprint 57.115 (Skills slash-command)
 *
 * Description:
 *   Fetches GET /api/v1/chat/skills (the tenant's bundled + overlay skills, name +
 *   description only) for the InputBar slash-command picker. Cached (staleTime) so
 *   typing "/" does not refetch each keystroke. Gated by `enabled` — the caller
 *   passes mode === "real_llm" (force-load is meaningful only for the real LLM;
 *   the echo mock ignores force_load_skill, so the picker is hidden in echo mode).
 *
 * Created: 2026-06-14 (Sprint 57.115)
 *
 * Modification History (newest-first):
 *   - 2026-06-14: Initial creation (Sprint 57.115)
 *
 * Related:
 *   - ../services/chatService.ts (fetchChatSkills)
 *   - ../components/SkillSlashMenu.tsx + ../components/InputBar.tsx (consumers)
 */

import { useQuery } from "@tanstack/react-query";

import { fetchChatSkills, type ChatSkill } from "../services/chatService";

export const CHAT_SKILLS_QUERY_KEY = ["chat-v2", "skills"] as const;

export function useChatSkills(enabled: boolean) {
  return useQuery<ChatSkill[], Error>({
    queryKey: CHAT_SKILLS_QUERY_KEY,
    queryFn: ({ signal }) => fetchChatSkills(signal),
    enabled,
    staleTime: 60_000,
  });
}
