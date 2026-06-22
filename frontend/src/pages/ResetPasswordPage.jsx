import { useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { authAPI } from '../services/api';

export default function ResetPasswordPage() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token');
  const navigate = useNavigate();

  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [status, setStatus] = useState(''); // 'idle', 'loading', 'success', 'error'
  const [errorMsg, setErrorMsg] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (password !== confirmPassword) {
      setStatus('error');
      setErrorMsg('Passwords do not match');
      return;
    }

    if (!token) {
      setStatus('error');
      setErrorMsg('Invalid or missing reset token');
      return;
    }

    setStatus('loading');
    setErrorMsg('');

    try {
      await authAPI.resetPassword(token, password);
      setStatus('success');
      
      // Redirect to login after a short delay
      setTimeout(() => {
        navigate('/login');
      }, 3000);
    } catch (err) {
      setStatus('error');
      setErrorMsg(err.message || 'Failed to reset password. The link might be expired.');
    }
  };

  return (
    <div className="min-h-screen bg-[#FAFAFA] flex items-center justify-center p-4">
      <div className="bg-white rounded-[24px] shadow-lg border border-gray-100 p-8 sm:p-10 w-full max-w-md transition-all duration-300">
        <div className="text-center mb-8">
          <div className="w-16 h-16 bg-teal-800 rounded-2xl flex items-center justify-center mx-auto mb-5 shadow-sm">
            <span className="text-3xl">🌿</span>
          </div>
          <h1 className="text-2xl font-bold text-gray-800 tracking-wide">Arogya AI</h1>
          <p className="text-teal-600 font-medium text-sm mt-1.5 tracking-wider">HEALTH COMPANION</p>
        </div>

        {status === 'success' ? (
          <div className="text-center">
            <div className="bg-teal-50 border border-teal-100 text-teal-700 px-4 py-3 rounded-xl text-sm font-medium animate-fade-in-up mb-6">
              Password successfully reset! Redirecting to login...
            </div>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1.5 tracking-wide">New Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-4 py-3 border border-gray-200 bg-gray-50/50 rounded-xl focus:bg-white focus:ring-2 focus:ring-teal-100 focus:border-teal-400 outline-none transition-all duration-200"
                placeholder="••••••••"
                required
                minLength={8}
              />
            </div>

            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1.5 tracking-wide">Confirm Password</label>
              <input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="w-full px-4 py-3 border border-gray-200 bg-gray-50/50 rounded-xl focus:bg-white focus:ring-2 focus:ring-teal-100 focus:border-teal-400 outline-none transition-all duration-200"
                placeholder="••••••••"
                required
                minLength={8}
              />
            </div>

            {status === 'error' && (
              <div className="bg-red-50 border border-red-100 text-red-600 px-4 py-3 rounded-xl text-sm font-medium animate-fade-in-up">
                {errorMsg}
              </div>
            )}

            <button
              type="submit"
              disabled={status === 'loading'}
              className="w-full bg-teal-700 hover:bg-teal-600 text-white font-semibold py-3.5 rounded-xl transition-all shadow-md hover:shadow-lg active:scale-[0.98] disabled:opacity-70 disabled:cursor-not-allowed mt-2 tracking-wide"
            >
              {status === 'loading' ? 'Please wait...' : 'Reset Password'}
            </button>

            <div className="mt-8 text-center space-y-3">
              <Link
                to="/login"
                className="block text-teal-600 hover:text-teal-700 text-sm font-semibold transition-colors"
              >
                Back to Login
              </Link>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
