# Sprint 74: Chat History Panel

## Sprint Overview

| Attribute | Value |
|-----------|-------|
| **Sprint Number** | 74 |
| **Phase** | 19 - UI Enhancement |
| **Duration** | 2-3 days |
| **Total Points** | 13 |
| **Focus** | Chat history panel, thread management, layout integration |

## Sprint Goals

1. Create ChatHistoryPanel component for conversation history
2. Implement useChatThreads hook for thread management
3. Integrate history panel into UnifiedChat layout
4. Enable thread switching and creation

## Prerequisites

- Sprint 73 completed
- UnifiedChat page exists with working chat
- localStorage available for persistence

---

## Stories

### S74-1: ChatHistoryPanel Component (5 pts)

**Description**: Create a conversation history panel component similar to ChatGPT's sidebar.

**Acceptance Criteria**:
- [ ] Display list of conversation threads
- [ ] Show thread title, last message preview, timestamp
- [ ] Highlight active/selected thread
- [ ] "New Chat" button at top
- [ ] Delete thread button (with confirmation)
- [ ] Collapsible panel with toggle button
- [ ] Smooth animations

**Technical Details**:
```tsx
// frontend/src/components/unified-chat/ChatHistoryPanel.tsx

import { Plus, MessageSquare, Trash2, ChevronLeft, ChevronRight } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { cn } from '@/lib/utils';
import { formatRelativeTime } from '@/lib/utils';

export interface ChatThread {
  id: string;
  title: string;
  lastMessage?: string;
  updatedAt: string;
  messageCount: number;
}

interface ChatHistoryPanelProps {
  threads: ChatThread[];
  activeThreadId: string | null;
  onSelectThread: (id: string) => void;
  onNewThread: () => void;
  onDeleteThread: (id: string) => void;
  isCollapsed?: boolean;
  onToggle?: () => void;
}

export function ChatHistoryPanel({
  threads,
  activeThreadId,
  onSelectThread,
  onNewThread,
  onDeleteThread,
  isCollapsed = false,
  onToggle,
}: ChatHistoryPanelProps) {
  return (
    <div className={cn(
      "border-r border-gray-200 flex flex-col bg-gray-50 transition-all duration-300",
      isCollapsed ? "w-0 overflow-hidden" : "w-64"
    )}>
      {/* Header with New Chat button */}
      <div className="p-3 border-b border-gray-200 flex items-center gap-2">
        <Button
          onClick={onNewThread}
          className="flex-1"
          size="sm"
        >
          <Plus className="h-4 w-4 mr-2" />
          新對話
        </Button>
        {onToggle && (
          <button
            onClick={onToggle}
            className="p-2 rounded-lg hover:bg-gray-200 transition-colors"
          >
            <ChevronLeft className="h-4 w-4" />
          </button>
        )}
      </div>

      {/* Thread List */}
      <div className="flex-1 overflow-y-auto">
        {threads.length === 0 ? (
          <div className="p-4 text-center text-gray-500 text-sm">
            暫無對話記錄
          </div>
        ) : (
          threads.map((thread) => (
            <ThreadItem
              key={thread.id}
              thread={thread}
              isActive={activeThreadId === thread.id}
              onSelect={() => onSelectThread(thread.id)}
              onDelete={() => onDeleteThread(thread.id)}
            />
          ))
        )}
      </div>
    </div>
  );
}

interface ThreadItemProps {
  thread: ChatThread;
  isActive: boolean;
  onSelect: () => void;
  onDelete: () => void;
}

function ThreadItem({ thread, isActive, onSelect, onDelete }: ThreadItemProps) {
  const [showDelete, setShowDelete] = useState(false);

  return (
    <div
      onClick={onSelect}
      onMouseEnter={() => setShowDelete(true)}
      onMouseLeave={() => setShowDelete(false)}
      className={cn(
        "p-3 cursor-pointer transition-colors relative group",
        isActive ? "bg-blue-50 border-r-2 border-blue-500" : "hover:bg-gray-100"
      )}
    >
      <div className="flex items-start gap-2">
        <MessageSquare className="h-4 w-4 text-gray-400 mt-0.5 shrink-0" />
        <div className="flex-1 min-w-0">
          <div className="font-medium text-sm text-gray-900 truncate">
            {thread.title}
          </div>
          {thread.lastMessage && (
            <div className="text-xs text-gray-500 truncate mt-0.5">
              {thread.lastMessage}
            </div>
          )}
          <div className="text-xs text-gray-400 mt-1">
            {formatRelativeTime(thread.updatedAt)}
          </div>
        </div>
      </div>

      {/* Delete button - shows on hover */}
      {showDelete && (
        <button
          onClick={(e) => {
            e.stopPropagation();
            if (confirm('確定要刪除此對話嗎？')) {
              onDelete();
            }
          }}
          className="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 rounded hover:bg-red-100 text-gray-400 hover:text-red-500 transition-colors"
        >
          <Trash2 className="h-4 w-4" />
        </button>
      )}
    </div>
  );
}
```

