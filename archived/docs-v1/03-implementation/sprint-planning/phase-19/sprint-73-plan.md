# Sprint 73: Token/Time Fix + Sidebar Collapse

## Sprint Overview

| Attribute | Value |
|-----------|-------|
| **Sprint Number** | 73 |
| **Phase** | 19 - UI Enhancement |
| **Duration** | 1-2 days |
| **Total Points** | 8 |
| **Focus** | Metrics display fix, Sidebar collapse functionality |

## Sprint Goals

1. Integrate `useExecutionMetrics` hook for proper timer functionality
2. Fix Time display to show actual execution duration
3. Implement collapsible Sidebar with smooth animation
4. Add collapse/expand toggle button

## Prerequisites

- Phase 18 completed
- `useExecutionMetrics` hook exists and tested
- Sidebar and AppLayout components exist

---

## Stories

### S73-1: Token/Time Metrics Fix (3 pts)

**Description**: Integrate `useExecutionMetrics` hook to fix the Time and Token display in StatusBar.

**Root Cause Analysis**:
- Time is hardcoded to `{ total: 0, isRunning: isStreaming }` in UnifiedChat.tsx
- Token depends on `TOKEN_UPDATE` SSE event which backend doesn't send
- `useExecutionMetrics` hook exists with complete timer logic but is not used

**Acceptance Criteria**:
- [ ] Import and use `useExecutionMetrics` hook in UnifiedChat
- [ ] Call `startTimer()` when `isStreaming` becomes true
- [ ] Call `stopTimer()` when `isStreaming` becomes false
- [ ] Use `time` from useExecutionMetrics in metrics object
- [ ] Time displays correctly: 0ms -> 1.5s -> 2m 30s

**Technical Details**:
```tsx
// frontend/src/pages/UnifiedChat.tsx

// Import useExecutionMetrics
import { useExecutionMetrics } from '@/hooks/useExecutionMetrics';

export function UnifiedChat() {
  // ... existing code

  // Add useExecutionMetrics hook
  const {
    time: executionTime,
    startTimer,
    stopTimer,
    resetTimer,
  } = useExecutionMetrics();

  // Start/stop timer based on streaming state
  useEffect(() => {
    if (isStreaming) {
      startTimer();
    } else {
      stopTimer();
    }
  }, [isStreaming, startTimer, stopTimer]);

  // Update metrics object to use executionTime
  const metrics: ExecutionMetrics = useMemo(() => ({
    tokens: {
      used: tokenUsage.used,
      limit: tokenUsage.limit,
      percentage: (tokenUsage.used / tokenUsage.limit) * 100,
    },
    time: executionTime,  // Changed from hardcoded { total: 0, ... }
    toolCallCount: toolCalls.length,
    messageCount: messages.length,
  }), [tokenUsage, executionTime, toolCalls.length, messages.length]);

  // ... rest of component
}
```

**Files to Modify**:
- `frontend/src/pages/UnifiedChat.tsx`

---

### S73-2: Sidebar Collapse (5 pts)

**Description**: Implement collapsible Sidebar with toggle button and smooth animation.

**Acceptance Criteria**:
- [ ] Add `sidebarCollapsed` state to AppLayout
- [ ] Pass `isCollapsed` and `onToggle` props to Sidebar
- [ ] Sidebar width changes: 256px (expanded) -> 64px (collapsed)
- [ ] Only show icons when collapsed (hide text)
- [ ] Add toggle button at bottom of Sidebar
- [ ] Smooth transition animation (300ms)

**Technical Details**:

1. **AppLayout.tsx** - Add state and pass props:
```tsx
// frontend/src/components/layout/AppLayout.tsx
import { useState } from 'react';

export function AppLayout() {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  return (
    <div className="flex h-screen bg-gray-50">
      <Sidebar
        isCollapsed={sidebarCollapsed}
        onToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
      />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header />
        <main className="flex-1 overflow-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
```

2. **Sidebar.tsx** - Add collapse logic:
```tsx
// frontend/src/components/layout/Sidebar.tsx
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { cn } from '@/lib/utils';

interface SidebarProps {
  isCollapsed: boolean;
  onToggle: () => void;
}

export function Sidebar({ isCollapsed, onToggle }: SidebarProps) {
  return (
    <aside className={cn(
      "bg-white border-r border-gray-200 flex flex-col transition-all duration-300",
      isCollapsed ? "w-16" : "w-64"
    )}>
      {/* Logo */}
      <div className={cn(
        "h-16 flex items-center border-b border-gray-200",
        isCollapsed ? "px-4 justify-center" : "px-6"
      )}>
        <Brain className="h-8 w-8 text-primary shrink-0" />
        {!isCollapsed && (
          <span className="ml-2 font-semibold text-gray-900">
            IPA Platform
          </span>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-2 py-4 space-y-1 overflow-y-auto">
        {navigation.map((item) => (
          <NavLink
            key={item.href}
            to={item.href}
            title={isCollapsed ? item.name : undefined}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors",
                isCollapsed && "justify-center",
                isActive
                  ? "bg-primary text-white"
                  : "text-gray-700 hover:bg-gray-100"
              )
            }
          >
            <item.icon className="h-5 w-5 shrink-0" />
            {!isCollapsed && <span>{item.name}</span>}
          </NavLink>
        ))}
      </nav>

      {/* Toggle Button */}
      <div className="p-3 border-t border-gray-200">
        <button
          onClick={onToggle}
          className={cn(
            "w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium",
            "text-gray-700 hover:bg-gray-100 transition-colors",
            isCollapsed && "justify-center"
          )}
        >
          {isCollapsed ? (
            <ChevronRight className="h-5 w-5" />
          ) : (
            <>
              <ChevronLeft className="h-5 w-5" />
              <span>收起</span>
            </>
          )}
        </button>
      </div>
    </aside>
  );
}
```

**Files to Modify**:
- `frontend/src/components/layout/AppLayout.tsx`
- `frontend/src/components/layout/Sidebar.tsx`

---

## Definition of Done

- [ ] Time display updates during streaming
- [ ] Time stops when streaming ends
- [ ] Time format correct (0ms, 1.5s, 2m 30s)
- [ ] Sidebar toggles between 256px and 64px
- [ ] Collapsed Sidebar shows only icons
- [ ] Toggle button works correctly
- [ ] Animation smooth (300ms transition)
- [ ] No visual glitches or layout breaks

---

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Timer memory leak | Low | Cleanup in useEffect |
| Layout shift on collapse | Medium | Use CSS transition |
| Tooltip needed for collapsed icons | Low | Add title attribute |

---

## Sprint Velocity Reference

Frontend UI enhancements.
Expected completion: 1-2 days for 8 pts
