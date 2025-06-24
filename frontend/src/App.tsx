import React, { useState, useEffect } from 'react';

// =============================================================================
// TYPES
// =============================================================================

interface User {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  role : 'basic' | 'pro';
}

interface Stock {
  id: number;
  symbol: string;
  name: string;
  sector: string;
  current_price: number;
}

interface StockQuote {
  stock: Stock;
  price: number;
  change: number;
  change_percent: number;
  volume: number;
  timestamp: string;
}

interface Portfolio {
  holdings: PortfolioHolding[];
  summary: {
    total_value: number;
    total_cost: number;
    total_gain_loss: number;
    total_gain_loss_percent: number;
    holdings_count: number;
  };
}

interface PortfolioHolding {
  stock_symbol: string;
  stock_name: string;
  quantity: number;
  average_price: number;
  current_price: number;
  market_value: number;
  cost_basis: number;
  unrealized_gain_loss: number;
  unrealized_gain_loss_percent: number;
}

interface Transaction {
  id: number;
  stock_symbol: string;
  stock_name: string;
  transaction_type: 'buy' | 'sell';
  quantity: number;
  price: number;
  total_amount: number;
  timestamp: string;
}

// =============================================================================
// API SERVICE
// =============================================================================

class ApiService {
  private baseURL = 'http://localhost:5500/api';

  private async request(endpoint: string, options: RequestInit = {}): Promise<any> {
    const token = localStorage.getItem('access_token');
    const headers = {
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Bearer ${token}` }),
      ...options.headers,
    };

    try {
      const response = await fetch(`${this.baseURL}${endpoint}`, {
        ...options,
        headers,
      });

      const data = await response.json();

      if (!response.ok) {
        // Try to refresh token if access token expired
        if (response.status === 401 && token) {
          const refreshed = await this.refreshToken();
          if (refreshed) {
            // Retry the original request with new token
            return this.request(endpoint, options);
          }
        }
        throw new Error(data.message || 'Request failed');
      }

      return data;
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }

  private async refreshToken(): Promise<boolean> {
    try {
      const refreshToken = localStorage.getItem('refresh_token');
      if (!refreshToken) return false;

      const response = await fetch(`${this.baseURL}/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });

      if (response.ok) {
        const data = await response.json();
        localStorage.setItem('access_token', data.data.tokens.access_token);
        localStorage.setItem('refresh_token', data.data.tokens.refresh_token);
        return true;
      }
    } catch (error) {
      console.error('Token refresh failed:', error);
    }

    // Clear tokens if refresh failed
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    return false;
  }

  async login(email: string, password: string) {
    const data = await this.request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    
    localStorage.setItem('access_token', data.data.tokens.access_token);
    localStorage.setItem('refresh_token', data.data.tokens.refresh_token);
    
    return data;
  }

  async register(userData: any) {
    const data = await this.request('/auth/register', {
      method: 'POST',
      body: JSON.stringify(userData),
    });
    
    localStorage.setItem('access_token', data.data.tokens.access_token);
    localStorage.setItem('refresh_token', data.data.tokens.refresh_token);
    
    return data;
  }

  async getProfile() {
    return this.request('/auth/profile');
  }

  async getStocks(search?: string) {
    const params = search ? `?search=${encodeURIComponent(search)}` : '';
    return this.request(`/stocks${params}`);
  }

  async getStockQuote(symbol: string) {
    return this.request(`/stocks/${symbol}/quote`);
  }

  async getPortfolio() {
    return this.request('/portfolio');
  }

  async buyStock(symbol: string, quantity: number) {
    return this.request('/portfolio/buy', {
      method: 'POST',
      body: JSON.stringify({ symbol, quantity }),
    });
  }

  async sellStock(symbol: string, quantity: number) {
    return this.request('/portfolio/sell', {
      method: 'POST',
      body: JSON.stringify({ symbol, quantity }),
    });
  }

  async getTransactions() {
    return this.request('/portfolio/transactions');
  }

  async getStockHistory(symbol: string) {
    return this.request(`/stocks/${symbol}/history`);
  }

}


const api = new ApiService();

// =============================================================================
// COMPONENTS
// =============================================================================

