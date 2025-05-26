import React, { useState, useEffect } from 'react';
import { apiService } from '../../services/api';
import { Stock, StockQuote } from '../../types';

interface StockListProps {
  onStockSelect: (stock: Stock) => void;
}

const StockList: React.FC<StockListProps> = ({ onStockSelect }) => {
  const [stocks, setStocks] = useState<Stock[]>([]);
  const [quotes, setQuotes] = useState<{ [symbol: string]: StockQuote }>({});
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  useEffect(() => {
    loadStocks();
  }, [search]);

  useEffect(() => {
    // Load quotes for all stocks
    if (stocks.length > 0) {
      loadQuotes();
      // Refresh quotes every 10 seconds
      const interval = setInterval(loadQuotes, 10000);
      return () => clearInterval(interval);
    }
  }, [stocks]);

  const loadStocks = async () => {
    try {
      const response = await apiService.getStocks(1, search);
      if (response.success && response.data) {
        setStocks(response.data.items);
      }
    } catch (error) {
      console.error('Failed to load stocks:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadQuotes = async () => {
    const quotePromises = stocks.map(async (stock) => {
      try {
        const response = await apiService.getStockQuote(stock.symbol);
        if (response.success && response.data) {
          return { symbol: stock.symbol, quote: response.data.quote };
        }
      } catch (error) {
        console.error(`Failed to load quote for ${stock.symbol}:`, error);
      }
      return null;
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

  const formatPrice = (price: number) => `$${price.toFixed(2)}`;
  const formatChange = (change: number, changePercent: number) => {
    const sign = change >= 0 ? '+' : '';
    const color = change >= 0 ? 'text-green-600' : 'text-red-600';
    return (
      <span className={color}>
        {sign}{formatPrice(change)} ({sign}{changePercent.toFixed(2)}%)
      </span>
    );
  };

  if (loading) {
    return <div className="text-center py-4">Loading stocks...</div>;
  }

  return (
    <div className="bg-white rounded-lg shadow-md">
      <div className="p-4 border-b">
        <h2 className="text-xl font-bold mb-4">Stock Market</h2>
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
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Symbol
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Name
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Price
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Change
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Action
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {stocks.map((stock) => {
              const quote = quotes[stock.symbol];
              return (
                <tr key={stock.symbol} className="hover:bg-gray-50">
                  <td className="px-4 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900">
                      {stock.symbol}
                    </div>
                  </td>
                  <td className="px-4 py-4">
                    <div className="text-sm text-gray-900">{stock.name}</div>
                    <div className="text-sm text-gray-500">{stock.sector}</div>
                  </td>
                  <td className="px-4 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">
                      {quote ? formatPrice(quote.price) : '-'}
                    </div>
                  </td>
                  <td className="px-4 py-4 whitespace-nowrap">
                    {quote ? formatChange(quote.change, quote.change_percent) : '-'}
                  </td>
                  <td className="px-4 py-4 whitespace-nowrap">
                    <button
                      onClick={() => onStockSelect(stock)}
                      className="text-blue-600 hover:text-blue-900 text-sm font-medium"
                    >
                      Trade
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

export default StockList;