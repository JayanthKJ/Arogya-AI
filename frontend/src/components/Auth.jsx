import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Leaf } from 'lucide-react';

export default function Auth({ onLogin }) {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const validatePassword = (pwd) => {
    if (pwd.length < 8) return "Password must be at least 8 characters long.";
    if (!/[A-Z]/.test(pwd)) return "Password must contain at least one uppercase letter.";
    if (!/[a-z]/.test(pwd)) return "Password must contain at least one lowercase letter.";
    if (!/\d/.test(pwd)) return "Password must contain at least one number.";
    if (!/[!@#$%^&*(),.?":{}|<>]/.test(pwd)) return "Password must contain at least one special character.";
    return null;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!isLogin) {
      const passwordError = validatePassword(password);
      if (passwordError) {
        setError(passwordError);
        return;
      }
    }

    setLoading(true);

    try {
      await onLogin(email, password, isLogin);
    } catch (err) {
      setError(err.message || 'Authentication failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <div className="bg-surface rounded-xl shadow-card border border-border p-8 sm:p-10 w-full max-w-md transition-all duration-200">
        <div className="text-center mb-8">
          <div className="w-16 h-16 bg-primary rounded-xl flex items-center justify-center mx-auto mb-5 shadow-sm text-primary-foreground">
            <Leaf size={32} />
          </div>
          <h1 className="text-2xl font-bold text-foreground tracking-wide">Arogya AI</h1>
          <p className="text-muted font-medium text-sm mt-1.5 tracking-wider">HEALTH COMPANION</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="block text-sm font-semibold text-foreground mb-1.5 tracking-wide">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-4 py-3 border border-border bg-background rounded-lg focus:bg-surface focus:ring-2 focus:ring-primary focus:border-primary outline-none transition-all duration-200"
              placeholder="you@example.com"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-semibold text-foreground mb-1.5 tracking-wide">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-3 border border-border bg-background rounded-lg focus:bg-surface focus:ring-2 focus:ring-primary focus:border-primary outline-none transition-all duration-200"
              placeholder="••••••••"
              required
            />
          </div>

          {error && (
            <div className="bg-danger/10 border border-danger/20 text-danger px-4 py-3 rounded-lg text-sm font-medium animate-fade-in-up">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-primary hover:bg-primary-hover text-primary-foreground font-semibold py-3.5 rounded-lg transition-all duration-200 shadow-sm hover:shadow-md hover:-translate-y-[1px] active:scale-[0.98] disabled:opacity-70 disabled:cursor-not-allowed mt-2 tracking-wide"
          >
            {loading ? 'Please wait...' : isLogin ? 'Login' : 'Sign Up'}
          </button>
        </form>

        <div className="mt-8 text-center space-y-3">
          <button
            type="button"
            onClick={() => setIsLogin(!isLogin)}
            className="block w-full text-muted hover:text-foreground text-sm font-semibold transition-colors"
          >
            {isLogin ? "Don't have an account? Sign up" : 'Already have an account? Login'}
          </button>
          
          {isLogin && (
            <div className="text-sm font-semibold">
              <Link to="/forgot-password" className="text-muted hover:text-foreground transition-colors">
                Forgot Password?
              </Link>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}