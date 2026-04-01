# Backend Integration Guide for Login System

## Overview
This document specifies the API endpoints and data contracts needed to connect the frontend login system to the backend.

## Required Endpoints

### 1. Custom Credentials Login
**Endpoint**: `POST /api/auth/login`

**Request Body**:
```json
{
  "username": "john.manager",
  "password": "secure_password_123",
  "rememberMe": true
}
```

**Response (200 OK)**:
```json
{
  "success": true,
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gTWFuYWdlciIsImlhdCI6MTUxNjIzOTAyMn0.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c",
  "user": {
    "id": "user_123",
    "username": "john.manager",
    "email": "john.manager@hitachi.com",
    "name": "John Manager"
  }
}
```

**Response (401 Unauthorized)**:
```json
{
  "success": false,
  "error": "Invalid username or password"
}
```

**Frontend Code Location**: `src/pages/LoginPage.tsx` lines 38-60

### 2. SSO Authentication (Optional)
**Endpoint**: `GET /api/auth/sso`

**Behavior**: 
- Redirect user to Hitachi SSO provider OR
- Return OAuth/SAML flow URL
- User confirms auth at Hitachi systems
- Redirects back with auth code
- Backend exchanges code for JWT

**Response**:
```json
{
  "redirectUrl": "https://sso.hitachi.com/authorize?client_id=...",
  "state": "random_state_123"
}
```

**Alternative**: Redirect directly
```
Location: https://sso.hitachi.com/authorize?client_id=...&redirect_uri=http://localhost:5174/auth/callback
```

**Frontend Code Location**: `src/pages/LoginPage.tsx` lines 23-31

### 3. Logout Endpoint (For Dashboard)
**Endpoint**: `POST /api/auth/logout`

**Request**:
```
Headers: {
  Authorization: "Bearer <token>"
}
```

**Response**:
```json
{
  "success": true,
  "message": "Logged out successfully"
}
```

**Frontend Code Location**: (To be implemented in Dashboard/Header)

### 4. Token Refresh (Optional but Recommended)
**Endpoint**: `POST /api/auth/refresh`

**Request**:
```json
{
  "refreshToken": "refresh_token_xyz"
}
```

**Response**:
```json
{
  "token": "new_jwt_token...",
  "refreshToken": "new_refresh_token..."
}
```

## Implementation Checklist

### Backend Team
- [ ] POST `/api/auth/login` - Username/password validation
- [ ] User database schema and queries
- [ ] Password hashing (bcrypt recommended)
- [ ] JWT token generation (HS256 or RS256)
- [ ] Token expiration (15 min recommended)
- [ ] (Optional) SSO integration with Hitachi systems
- [ ] (Optional) Refresh token mechanism
- [ ] CORS configuration (allow localhost:5174, production domain)
- [ ] Error handling and logging
- [ ] Rate limiting on auth endpoints

### Frontend Team (Already Done)
- [x] Login UI with SSO + custom form
- [x] Form validation and error display
- [x] Loading states and user feedback
- [x] State management with AuthContext
- [x] localStorage persistence
- [ ] TODO: Update endpoints with actual URLs
- [ ] TODO: Store JWT token properly
- [ ] TODO: Add JWT to request headers
- [ ] TODO: Handle 401 responses
- [ ] TODO: Implement logout functionality
- [ ] TODO: Add token refresh logic

## API Contract Details

### User Object Format
```typescript
interface User {
  id: string
  username: string
  email: string
  name: string
}
```

### JWT Token Payload (Recommended)
```json
{
  "sub": "user_123",
  "username": "john.manager",
  "email": "john.manager@hitachi.com",
  "name": "John Manager",
  "iat": 1676000000,
  "exp": 1676003600,
  "roles": ["manager", "approver"]
}
```

### Error Response Format
```json
{
  "success": false,
  "error": "Login failed",
  "code": "INVALID_CREDENTIALS",
  "details": {
    "field": "username",
    "message": "User not found"
  }
}
```

## CORS Configuration

Add to your backend (e.g., Express.js):
```javascript
// Allow requests from frontend
const corsOptions = {
  origin: [
    'http://localhost:5174',      // Dev
    'http://localhost:5173',      // Vite fallback
    'https://yourdomain.com'      // Production
  ],
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE'],
  allowedHeaders: ['Content-Type', 'Authorization']
}

app.use(cors(corsOptions))
```

## Frontend Integration Steps

