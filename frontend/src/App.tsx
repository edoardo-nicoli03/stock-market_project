import React, { useState, useEffect } from 'react';
import LoginForm from './components/Auth/LoginForm';
import PortfolioView from './components/Portfolio/PortfolioView';
import TradingModal from './components/Trading/TradingModal';
import StockList from './components/Dashboard/StockList';
import { apiService } from './services/api';
import { User, AuthTokens, Stock } from './types';
import './App.css';

const App: React.FC = () => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'stocks' | 'portfolio'>('stocks');
  const [selectedStock, setSelectedStock] = useState<Stock | null>(null);
  const [showRegister, setShowRegister] = useState(false);

  useEffect(() => {
    // Check if user is already logged in
    const token = localStorage.getItem('access_token');
    if (token) {
      loadUserProfile();
    } else {
      setLoading(false);
    }
  }, []);

  const loadUserProfile = async () => {
    try {
      const response = await apiService.getProfile();
      if (response.success && response.data) {
        setUser(response.data.user);
      } else {
        // Token might be expired
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
      }
    } catch (error) {
      console.error('Failed to load user profile:', error);
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
    } finally {
      setLoading(false);
    }
  };

  const handleLogin = (userData: User, tokens: AuthTokens) => {
    setUser(userData);
  };

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    setUser(null);
  };

  const handleStockSelect = (stock: Stock) => {
    setSelectedStock(stock);
  };

  const handleTradeComplete = () => {
    // Refresh portfolio data if on portfolio tab
    if (activeTab === 'portfolio') {
      window.location.reload(); // Simple refresh - in production, you'd update state
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-100">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-500 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="min-h-screen bg-gray-100 py-8">
        <div className="container mx-auto px-4">
          <div className="text-center mb-8">
            <h1 className="text-4xl font-bold text-gray-800 mb-2">Stock Market API</h1>
            <p className="text-gray-600">Real-time stock trading platform</p>
          </div>
          
          {showRegister ? (
            <RegisterForm onRegister={handleLogin} onShowLogin={() => setShowRegister(false)} />
          ) : (
            <LoginForm onLogin={handleLogin} onShowRegister={() => setShowRegister(true)} />
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="container mx-auto px-4 py-4">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-bold text-gray-800">Stock Market Dashboard</h1>
              <p className="text-gray-600">Welcome, {user.first_name} {user.last_name}</p>
            </div>
            
            <div className="flex items-center space-x-4">
              <nav className="flex space-x-2">
                <button
                  onClick={() => setActiveTab('stocks')}
                  className={`px-4 py-2 rounded ${
                    activeTab === 'stocks'
                      ? 'bg-blue-500 text-white'
                      : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                  }`}
                >
                  Stocks
                </button>
                <button
                  onClick={() => setActiveTab('portfolio')}
                  className={`px-4 py-2 rounded ${
                    activeTab === 'portfolio'
                      ? 'bg-blue-500 text-white'
                      : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                  }`}
                >
                  Portfolio
                </button>
              </nav>
              
              <button
                onClick={handleLogout}
                className="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        {activeTab === 'stocks' && <StockList onStockSelect={handleStockSelect} />}
        {activeTab === 'portfolio' && <PortfolioView />}
      </main>

      {/* Trading Modal */}
      {selectedStock && (
        <TradingModal
          stock={selectedStock}
          onClose={() => setSelectedStock(null)}
          onTradeComplete={handleTradeComplete}
        />
      )}
    </div>
  );
};

// Simple Register Form Component
const RegisterForm: React.FC<{
  onRegister: (user: User, tokens: AuthTokens) => void;
  onShowLogin: () => void;
}> = ({ onRegister, onShowLogin }) => {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    first_name: '',
    last_name: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await apiService.register(formData);
      if (response.success && response.data) {
        localStorage.setItem('access_token', response.data.tokens.access_token);
        localStorage.setItem('refresh_token', response.data.tokens.refresh_token);
        onRegister(response.data.user, response.data.tokens);
      }
    } catch (err: any) {
      setError(err.message || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto mt-8 p-6 bg-white rounded-lg shadow-md">
      <h2 className="text-2xl font-bold mb-6 text-center">Register</h2>
      
      {error && (
        <div className="mb-4 p-3 bg-red-100 border border-red-300 text-red-700 rounded">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <div className="grid grid-cols-2 gap-4 mb-4">
          <div>
            <label className="block text-gray-700 text-sm font-bold mb-2">
              First Name
            </label>
            <input
              type="text"
              value={formData.first_name}
              onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:border-blue-500"
              required
            />
          </div>
          <div>
            <label className="block text-gray-700 text-sm font-bold mb-2">
              Last Name
            </label>
            <input
              type="text"
              value={formData.last_name}
              onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:border-blue-500"
              required
            />
          </div>
        </div>

        <div className="mb-4">
          <label className="block text-gray-700 text-sm font-bold mb-2">
            Email
          </label>
          <input
            type="email"
            value={formData.email}
            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
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
            value={formData.password}
            onChange={(e) => setFormData({ ...formData, password: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:border-blue-500"
            required
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline disabled:opacity-50"
        >
          {loading ? 'Registering...' : 'Register'}
        </button>
      </form>

      <p className="mt-4 text-center text-gray-600">
        Already have an account?{' '}
        <button
          onClick={onShowLogin}
          className="text-blue-500 hover:text-blue-700 underline"
        >
          Login here
        </button>
      </p>
    </div>
  );
};

export default App;