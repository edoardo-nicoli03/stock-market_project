import React, { useState, useEffect } from 'react';
import { apiService } from '../../services/api';
import { Portfolio, Transaction } from '../../types';

const PortfolioView: React.FC = () => {
  const [portfolio, setPortfolio] = useState<Portfolio | null>(null);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'holdings' | 'transactions'>('holdings');

  useEffect(() => {
    loadPortfolio();
    loadTransactions();
  }, []);

  const loadPortfolio = async () => {
    try {
      const response = await apiService.getPortfolio();
      if (response.success && response.data) {
        setPortfolio(response.data.portfolio);
      }
    } catch (error) {
      console.error('Failed to load portfolio:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadTransactions = async () => {
    try {
      const response = await apiService.getTransactions();
      if (response.success && response.data) {
        setTransactions(response.data.items);
      }
    } catch (error) {
      console.error('Failed to load transactions:', error);
    }
  };

  const formatPrice = (price: number) => `$${price.toFixed(2)}`;
  const formatPercent = (percent: number) => {
    const color = percent >= 0 ? 'text-green-600' : 'text-red-600';
    const sign = percent >= 0 ? '+' : '';
    return <span className={color}>{sign}{percent.toFixed(2)}%</span>;
  };

  if (loading) {
    return <div className="text-center py-4">Loading portfolio...</div>;
  }

  if (!portfolio) {
    return <div className="text-center py-4">Failed to load portfolio</div>;
  }

  return (
    <div className="bg-white rounded-lg shadow-md">
      <div className="p-4 border-b">
        <h2 className="text-xl font-bold mb-4">Portfolio</h2>
        
        {/* Portfolio Summary */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
          <div className="bg-blue-50 p-3 rounded">
            <div className="text-sm text-gray-600">Total Value</div>
            <div className="text-lg font-semibold">{formatPrice(portfolio.summary.total_value)}</div>
          </div>
          <div className="bg-green-50 p-3 rounded">
            <div className="text-sm text-gray-600">Total Cost</div>
            <div className="text-lg font-semibold">{formatPrice(portfolio.summary.total_cost)}</div>
          </div>
          <div className="bg-yellow-50 p-3 rounded">
            <div className="text-sm text-gray-600">Gain/Loss</div>
            <div className="text-lg font-semibold">{formatPrice(portfolio.summary.total_gain_loss)}</div>
          </div>
          <div className="bg-purple-50 p-3 rounded">
            <div className="text-sm text-gray-600">Return</div>
            <div className="text-lg font-semibold">
              {formatPercent(portfolio.summary.total_gain_loss_percent)}
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex space-x-4">
          <button
            onClick={() => setActiveTab('holdings')}
            className={`px-4 py-2 rounded ${
              activeTab === 'holdings'
                ? 'bg-blue-500 text-white'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            Holdings ({portfolio.summary.holdings_count})
          </button>
          <button
            onClick={() => setActiveTab('transactions')}
            className={`px-4 py-2 rounded ${
              activeTab === 'transactions'
                ? 'bg-blue-500 text-white'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            Transactions ({transactions.length})
          </button>
        </div>
      </div>

      {/* Tab Content */}
      <div className="p-4">
        {activeTab === 'holdings' && (
          <div className="overflow-x-auto">
            {portfolio.holdings.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                No holdings yet. Start trading to build your portfolio!
              </div>
            ) : (
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Stock
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Quantity
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Avg Price
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Current Price
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Market Value
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Gain/Loss
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {portfolio.holdings.map((holding) => (
                    <tr key={holding.stock_symbol}>
                      <td className="px-4 py-4">
                        <div className="text-sm font-medium text-gray-900">
                          {holding.stock_symbol}
                        </div>
                        <div className="text-sm text-gray-500">{holding.stock_name}</div>
                      </td>
                      <td className="px-4 py-4 text-sm text-gray-900">
                        {holding.quantity}
                      </td>
                      <td className="px-4 py-4 text-sm text-gray-900">
                        {formatPrice(holding.average_price)}
                      </td>
                      <td className="px-4 py-4 text-sm text-gray-900">
                        {formatPrice(holding.current_price)}
                      </td>
                      <td className="px-4 py-4 text-sm text-gray-900">
                        {formatPrice(holding.market_value)}
                      </td>
                      <td className="px-4 py-4">
                        <div className="text-sm">
                          {formatPrice(holding.unrealized_gain_loss)}
                        </div>
                        <div className="text-sm">
                          {formatPercent(holding.unrealized_gain_loss_percent)}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        )}

        {activeTab === 'transactions' && (
          <div className="overflow-x-auto">
            {transactions.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                No transactions yet.
              </div>
            ) : (
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Date
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Type
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Stock
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Quantity
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Price
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Total
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {transactions.map((transaction) => (
                    <tr key={transaction.id}>
                      <td className="px-4 py-4 text-sm text-gray-900">
                        {new Date(transaction.timestamp).toLocaleDateString()}
                      </td>
                      <td className="px-4 py-4">
                        <span
                          className={`px-2 py-1 text-xs font-semibold rounded-full ${
                            transaction.transaction_type === 'buy'
                              ? 'bg-green-100 text-green-800'
                              : 'bg-red-100 text-red-800'
                          }`}
                        >
                          {transaction.transaction_type.toUpperCase()}
                        </span>
                      </td>
                      <td className="px-4 py-4">
                        <div className="text-sm font-medium text-gray-900">
                          {transaction.stock_symbol}
                        </div>
                        <div className="text-sm text-gray-500">{transaction.stock_name}</div>
                      </td>
                      <td className="px-4 py-4 text-sm text-gray-900">
                        {transaction.quantity}
                      </td>
                      <td className="px-4 py-4 text-sm text-gray-900">
                        {formatPrice(transaction.price)}
                      </td>
                      <td className="px-4 py-4 text-sm text-gray-900">
                        {formatPrice(transaction.total_amount)}
                      </td>
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

export default PortfolioView;