### Step 1: Update Login Handler
**File**: `src/pages/LoginPage.tsx`

Replace the mock implementation (lines 38-60):
```tsx
const handleCustomLogin = async (e: React.FormEvent) => {
  e.preventDefault()
  setError('')
  setIsLoading(true)

  try {
    const response = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        username,
        password,
        rememberMe
      })
    })

    if (!response.ok) {
      const data = await response.json()
      setError(data.error || 'Login failed')
      setIsLoading(false)
      return
    }

    const data = await response.json()
    
    // Store token
    localStorage.setItem('authToken', data.token)
    if (data.refreshToken) {
      localStorage.setItem('refreshToken', data.refreshToken)
    }
    
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

### Step 2: Update SSO Handler
**File**: `src/pages/LoginPage.tsx`

Replace the mock implementation (lines 23-31):
```tsx
const handleSSOLogin = () => {
  // Option A: Redirect to backend SSO endpoint
  window.location.href = '/api/auth/sso'
  
  // Option B: Call backend to get SSO URL
  // fetch('/api/auth/sso-url')
  //   .then(r => r.json())
  //   .then(data => window.location.href = data.redirectUrl)
}
```

### Step 3: Create API Service
Create `src/services/authService.ts`:
```typescript
export async function login(username: string, password: string) {
  const response = await fetch('/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password })
  })
  return response.json()
}

export async function logout() {
  return fetch('/api/auth/logout', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('authToken')}`
    }
  })
}

export function getAuthToken() {
  return localStorage.getItem('authToken')
}
```

### Step 4: Add JWT to API Requests
Create `src/lib/api.ts`:
```typescript
export function getAuthHeaders() {
  const token = localStorage.getItem('authToken')
  return {
    'Authorization': `Bearer ${token}`
  }
}

// Use in all API calls:
fetch('/api/evidence/list', {
  headers: getAuthHeaders()
})
```

## Security Considerations

### Frontend
- ✅ Store JWT in localStorage (accessible to JavaScript)
- ✅ Include token in all future API requests
- ✅ Clear token on logout
- ⚠️ Consider httpOnly cookies for added security (requires backend support)

### Backend (CRITICAL)
- ✅ Hash passwords with bcrypt before storage
- ✅ Use HTTPS in production
- ✅ Validate token signature and expiration
- ✅ Implement rate limiting (prevent brute force)
- ✅ Log authentication attempts
- ✅ Use secure session tokens
- ✅ Set CORS headers properly
- ✅ Validate Content-Type headers

## Testing

### Manual Testing Checklist
- [ ] Login with valid credentials → Dashboard shown
- [ ] Login with invalid credentials → Error message displayed
- [ ] Refresh page after login → Stay logged in
- [ ] Click logout → Redirected to login
- [ ] SSO button → Redirects to SSO provider
- [ ] Remember me checkbox → Saves preference
- [ ] Mobile view → Responsive layout

### Automated Testing
```bash
# Test API endpoint
curl -X POST http://localhost:3000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test"}'
```

## Troubleshooting

### "Invalid credentials" Error
- Check username/password in database
- Verify password hashing matches
- Check user is active/not deleted

### CORS Error
- Verify backend CORS configuration
- Check origin header in request
- Ensure credentials: true is set in fetch

### Token Invalid
- Check token expiration time
- Verify signature algorithm matches
- Check token payload has required fields

### "404 Not Found" on /api/auth/login
- Verify backend is running on correct port
- Check API proxy in vite.config.ts:
  ```ts
  proxy: {
    '/api': {
      target: 'http://localhost:3000',  // Update port if needed
      changeOrigin: true,
      rewrite: (path) => path.replace(/^\/api/, '')
    }
  }
  ```

## Timeline

1. **Week 1-2**: Backend team builds auth endpoints
2. **Week 2-3**: Frontend team integrates with endpoints
3. **Week 3**: QA tests login flows
4. **Week 4**: Deploy to staging/production

## Questions for Backend Team

1. What's the user database schema?
2. Will you implement SSO or just custom login?
3. What's the token expiration time?
4. Do you need refresh tokens?
5. What password complexity requirements?
6. Do you need email verification?
7. What's the password reset flow?

## Contact

For integration questions, reach out to:
- Frontend Lead: Giovanni (Task #7)
- Backend Lead: Lorenzo De Blasio (Task #6)
- Project Manager: Kiyan Saghti Jalali
