import React, { useState } from 'react';
import { apiService } from '../../services/api';
import { User, AuthTokens } from '../../types';

interface LoginFormProps {
  onLogin: (user: User, tokens: AuthTokens) => void;
  onShowRegister: () => void;
}

const LoginForm: React.FC<LoginFormProps> = ({ onLogin, onShowRegister }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await apiService.login(email, password);
      if (response.success && response.data) {
        localStorage.setItem('access_token', response.data.tokens.access_token);
        localStorage.setItem('refresh_token', response.data.tokens.refresh_token);
        onLogin(response.data.user, response.data.tokens);
      }
    } catch (err: any) {
      setError(err.message || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto mt-8 p-6 bg-white rounded-lg shadow-md">
      <h2 className="text-2xl font-bold mb-6 text-center">Login</h2>
      
      {error && (
        <div className="mb-4 p-3 bg-red-100 border border-red-300 text-red-700 rounded">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <div className="mb-4">
          <label className="block text-gray-700 text-sm font-bold mb-2">
            Email
          </label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:border-blue-500"
            required
          />
        </div>

        <div className="mb-6">
          <label className="block text-gray-700 text-sm font-bold mb-2">
            Password
          </label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:border-blue-500"
            required
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline disabled:opacity-50"
        >
          {loading ? 'Logging in...' : 'Login'}
        </button>
      </form>

      <p className="mt-4 text-center text-gray-600">
        Don't have an account?{' '}
        <button
          onClick={onShowRegister}
          className="text-blue-500 hover:text-blue-700 underline"
        >
          Register here
        </button>
      </p>

      <div className="mt-4 p-3 bg-gray-100 rounded text-sm">
        <p className="font-semibold">Demo Accounts:</p>
        <p>Admin: admin@stockapi.com</p>
        <p>User: john.doe@example.com</p>
        <p>Password: TestPassword123</p>
      </div>
    </div>
  );
};

export default LoginForm;