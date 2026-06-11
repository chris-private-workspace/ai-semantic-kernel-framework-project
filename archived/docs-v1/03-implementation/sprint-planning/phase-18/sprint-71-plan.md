# Sprint 71: Frontend Authentication + Protected Routes

## Sprint Overview

| Attribute | Value |
|-----------|-------|
| **Sprint Number** | 71 |
| **Phase** | 18 - Authentication System |
| **Duration** | 2-3 days |
| **Total Points** | 13 |
| **Focus** | Auth store, Login/Signup pages, Route protection |

## Sprint Goals

1. Create Zustand auth store
2. Create Login and Signup pages
3. Create ProtectedRoute component
4. Add token interceptor to API client

## Prerequisites

- Sprint 70 completed (Backend auth)
- Auth API endpoints working
- Zustand pattern established

---

## Stories

### S71-1: Auth Store (Zustand) (3 pts)

**Description**: Create authentication state management with Zustand.

**Acceptance Criteria**:
- [ ] Store user, token, isAuthenticated state
- [ ] Implement login action
- [ ] Implement register action
- [ ] Implement logout action
- [ ] Persist token to localStorage
- [ ] Restore session on app load

**Technical Details**:
```typescript
// frontend/src/store/authStore.ts
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface User {
  id: string;
  email: string;
  fullName: string;
  role: string;
}

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;

  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName: string) => Promise<void>;
  logout: () => void;
  refreshSession: () => Promise<void>;
  clearError: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      login: async (email, password) => {
        set({ isLoading: true, error: null });
        try {
          const response = await fetch('/api/v1/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: new URLSearchParams({ username: email, password }),
          });

          if (!response.ok) {
            throw new Error('Invalid credentials');
          }

          const { access_token } = await response.json();

          // Fetch user info
          const meResponse = await fetch('/api/v1/auth/me', {
            headers: { Authorization: `Bearer ${access_token}` },
          });
          const user = await meResponse.json();

          set({
            token: access_token,
            user,
            isAuthenticated: true,
            isLoading: false,
          });

          // Migrate guest data
          await migrateGuestData(access_token);
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : 'Login failed',
            isLoading: false,
          });
        }
      },

      logout: () => {
        set({
          user: null,
          token: null,
          isAuthenticated: false,
        });
        localStorage.removeItem('ipa_guest_user_id');
      },
      // ... other actions
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({ token: state.token, user: state.user }),
    }
  )
);
```

**Files to Create**:
- `frontend/src/store/authStore.ts`

---

### S71-2: Login/Signup Pages (5 pts)

**Description**: Create login and signup pages with forms.

**Acceptance Criteria**:
- [ ] Create LoginPage with form
- [ ] Create SignupPage with form
- [ ] Form validation (email, password length)
- [ ] Error message display
- [ ] Loading state during submission
- [ ] Redirect to Dashboard on success

**Technical Details**:
```tsx
// frontend/src/pages/auth/LoginPage.tsx
import { useState } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { useAuthStore } from '@/store/authStore';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

export function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const { login, isLoading, error } = useAuthStore();
  const navigate = useNavigate();
  const location = useLocation();

  const from = location.state?.from?.pathname || '/dashboard';

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await login(email, password);
    if (useAuthStore.getState().isAuthenticated) {
      navigate(from, { replace: true });
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full space-y-8 p-8 bg-white rounded-xl shadow">
        <h2 className="text-2xl font-bold text-center">Sign in to IPA Platform</h2>

        {error && (
          <div className="p-3 bg-red-50 text-red-700 rounded">{error}</div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
          <Input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            minLength={8}
          />
          <Button type="submit" className="w-full" disabled={isLoading}>
            {isLoading ? 'Signing in...' : 'Sign in'}
          </Button>
        </form>

        <p className="text-center text-sm text-gray-600">
          Don't have an account? <Link to="/signup" className="text-primary">Sign up</Link>
        </p>
      </div>
    </div>
  );
}
```

**Files to Create**:
- `frontend/src/pages/auth/LoginPage.tsx`
- `frontend/src/pages/auth/SignupPage.tsx`
- `frontend/src/components/auth/LoginForm.tsx`
- `frontend/src/components/auth/SignupForm.tsx`

---

### S71-3: ProtectedRoute Component (3 pts)

**Description**: Create route protection component.

**Acceptance Criteria**:
- [ ] Check isAuthenticated state
- [ ] Show loading during session check
- [ ] Redirect to /login if not authenticated
- [ ] Preserve intended destination in state
- [ ] Wrap Dashboard routes

**Technical Details**:
```tsx
// frontend/src/components/auth/ProtectedRoute.tsx
import { Navigate, useLocation } from 'react-router-dom';
import { useAuthStore } from '@/store/authStore';
import { Loader2 } from 'lucide-react';

interface ProtectedRouteProps {
  children: React.ReactNode;
}

export function ProtectedRoute({ children }: ProtectedRouteProps) {
  const { isAuthenticated, isLoading } = useAuthStore();
  const location = useLocation();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return <>{children}</>;
}
```

```tsx
// App.tsx - Updated routes
<Route path="/login" element={<LoginPage />} />
<Route path="/signup" element={<SignupPage />} />
<Route
  element={
    <ProtectedRoute>
      <AppLayout />
    </ProtectedRoute>
  }
>
  <Route path="/" element={<Navigate to="/dashboard" replace />} />
  <Route path="dashboard" element={<DashboardPage />} />
  <Route path="chat" element={<UnifiedChat />} />
  ...
</Route>
```

**Files to Create**:
- `frontend/src/components/auth/ProtectedRoute.tsx`

**Files to Modify**:
- `frontend/src/App.tsx`

---

### S71-4: API Client Token Interceptor (2 pts)

**Description**: Add token management and 401 handling to API client.

**Acceptance Criteria**:
- [ ] Add Authorization header with token
- [ ] Handle 401 responses
- [ ] Trigger logout on 401
- [ ] Redirect to login

**Technical Details**:
```typescript
// frontend/src/api/client.ts - Updates

import { useAuthStore } from '@/store/authStore';

// Add to fetch wrapper
const authToken = useAuthStore.getState().token;
if (authToken) {
  headers['Authorization'] = `Bearer ${authToken}`;
}

// Handle 401
if (response.status === 401) {
  useAuthStore.getState().logout();
  window.location.href = '/login';
  throw new Error('Session expired');
}
```

**Files to Modify**:
- `frontend/src/api/client.ts`

---

## Definition of Done

- [ ] All 4 stories completed and tested
- [ ] Login/Signup pages work
- [ ] Protected routes redirect correctly
- [ ] Token stored and used in requests
- [ ] 401 triggers logout and redirect

---

## Sprint Velocity Reference

Frontend authentication integration.
Expected completion: 2-3 days for 13 pts