// Auth Component
const AuthForm: React.FC<{ onLogin: (user: User) => void }> = ({ onLogin }) => {
  const [isLogin, setIsLogin] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    first_name: '',
    last_name: '',
    role: 'basic'
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = isLogin 
        ? await api.login(formData.email, formData.password)
        : await api.register(formData);
      
      onLogin(response.data.user);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 flex items-center justify-center">
      <div className="bg-white p-8 rounded-lg shadow-md w-full max-w-md">
        <h2 className="text-2xl font-bold mb-6 text-center">
          {isLogin ? 'Login' : 'Register'}
        </h2>
        
        {error && (
          <div className="mb-4 p-3 bg-red-100 border border-red-300 text-red-700 rounded">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          {!isLogin && (
            <div className="grid grid-cols-2 gap-4 mb-4">
              <input
                type="text"
                placeholder="First Name"
                value={formData.first_name}
                onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:border-blue-500"
                required={!isLogin}
              />
              <input
                type="text"
                placeholder="Last Name"
                value={formData.last_name}
                onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:border-blue-500"
                required={!isLogin}
              />
            </div>
          )}
          {!isLogin && (
              <div className="mb-4">
                <label className="block mb-1 font-medium text-sm text-gray-700">
                  Account Type
                </label>
                <select
                    value={formData.role}
                    onChange={e =>
                        setFormData({
                          ...formData,
                          role: e.target.value as 'basic' | 'pro',
                        })
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:border-blue-500"
                >
                  <option value="basic">Basic</option>
                  <option value="pro">Pro</option>
                </select>
              </div>
          )}

          <div className="mb-4">
            <input
              type="email"
              placeholder="Email"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:border-blue-500"
              required
            />
          </div>

          <div className="mb-6">
            <input
              type="password"
              placeholder="Password"
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:border-blue-500"
              required
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded disabled:opacity-50"
          >
            {loading ? 'Processing...' : (isLogin ? 'Login' : 'Register')}
          </button>
        </form>

        <p className="mt-4 text-center text-gray-600">
          {isLogin ? "Don't have an account? " : "Already have an account? "}
          <button
            onClick={() => setIsLogin(!isLogin)}
            className="text-blue-500 hover:text-blue-700 underline"
          >
            {isLogin ? 'Register' : 'Login'}
          </button>
        </p>
      </div>
    </div>
  );
};

// Stock List Component
const StockList: React.FC<{
    onTradeClick(stock: Stock): void;
    onHistoryClick(symbol: string): void;
   }> = ({ onTradeClick, onHistoryClick }) => {
  const [stocks, setStocks] = useState<Stock[]>([]);
  const [quotes, setQuotes] = useState<{ [symbol: string]: StockQuote }>({});
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadStocks();
  }, [search]);

  useEffect(() => {
    if (stocks.length > 0) {
      loadQuotes();
      const interval = setInterval(loadQuotes, 3000);
      return () => clearInterval(interval);
    }
  }, [stocks]);

  const loadStocks = async () => {
    try {
      const response = await api.getStocks(search);
      setStocks(response.data.items);
    } catch (error) {
      console.error('Failed to load stocks:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadQuotes = async () => {
    const quotePromises = stocks.map(async (stock) => {
      try {
        const response = await api.getStockQuote(stock.symbol);
        return { symbol: stock.symbol, quote: response.data.quote };
      } catch (error) {
        return null;
      }
    });

    const results = await Promise.all(quotePromises);
    const newQuotes: { [symbol: string]: StockQuote } = {};
    
    results.forEach((result) => {
      if (result) {
        newQuotes[result.symbol] = result.quote;
      }
    });

    setQuotes(newQuotes);
  };

  if (loading) return <div className="text-center py-8">Loading stocks...</div>;

  return (
    <div className="bg-white rounded-lg shadow-md">
      <div className="p-4 border-b">
        <h2 className="text-xl font-bold mb-4">Live Stock Market</h2>
        <input
          type="text"
          placeholder="Search stocks..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:border-blue-500"
        />
      </div>

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Symbol</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Name</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Price</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Change</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Action</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {stocks.map((stock) => {
              const quote = quotes[stock.symbol];
              const isPositive = quote ? quote.change >= 0 : false;
              
              return (
                <tr key={stock.symbol} className="hover:bg-gray-50">
                  <td className="px-4 py-4 font-medium">{stock.symbol}</td>
                  <td className="px-4 py-4">
                    <div className="text-sm text-gray-900">{stock.name}</div>
                    <div className="text-xs text-gray-500">{stock.sector}</div>
                  </td>
                  <td className="px-4 py-4">${quote ? quote.price.toFixed(2) : stock.current_price.toFixed(2)}</td>
                  <td className="px-4 py-4">
                    {quote && (
                      <span className={isPositive ? 'text-green-600' : 'text-red-600'}>
                        {isPositive ? '+' : ''}${quote.change.toFixed(2)} ({isPositive ? '+' : ''}{quote.change_percent.toFixed(2)}%)
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-4">
                    <button
                      onClick={() => onTradeClick(stock)}
                      className="text-blue-600 hover:text-blue-900 font-medium"
                    >
                      Trade
                    </button>
                    <button onClick={() => onHistoryClick(stock.symbol)}
                            className="ml-4 text-green-600 hover:text-green-900 font-medium"
                    >
                        History
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};

// Portfolio Component
const PortfolioView: React.FC = () => {
  const [portfolio, setPortfolio] = useState<Portfolio | null>(null);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [activeTab, setActiveTab] = useState<'holdings' | 'transactions'>('holdings');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [portfolioRes, transactionsRes] = await Promise.all([
        api.getPortfolio(),
        api.getTransactions()
      ]);
      
      setPortfolio(portfolioRes.data.portfolio);
      setTransactions(transactionsRes.data.items);
    } catch (error) {
      console.error('Failed to load portfolio:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="text-center py-8">Loading portfolio...</div>;
  if (!portfolio) return <div className="text-center py-8">Failed to load portfolio</div>;

  return (
    <div className="bg-white rounded-lg shadow-md">
      <div className="p-4 border-b">
        <h2 className="text-xl font-bold mb-4">Portfolio</h2>
        
        {/* Summary Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
          <div className="bg-blue-50 p-3 rounded">
            <div className="text-sm text-gray-600">Total Value</div>
            <div className="text-lg font-semibold">${portfolio.summary.total_value.toFixed(2)}</div>
          </div>
          <div className="bg-green-50 p-3 rounded">
            <div className="text-sm text-gray-600">Total Cost</div>
            <div className="text-lg font-semibold">${portfolio.summary.total_cost.toFixed(2)}</div>
          </div>
          <div className="bg-yellow-50 p-3 rounded">
            <div className="text-sm text-gray-600">Gain/Loss</div>
            <div className={`text-lg font-semibold ${portfolio.summary.total_gain_loss >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              ${portfolio.summary.total_gain_loss.toFixed(2)}
            </div>
          </div>
          <div className="bg-purple-50 p-3 rounded">
            <div className="text-sm text-gray-600">Return</div>
            <div className={`text-lg font-semibold ${portfolio.summary.total_gain_loss_percent >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {portfolio.summary.total_gain_loss_percent.toFixed(2)}%
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex space-x-4">
          <button
            onClick={() => setActiveTab('holdings')}
            className={`px-4 py-2 rounded ${activeTab === 'holdings' ? 'bg-blue-500 text-white' : 'bg-gray-200 text-gray-700'}`}
          >
            Holdings ({portfolio.summary.holdings_count})
          </button>
          <button
            onClick={() => setActiveTab('transactions')}
            className={`px-4 py-2 rounded ${activeTab === 'transactions' ? 'bg-blue-500 text-white' : 'bg-gray-200 text-gray-700'}`}
          >
            Transactions ({transactions.length})
          </button>
        </div>
      </div>

      <div className="p-4">
        {activeTab === 'holdings' ? (
          <div className="overflow-x-auto">
            {portfolio.holdings.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                No holdings yet. Start trading to build your portfolio!
              </div>
            ) : (
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Stock</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Quantity</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Avg Price</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Current</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Value</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Gain/Loss</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {portfolio.holdings.map((holding) => (
                    <tr key={holding.stock_symbol}>
                      <td className="px-4 py-4">
                        <div className="font-medium">{holding.stock_symbol}</div>
                        <div className="text-sm text-gray-500">{holding.stock_name}</div>
                      </td>
                      <td className="px-4 py-4">{holding.quantity}</td>
                      <td className="px-4 py-4">${holding.average_price.toFixed(2)}</td>
                      <td className="px-4 py-4">${holding.current_price.toFixed(2)}</td>
                      <td className="px-4 py-4">${holding.market_value.toFixed(2)}</td>
                      <td className="px-4 py-4">
                        <div className={holding.unrealized_gain_loss >= 0 ? 'text-green-600' : 'text-red-600'}>
                          ${holding.unrealized_gain_loss.toFixed(2)}
                        </div>
                        <div className={`text-sm ${holding.unrealized_gain_loss_percent >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                          {holding.unrealized_gain_loss_percent.toFixed(2)}%
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        ) : (
          <div className="overflow-x-auto">
            {transactions.length === 0 ? (
              <div className="text-center py-8 text-gray-500">No transactions yet.</div>
            ) : (
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Stock</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Quantity</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Price</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Total</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {transactions.map((transaction) => (
                    <tr key={transaction.id}>
                      <td className="px-4 py-4">{new Date(transaction.timestamp).toLocaleDateString()}</td>
                      <td className="px-4 py-4">
                        <span className={`px-2 py-1 text-xs font-semibold rounded-full ${
                          transaction.transaction_type === 'buy' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                        }`}>
                          {transaction.transaction_type.toUpperCase()}
                        </span>
                      </td>
                      <td className="px-4 py-4">
                        <div className="font-medium">{transaction.stock_symbol}</div>
                        <div className="text-sm text-gray-500">{transaction.stock_name}</div>
                      </td>
                      <td className="px-4 py-4">{transaction.quantity}</td>
                      <td className="px-4 py-4">${transaction.price.toFixed(2)}</td>
                      <td className="px-4 py-4">${transaction.total_amount.toFixed(2)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

// Trading Modal Component
const TradingModal: React.FC<{
  stock: Stock;
  onClose: () => void;
  onComplete: () => void;
}> = ({ stock, onClose, onComplete }) => {
  const [quote, setQuote] = useState<StockQuote | null>(null);
  const [tradeType, setTradeType] = useState<'buy' | 'sell'>('buy');
  const [quantity, setQuantity] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    loadQuote();
    const interval = setInterval(loadQuote, 2000);
    return () => clearInterval(interval);
  }, [stock.symbol]);

  const loadQuote = async () => {
    try {
      const response = await api.getStockQuote(stock.symbol);
      setQuote(response.data.quote);
    } catch (error) {
      console.error('Failed to load quote:', error);
    }
  };

  const handleTrade = async () => {
    if (!quote || quantity <= 0) return;

    setLoading(true);
    setError('');

    try {
      await (tradeType === 'buy' 
        ? api.buyStock(stock.symbol, quantity)
        : api.sellStock(stock.symbol, quantity));
      
      onComplete();
      onClose();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const totalAmount = quote ? quote.price * quantity : 0;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-md mx-4">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-bold">Trade {stock.symbol}</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700 text-2xl">×</button>
        </div>

        {quote && (
          <div className="mb-4 p-3 bg-gray-50 rounded">
            <div className="flex justify-between items-center">
              <div className="text-lg font-semibold">${quote.price.toFixed(2)}</div>
              <div className="text-xs text-gray-500">Live Price</div>
            </div>
            <div className={`text-sm ${quote.change >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {quote.change >= 0 ? '+' : ''}${quote.change.toFixed(2)} ({quote.change_percent.toFixed(2)}%)
            </div>
          </div>
        )}

        {error && (
          <div className="mb-4 p-3 bg-red-100 border border-red-300 text-red-700 rounded">
            {error}
          </div>
        )}

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Trade Type</label>
            <div className="flex space-x-2">
              <button
                onClick={() => setTradeType('buy')}
                className={`flex-1 py-2 px-4 rounded ${
                  tradeType === 'buy' ? 'bg-green-500 text-white' : 'bg-gray-200 text-gray-700'
                }`}
              >
                Buy
              </button>
              <button
                onClick={() => setTradeType('sell')}
                className={`flex-1 py-2 px-4 rounded ${
                  tradeType === 'sell' ? 'bg-red-500 text-white' : 'bg-gray-200 text-gray-700'
                }`}
              >
                Sell
              </button>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Quantity</label>
            <input
              type="number"
              min="1"
              value={quantity}
              onChange={(e) => setQuantity(Math.max(1, parseInt(e.target.value) || 1))}
              className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:border-blue-500"
            />
          </div>

          <div className="p-3 bg-blue-50 rounded">
            <div className="flex justify-between text-sm">
              <span>Total Amount:</span>
              <span className="font-semibold">${totalAmount.toFixed(2)}</span>
            </div>
          </div>

          <div className="flex space-x-2">
            <button
              onClick={onClose}
              className="flex-1 py-2 px-4 border border-gray-300 text-gray-700 rounded hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              onClick={handleTrade}
              disabled={loading || !quote}
              className={`flex-1 py-2 px-4 text-white rounded disabled:opacity-50 ${
                tradeType === 'buy' ? 'bg-green-500 hover:bg-green-600' : 'bg-red-500 hover:bg-red-600'
              }`}
            >
              {loading ? 'Processing...' : `${tradeType === 'buy' ? 'Buy' : 'Sell'} ${stock.symbol}`}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
// ====== NEW COMPONENT: StockHistory ======
const StockHistory: React.FC<{
  symbol: string;
  onClose: () => void;
}> = ({ symbol, onClose }) => {
  const [history, setHistory] = useState<{ date: string; price: number }[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getStockHistory(symbol)
        .then(res => setHistory(res.data.history))
        .catch(console.error)
        .finally(() => setLoading(false));
  }, [symbol]);

  return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-6 w-full max-w-lg mx-4">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-xl font-bold">History: {symbol}</h3>
            <button onClick={onClose} className="text-2xl">×</button>
          </div>
          {loading
              ? <p>Loading history…</p>
              : (
                  <div className="overflow-y-auto max-h-80">
                    <table className="w-full table-auto">
                      <thead>
                      <tr>
                        <th className="px-4 py-2 text-left">Date</th>
                        <th className="px-4 py-2 text-left">Price</th>
                      </tr>
                      </thead>
                      <tbody>
                      {history.map(h => (
                          <tr key={h.date}>
                            <td className="px-4 py-2">{h.date}</td>
                            <td className="px-4 py-2">${h.price.toFixed(2)}</td>
                          </tr>
                      ))}
                      </tbody>
                    </table>
                  </div>
              )
          }
        </div>
      </div>
  );
};



// =============================================================================
// MAIN APP
// =============================================================================

const App: React.FC = () => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'stocks' | 'portfolio'>('stocks');
  const [selectedStock, setSelectedStock] = useState<Stock | null>(null);
    const [historySymbol, setHistorySymbol] = useState<string | null>(null);

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    try {
      const token = localStorage.getItem('access_token');
      if (token) {
        const response = await api.getProfile();
        setUser(response.data.user);
      }
    } catch (error) {
      console.error('Auth check failed:', error);
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
    } finally {
      setLoading(false);
    }
  };

  const handleLogin = (userData: User) => {
    setUser(userData);
  };

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    setUser(null);
  };

  const handleTradeComplete = () => {
    // Simple refresh - in production you'd update state more elegantly
    window.location.reload();
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-100">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-500 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return <AuthForm onLogin={handleLogin} />;
  }

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-bold text-gray-800">Stock Trading Platform</h1>
              <p className="text-gray-600 flex items-center space-x-2"><span>

              Welcome, {user.first_name} {user.last_name} </span>
                <span
                  className={`px-2 py-1 text-xs font-semibold rounded ${
                       user.role === 'pro'
                       ? 'bg-green-100 text-green-800'
                              : 'bg-yellow-100 text-yellow-800'
                         }`}
                 >
                   {user.role.toUpperCase()}
                 </span>
              </p>
            </div>
            
            <div className="flex items-center space-x-4">
              <nav className="flex space-x-2">
                <button
                  onClick={() => setActiveTab('stocks')}
                  className={`px-4 py-2 rounded ${
                    activeTab === 'stocks' ? 'bg-blue-500 text-white' : 'bg-gray-200 text-gray-700'
                  }`}
                >
                  Stocks
                </button>
                <button
                  onClick={() => setActiveTab('portfolio')}
                  className={`px-4 py-2 rounded ${
                    activeTab === 'portfolio' ? 'bg-blue-500 text-white' : 'bg-gray-200 text-gray-700'
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
      <main className="max-w-7xl mx-auto px-4 py-8">
        {activeTab === 'stocks' && <StockList onTradeClick={setSelectedStock} onHistoryClick={setHistorySymbol} />}
        {activeTab === 'portfolio' && <PortfolioView />}
      </main>

      {/* Trading Modal */}
      {selectedStock && (
        <TradingModal
          stock={selectedStock}
          onClose={() => setSelectedStock(null)}
          onComplete={handleTradeComplete}
        />
      )}
      {historySymbol && (
          <StockHistory
              symbol={historySymbol}
              onClose={() => setHistorySymbol(null)}
          />
      )}
    </div>
  );
};

export default App;