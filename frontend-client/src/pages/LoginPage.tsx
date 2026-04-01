import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Shield, Mail, Lock } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardHeader, CardContent, CardFooter } from '@/components/ui/card'
import { Separator } from '@/components/ui/separator'
import { useAuth } from '@/contexts/AuthContext'

export function LoginPage() {
  const navigate = useNavigate()
  const { login } = useAuth()
  const [showCustomLogin, setShowCustomLogin] = useState(false)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSSOLogin = () => {
    setIsLoading(true)
    // TODO: Integrate with actual Hitachi SSO endpoint
    // window.location.href = '/api/auth/sso'
    setTimeout(() => {
      setIsLoading(false)
      // Mock user login
      login({
        id: '1',
        username: 'manager123',
        email: 'manager@hitachi.com',
        name: 'John Manager',
      })
      navigate('/dashboard')
    }, 1000)
  }

  const handleCustomLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setIsLoading(true)

    try {
      // Validate inputs
      if (!email || !password) {
        setError('Please enter both email and password')
        setIsLoading(false)
        return
      }

      // Validate email format
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
      if (!emailRegex.test(email)) {
        setError('Please enter a valid email address')
        setIsLoading(false)
        return
      }

      // TODO: Replace with actual API call to /api/auth/login
      // const response = await fetch('/api/auth/login', {
      //   method: 'POST',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify({ email, password })
      // })
      // const data = await response.json()
      // if (response.ok) {
      //   localStorage.setItem('token', data.token)
      //   login(data.user)
      //   navigate('/dashboard')
      // } else {
      //   setError(data.message || 'Authentication failed')
      // }

      // Simulate API delay
      await new Promise((resolve) => setTimeout(resolve, 800))

      // Mock user login
      login({
        id: '1',
        username: 'manager123',
        email: email,
        name: 'Manager User',
      })
      navigate('/dashboard')
    } catch (err) {
      setError('Authentication failed. Please try again.')
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen w-full flex items-center justify-center bg-background px-4 py-8">
      <Card className="w-full max-w-md mx-4">
        {/* Header */}
        <CardHeader className="space-y-1 text-center">
          <div className="flex justify-center mb-2">
            <Shield className="w-8 h-8 text-hitachi-blue" />
          </div>
          <h1 className="text-2xl font-bold">Hitachi AI Advisor</h1>
          <p className="text-sm text-muted-foreground">
            Release Management & Approval Platform
          </p>
        </CardHeader>

        {/* Content */}
        <CardContent className="grid gap-4">
          {!showCustomLogin ? (
            <>
              {/* SSO Button */}
              <Button
                onClick={handleSSOLogin}
                disabled={isLoading}
                className="w-full bg-hitachi-blue hover:bg-hitachi-blue-light text-white hover:text-white font-semibold"
              >
                {isLoading ? 'Connecting...' : 'Sign In with Hitachi SSO'}
              </Button>

              {/* Separator with OR text */}
              <div className="flex items-center gap-2">
                <Separator className="flex-1" />
                <span className="text-xs text-muted-foreground">OR</span>
                <Separator className="flex-1" />
              </div>

              {/* Email & Password Toggle */}
              <Button
                onClick={() => setShowCustomLogin(true)}
                variant="outline"
                className="w-full"
              >
                Use Email & Password
              </Button>
            </>
          ) : (
            <>
              {/* Error Message */}
              {error && (
                <div className="bg-red-50 border border-red-200 rounded-md p-3">
                  <p className="text-sm text-red-700 font-medium">{error}</p>
                </div>
              )}

              {/* Custom Login Form */}
              <form onSubmit={handleCustomLogin} className="space-y-4">
                {/* Email Field */}
                <div className="space-y-2">
                  <Label htmlFor="email">Email Address</Label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-2.5 w-4 h-4 text-muted-foreground" />
                    <Input
                      id="email"
                      type="email"
                      placeholder="you@hitachi.com"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      disabled={isLoading}
                      className="pl-10"
                    />
                  </div>
                </div>

                {/* Password Field */}
                <div className="space-y-2">
                  <Label htmlFor="password">Password</Label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-2.5 w-4 h-4 text-muted-foreground" />
                    <Input
                      id="password"
                      type="password"
                      placeholder="••••••••"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      disabled={isLoading}
                      className="pl-10"
                    />
                  </div>
                </div>

                {/* Sign In Button */}
                <Button
                  type="submit"
                  disabled={isLoading}
                  className="w-full bg-hitachi-blue hover:bg-hitachi-blue-light text-white hover:text-white font-semibold"
                >
                  {isLoading ? 'Signing in...' : 'Sign In'}
                </Button>
              </form>

              {/* Back to SSO Button */}
              <Button
                type="button"
                onClick={() => {
                  setShowCustomLogin(false)
                  setEmail('')
                  setPassword('')
                  setError('')
                }}
                variant="outline"
                className="w-full"
                disabled={isLoading}
              >
                Back to SSO
              </Button>
            </>
          )}
        </CardContent>

        {/* Footer */}
        <CardFooter className="flex flex-col gap-2 text-center text-sm text-muted-foreground">
          <a href="#" className="hover:text-foreground transition-colors">
            Need help? Contact your system administrator
          </a>
          <p className="text-xs">© 2024 Hitachi Rail. All rights reserved.</p>
        </CardFooter>
      </Card>
    </div>
  )
}
