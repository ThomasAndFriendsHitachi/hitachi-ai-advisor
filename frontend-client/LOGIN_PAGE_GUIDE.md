# Login Page Integration Guide

## Overview
A corporate, minimalist login page with dual authentication methods:
1. **Hitachi SSO** (Primary) - Corporate single sign-on
2. **Custom Credentials** (Secondary) - Username/password fallback

## File Structure
```
src/
├── pages/
│   └── LoginPage.tsx          # Login UI component
├── contexts/
│   └── AuthContext.tsx        # Auth state management
├── App.tsx                     # App router (login check)
└── main.tsx                    # AuthProvider wrapper
```

## Current Status
✅ UI complete and styled
✅ Form validation and error handling
✅ State management with React Context
✅ localStorage persistence (remembers logged-in users)
✅ Responsive design
⏳ Backend integration (TODO)

## Data Flow
```
User → LoginPage
  ├─ SSO: handleSSOLogin()   → TODO: /api/auth/sso
  └─ Custom: handleCustomLogin() → TODO: /api/auth/login
     → AuthContext.login(user)
     → stores in localStorage
     → App shows Dashboard
```

## TODO: Backend Integration

### 1. Hitachi SSO Integration
**File**: `src/pages/LoginPage.tsx` line 23

Replace the mock implementation:
```tsx
const handleSSOLogin = () => {
  // TODO: Implement
  // Option A: Redirect to SSO provider
  // window.location.href = 'https://sso.hitachi.com/authorize?redirect_uri=...'
  
  // Option B: Backend proxy (recommended)
  // window.location.href = '/api/auth/sso'
}
```

### 2. Custom Login API
**File**: `src/pages/LoginPage.tsx` line 38

Replace the mock implementation:
```tsx
const handleCustomLogin = async (e: React.FormEvent) => {
  e.preventDefault()
  setError('')
  setIsLoading(true)

  try {
    const response = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password, rememberMe }),
    })

    if (!response.ok) {
      const data = await response.json()
      setError(data.message || 'Login failed')
      return
    }

    const data = await response.json()
    
    // Store token
    localStorage.setItem('authToken', data.token)
    
    // Update auth context
    login({
      id: data.user.id,
      username: data.user.username,
      email: data.user.email,
      name: data.user.name,
    })
  } catch (err) {
    setError('Network error. Please try again.')
  } finally {
    setIsLoading(false)
  }
}
```

### 3. API Response Format (Expected)
```json
{
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "user": {
    "id": "123",
    "username": "john.manager",
    "email": "john.manager@hitachi.com",
    "name": "John Manager"
  }
}
```

## Features

### SSO Button
- Navy blue Hitachi branding (#003366)
- Shows loading state
- Clickable only when not loading
- Recommended badge

### Custom Credentials Form
- Email/username input
- Password input
- Remember me checkbox
- Error message display
- Form validation
- Toggle back to SSO

### Design Elements
- Minimalist card layout
- Gradient background
- Hitachi logo placeholder
- Clear typography hierarchy
- Accessible form labels
- Smooth transitions

## Using the Login Page

### Automatic Redirect
The app automatically redirects to login if not authenticated:
```tsx
// App.tsx
if (!isAuthenticated) {
  return <LoginPage onLoginSuccess={handleLoginSuccess} />
}
```

### Manual Testing
1. Open `http://localhost:5174/`
2. Click "Sign In with Hitachi SSO" → Mock login
3. Or click "Use Custom Credentials" → Enter any username/password
4. After login, you see the dashboard
5. Refresh page → Stays logged in (localStorage persistence)

### Logout
To implement logout, use the AuthContext in your dashboard header:
```tsx
import { useAuth } from '@/contexts/AuthContext'

export function Header() {
  const { user, logout } = useAuth()
  
  return (
    <button onClick={logout}>
      Logout ({user?.name})
    </button>
  )
}
```

## Customization

### Change Colors
**File**: `src/pages/LoginPage.tsx`

Replace `#003366` (Hitachi Blue) with your color:
```tsx
<Button className="bg-[#003366] hover:bg-[#004a7f]">
  // Change to your color
</Button>
```

### Change Branding
- Logo: Line 42 (replace gear emoji with actual logo)
- Title: Line 44
- Subtitle: Line 46
- Footer: Line 145

### Adjust Layout
All styling uses Tailwind classes - customize spacing and sizing:
```tsx
{/* Header */}
<div className="text-center mb-8">  {/* mb-8 = margin-bottom */}
  <div className="mb-4">              {/* mb-4 = margin-bottom */}
    <div className="w-12 h-12">       {/* w-12 h-12 = size */}
```

## Testing
```bash
# Run tests (if added)
npm run test

# Type check
npm run type-check

# Lint
npm run lint
```

## Next Steps
1. ✅ UI/UX complete
2. ⏳ Connect to backend auth endpoints
3. ⏳ Add forgot password flow
4. ⏳ Add multi-factor authentication (MFA)
5. ⏳ Build dashboard pages
6. ⏳ Implement logout button in header

## Support
For implementation details, see:
- shadcn/ui docs: https://ui.shadcn.com
- React Context: https://react.dev/reference/react/useContext
- Tailwind CSS: https://tailwindcss.com