**Files to Create**:
- `frontend/src/components/unified-chat/ChatHistoryPanel.tsx`

**Files to Modify**:
- `frontend/src/components/unified-chat/index.ts` - Export new component

---

### S74-2: useChatThreads Hook (3 pts)

**Description**: Create a hook for managing chat threads with localStorage persistence.

**Acceptance Criteria**:
- [ ] Load threads from localStorage on mount
- [ ] Save threads to localStorage on change
- [ ] `createThread()` - Create new thread
- [ ] `updateThread()` - Update thread metadata
- [ ] `deleteThread()` - Delete thread
- [ ] Auto-generate title from first message

**Technical Details**:
```tsx
// frontend/src/hooks/useChatThreads.ts

import { useState, useEffect, useCallback } from 'react';

export interface ChatThread {
  id: string;
  title: string;
  lastMessage?: string;
  updatedAt: string;
  messageCount: number;
}

const STORAGE_KEY = 'ipa_chat_threads';
const MAX_THREADS = 50;

export function useChatThreads() {
  const [threads, setThreads] = useState<ChatThread[]>(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      return saved ? JSON.parse(saved) : [];
    } catch {
      return [];
    }
  });

  // Persist to localStorage
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(threads));
    } catch (e) {
      console.warn('Failed to save threads to localStorage:', e);
    }
  }, [threads]);

  // Create new thread
  const createThread = useCallback((title: string = '新對話'): string => {
    const newThread: ChatThread = {
      id: crypto.randomUUID(),
      title,
      updatedAt: new Date().toISOString(),
      messageCount: 0,
    };

    setThreads((prev) => {
      // Keep only MAX_THREADS
      const updated = [newThread, ...prev].slice(0, MAX_THREADS);
      return updated;
    });

    return newThread.id;
  }, []);

  // Update thread
  const updateThread = useCallback((
    id: string,
    updates: Partial<Omit<ChatThread, 'id'>>
  ) => {
    setThreads((prev) => prev.map((t) =>
      t.id === id
        ? { ...t, ...updates, updatedAt: new Date().toISOString() }
        : t
    ));
  }, []);

  // Delete thread
  const deleteThread = useCallback((id: string) => {
    setThreads((prev) => prev.filter((t) => t.id !== id));
  }, []);

  // Get thread by ID
  const getThread = useCallback((id: string): ChatThread | undefined => {
    return threads.find((t) => t.id === id);
  }, [threads]);

  // Generate title from first message
  const generateTitle = useCallback((message: string): string => {
    // Take first 30 characters, trim at word boundary
    const maxLength = 30;
    if (message.length <= maxLength) return message;

    const truncated = message.slice(0, maxLength);
    const lastSpace = truncated.lastIndexOf(' ');
    return lastSpace > 20 ? truncated.slice(0, lastSpace) + '...' : truncated + '...';
  }, []);

  return {
    threads,
    createThread,
    updateThread,
    deleteThread,
    getThread,
    generateTitle,
  };
}
```

**Files to Create**:
- `frontend/src/hooks/useChatThreads.ts`

---

### S74-3: UnifiedChat Layout Integration (5 pts)

**Description**: Integrate ChatHistoryPanel into UnifiedChat and connect thread management.

**Acceptance Criteria**:
- [ ] Add ChatHistoryPanel to left side of UnifiedChat
- [ ] Connect useChatThreads hook
- [ ] Handle new thread creation
- [ ] Handle thread selection (load history)
- [ ] Update thread metadata when messages sent
- [ ] History panel can be collapsed
- [ ] Layout responsive without breaking

