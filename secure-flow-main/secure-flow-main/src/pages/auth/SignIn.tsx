import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Link, useNavigate } from 'react-router-dom';
import { Shield, Mail, Lock, Eye, EyeOff, ArrowRight, Fingerprint } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Checkbox } from '@/components/ui/checkbox';
import { toast } from 'sonner';
import { authApi } from '@/services/api';

const SignIn: React.FC = () => {
  const [showPassword, setShowPassword] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [rememberMe, setRememberMe] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    try {
      const response = await authApi.login({ username: email, password });

      // Store session data
      sessionStorage.setItem('token', response.token);
      sessionStorage.setItem('session_id', response.session_id);
      sessionStorage.setItem('trust_score', response.trust_score.toString());

      // Initialize Three.js background (if applicable, via event or state)
      // customizable event to notify other components
      window.dispatchEvent(new CustomEvent('auth:login-success', { detail: response }));

      navigate('/dashboard');
    } catch (error) {
      console.error('Login failed:', error);
      toast.error("Login failed. Please check your credentials.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background flex">
      {/* Left Panel - Form */}
      <div className="flex-1 flex items-center justify-center px-6 py-12">
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5 }}
          className="w-full max-w-md"
        >
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2 mb-8">
            <div className="w-10 h-10 rounded-xl bg-primary flex items-center justify-center">
              <Shield className="w-5 h-5 text-primary-foreground" />
            </div>
            <span className="text-xl font-bold text-foreground">ShadowKey</span>
          </Link>

          {/* Header */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-foreground mb-2">Welcome back</h1>
            <p className="text-muted-foreground">
              Sign in to access your secure dashboard
            </p>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
                <Input
                  id="email"
                  type="email"
                  placeholder="you@company.com"
                  className="pl-10 h-12 rounded-xl"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="password">Password</Label>
                <a href="#" className="text-sm text-primary hover:underline">
                  Forgot password?
                </a>
              </div>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
                <Input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  placeholder="••••••••"
                  className="pl-10 pr-10 h-12 rounded-xl"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                >
                  {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
            </div>

            <div className="flex items-center space-x-2">
              <Checkbox
                id="remember"
                checked={rememberMe}
                onCheckedChange={(checked) => setRememberMe(checked as boolean)}
              />
              <Label htmlFor="remember" className="text-sm font-normal cursor-pointer">
                Remember me for 30 days
              </Label>
            </div>

            <Button
              type="submit"
              className="w-full h-12 rounded-xl bg-primary hover:bg-primary/90 text-primary-foreground text-lg"
              disabled={isLoading}
            >
              {isLoading ? (
                <motion.div
                  animate={{ rotate: 360 }}
                  transition={{ repeat: Infinity, duration: 1, ease: 'linear' }}
                  className="w-5 h-5 border-2 border-primary-foreground border-t-transparent rounded-full"
                />
              ) : (
                <>
                  Sign In
                  <ArrowRight className="ml-2 w-5 h-5" />
                </>
              )}
            </Button>
          </form>

          {/* Security notice */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3 }}
            className="mt-6 p-4 bg-accent rounded-xl flex items-start gap-3"
          >
            <Fingerprint className="w-5 h-5 text-primary shrink-0 mt-0.5" />
            <p className="text-sm text-accent-foreground">
              Your typing patterns will be analyzed for continuous authentication after sign-in.
            </p>
          </motion.div>

          {/* Sign up link */}
          <p className="mt-8 text-center text-muted-foreground">
            Don't have an account?{' '}
            <Link to="/auth/sign-up" className="text-primary hover:underline font-medium">
              Request access
            </Link>
          </p>
        </motion.div>
      </div>

      {/* Right Panel - Visual */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.8 }}
        className="hidden lg:flex flex-1 bg-primary/5 items-center justify-center p-12"
      >
        <div className="max-w-lg text-center">
          <motion.div
            initial={{ scale: 0.8 }}
            animate={{ scale: 1 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="w-32 h-32 rounded-3xl bg-primary/10 flex items-center justify-center mx-auto mb-8"
          >
            <Shield className="w-16 h-16 text-primary" />
          </motion.div>
          <h2 className="text-2xl font-bold text-foreground mb-4">
            Continuous Authentication
          </h2>
          <p className="text-muted-foreground">
            Your identity is verified continuously through behavioral biometrics,
            ensuring security without interrupting your workflow.
          </p>

          <div className="mt-12 grid grid-cols-3 gap-4">
            <div className="p-4 bg-background rounded-xl">
              <p className="text-2xl font-bold text-primary">99.9%</p>
              <p className="text-sm text-muted-foreground">Accuracy</p>
            </div>
            <div className="p-4 bg-background rounded-xl">
              <p className="text-2xl font-bold text-primary">&lt;50ms</p>
              <p className="text-sm text-muted-foreground">Latency</p>
            </div>
            <div className="p-4 bg-background rounded-xl">
              <p className="text-2xl font-bold text-primary">24/7</p>
              <p className="text-sm text-muted-foreground">Protection</p>
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  );
};

export default SignIn;
