import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Eye, EyeOff, Lock, Mail, ArrowRight, ShieldCheck, KeyRound } from 'lucide-react';
import { Logo } from '../components/ui/Logo';
import { Button } from '../components/ui/Button';
import { Card, CardContent } from '../components/ui/Card';
import { useAuth } from '../context/AuthContext';

export const LoginPage: React.FC = () => {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg('');
    if (!email.trim() || !password) {
      setErrorMsg('Please enter both email and password.');
      return;
    }

    setIsLoading(true);
    try {
      const ok = await login(email, password);
      if (ok) {
        navigate('/app');
      } else {
        setErrorMsg('Invalid credentials. You can click "Use demo account" below.');
      }
    } catch {
      setErrorMsg('An unexpected error occurred. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleUseDemo = () => {
    setEmail('analyst@fraudsight.demo');
    setPassword('Demo@1234');
    setErrorMsg('');
  };

  return (
    <div className="min-h-screen bg-[#FAF9F5] flex flex-col justify-between p-4 sm:p-6 lg:p-12 text-[#141413]">
      <div className="w-full max-w-7xl mx-auto flex items-center justify-between">
        <Link to="/">
          <Logo showText={true} />
        </Link>
        <Link to="/" className="text-xs text-[#6B6A65] hover:text-[#141413] transition-colors">
          ← Back to overview
        </Link>
      </div>

      <div className="w-full max-w-md mx-auto my-12">
        <Card className="p-8 bg-white border border-[#E8E6DC] shadow-lg rounded-2xl">
          <div className="text-center mb-6">
            <div className="w-12 h-12 rounded-xl bg-[#F5E6DF] border border-[#E8C5B8] flex items-center justify-center text-[#D97757] mx-auto mb-3">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <h1 className="font-serif text-2xl font-medium text-[#141413]">Investigator Sign In</h1>
            <p className="text-xs text-[#6B6A65] mt-1">
              Access the autonomous fraud graph platform
            </p>
          </div>

          {errorMsg && (
            <div className="mb-5 p-3 rounded-xl bg-[#FBEAE7] border border-[#F5C7BE] text-xs text-[#C0392B] leading-relaxed">
              {errorMsg}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-[#141413] mb-1.5">
                Work Email Address
              </label>
              <div className="relative">
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="analyst@fraudsight.demo"
                  className="w-full px-3.5 py-2.5 pl-10 text-xs rounded-xl bg-[#FAF9F5] border border-[#E8E6DC] focus:bg-white focus:outline-hidden focus:ring-2 focus:ring-[#D97757]/30 focus:border-[#D97757] transition-all"
                  required
                />
                <Mail className="w-4 h-4 text-[#6B6A65] absolute left-3.5 top-3" />
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-[#141413] mb-1.5">
                Password
              </label>
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  className="w-full px-3.5 py-2.5 pl-10 pr-10 text-xs rounded-xl bg-[#FAF9F5] border border-[#E8E6DC] focus:bg-white focus:outline-hidden focus:ring-2 focus:ring-[#D97757]/30 focus:border-[#D97757] transition-all"
                  required
                />
                <Lock className="w-4 h-4 text-[#6B6A65] absolute left-3.5 top-3" />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3.5 top-3 text-[#6B6A65] hover:text-[#141413] transition-colors cursor-pointer"
                  tabIndex={-1}
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <Button
              type="submit"
              className="w-full mt-2"
              size="lg"
              isLoading={isLoading}
              rightIcon={<ArrowRight className="w-4 h-4" />}
            >
              Sign In to Platform
            </Button>
          </form>

          {/* Demo account credential box */}
          <div className="mt-6 pt-5 border-t border-[#E8E6DC]">
            <div className="bg-[#FAF9F5] rounded-xl p-3.5 border border-[#E8E6DC] text-xs">
              <div className="flex items-center justify-between mb-2">
                <span className="font-semibold text-[#141413] flex items-center gap-1.5">
                  <KeyRound className="w-3.5 h-3.5 text-[#D97757]" />
                  Demo Credentials
                </span>
                <button
                  type="button"
                  onClick={handleUseDemo}
                  className="text-[11px] font-medium text-[#D97757] hover:text-[#C4623F] underline cursor-pointer"
                >
                  Fill credentials
                </button>
              </div>
              <div className="text-[11px] text-[#6B6A65] space-y-1">
                <div>
                  <span className="text-[#141413] font-medium">Email:</span> analyst@fraudsight.demo
                </div>
                <div>
                  <span className="text-[#141413] font-medium">Password:</span> Demo@1234
                </div>
              </div>
            </div>

            <Button
              type="button"
              variant="secondary"
              className="w-full mt-3 text-xs"
              onClick={handleUseDemo}
            >
              Use demo account
            </Button>
          </div>
        </Card>
      </div>

      <footer className="w-full max-w-7xl mx-auto text-center text-xs text-[#6B6A65]">
        Built for the TigerGraph Hackathon • Powered by TigerGraph
      </footer>
    </div>
  );
};