**Technical Details**:
```tsx
// frontend/src/pages/UnifiedChat.tsx (updated sections)

import { ChatHistoryPanel } from '@/components/unified-chat';
import { useChatThreads } from '@/hooks/useChatThreads';

export function UnifiedChat() {
  // History panel state
  const [historyCollapsed, setHistoryCollapsed] = useState(false);

  // Thread management
  const {
    threads,
    createThread,
    updateThread,
    deleteThread,
    generateTitle,
  } = useChatThreads();

  const [activeThreadId, setActiveThreadId] = useState<string | null>(() => {
    // Try to restore last active thread
    return localStorage.getItem('ipa_active_thread_id');
  });

  // Persist active thread
  useEffect(() => {
    if (activeThreadId) {
      localStorage.setItem('ipa_active_thread_id', activeThreadId);
    }
  }, [activeThreadId]);

  // Handle new thread
  const handleNewThread = useCallback(() => {
    const newId = createThread();
    setActiveThreadId(newId);
    clearMessages();
    resetTimer();
  }, [createThread, clearMessages, resetTimer]);

  // Handle thread selection
  const handleSelectThread = useCallback((threadId: string) => {
    if (threadId === activeThreadId) return;

    setActiveThreadId(threadId);
    // Clear current messages and load history for selected thread
    clearMessages();
    // Note: loadHistory is from useUnifiedChat, pass threadId
    // You may need to update threadId in useUnifiedChat or reload
  }, [activeThreadId, clearMessages]);

  // Update thread when first message sent
  useEffect(() => {
    if (messages.length === 1 && activeThreadId) {
      const firstMessage = messages[0];
      if (firstMessage.role === 'user') {
        updateThread(activeThreadId, {
          title: generateTitle(firstMessage.content),
          lastMessage: firstMessage.content,
          messageCount: 1,
        });
      }
    } else if (messages.length > 0 && activeThreadId) {
      const lastMessage = messages[messages.length - 1];
      updateThread(activeThreadId, {
        lastMessage: lastMessage.content.slice(0, 50),
        messageCount: messages.length,
      });
    }
  }, [messages, activeThreadId, updateThread, generateTitle]);

  // Auto-create thread if none active and trying to send message
  const handleSendMessage = useCallback(async (content: string) => {
    let threadId = activeThreadId;
    if (!threadId) {
      threadId = createThread(generateTitle(content));
      setActiveThreadId(threadId);
    }
    await sendMessage(content);
  }, [activeThreadId, createThread, generateTitle, sendMessage]);

  return (
    <div className="flex h-full">
      {/* Chat History Panel */}
      <ChatHistoryPanel
        threads={threads}
        activeThreadId={activeThreadId}
        onSelectThread={handleSelectThread}
        onNewThread={handleNewThread}
        onDeleteThread={deleteThread}
        isCollapsed={historyCollapsed}
        onToggle={() => setHistoryCollapsed(!historyCollapsed)}
      />

      {/* Toggle button when collapsed */}
      {historyCollapsed && (
        <button
          onClick={() => setHistoryCollapsed(false)}
          className="p-2 border-r border-gray-200 hover:bg-gray-100"
        >
          <ChevronRight className="h-4 w-4" />
        </button>
      )}

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col min-w-0">
        <ChatHeader
          currentMode={currentMode}
          autoMode={autoMode}
          isManuallyOverridden={isManuallyOverridden}
          onModeChange={handleModeChange}
          connection={connectionStatus}
        />

        <div className="flex-1 flex overflow-hidden">
          <ChatArea
            messages={messages}
            isStreaming={isStreaming}
            pendingApprovals={pendingApprovals}
            onApprove={approveToolCall}
            onReject={rejectToolCall}
          />

          {currentMode === 'workflow' && (
            <WorkflowSidePanel
              workflowState={workflowState}
              toolCalls={toolCalls}
              checkpoints={checkpoints}
              onRestoreCheckpoint={handleRestore}
            />
          )}
        </div>

        <ChatInput
          onSend={handleSendMessage}  // Use wrapped handler
          isStreaming={isStreaming}
          onCancel={cancelStream}
        />

        <StatusBar
          mode={currentMode}
          riskLevel={dialogApproval?.risk_level}
          metrics={metrics}
          hasCheckpoint={checkpoints.length > 0}
          heartbeat={heartbeat}
        />
      </div>

      {/* Dialogs */}
      {/* ... existing dialogs ... */}
    </div>
  );
}
```

**Files to Modify**:
- `frontend/src/pages/UnifiedChat.tsx`

---

## Definition of Done

- [ ] ChatHistoryPanel displays threads
- [ ] New thread can be created
- [ ] Threads persist in localStorage
- [ ] Thread selection works
- [ ] Thread title auto-generated
- [ ] Delete thread works
- [ ] History panel can collapse
- [ ] Layout doesn't break

---

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| localStorage quota | Low | Limit to 50 threads |
| Thread state sync | Medium | Clear messages on switch |
| Layout overflow | Low | Use min-w-0 and overflow |

---

## Sprint Velocity Reference

Frontend feature addition.
Expected completion: 2-3 days for 13 pts
