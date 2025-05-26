import React, { useState, useEffect } from 'react';
import { apiService } from '../../services/api';
import { Stock, StockQuote } from '../../types';

interface TradingModalProps {
  stock: Stock;
  onClose: () => void;
  onTradeComplete: () => void;
}

const TradingModal: React.FC<TradingModalProps> = ({ stock, onClose, onTradeComplete }) => {
  const [quote, setQuote] = useState<StockQuote | null>(null);
  const [tradeType, setTradeType] = useState<'buy' | 'sell'>('buy');
  const [quantity, setQuantity] = useState<number>(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    loadQuote();
    const interval = setInterval(loadQuote, 2000); // Update every 2 seconds
    return () => clearInterval(interval);
  }, [stock.symbol]);

  const loadQuote = async () => {
    try {
      const response = await apiService.getStockQuote(stock.symbol);
      if (response.success && response.data) {
        setQuote(response.data.quote);
      }
    } catch (error) {
      console.error('Failed to load quote:', error);
    }
  };

  const handleTrade = async () => {
    if (!quote || quantity <= 0) return;

    setLoading(true);
    setError('');

    try {
      const response = tradeType === 'buy' 
        ? await apiService.buyStock(stock.symbol, quantity)
        : await apiService.sellStock(stock.symbol, quantity);

      if (response.success) {
        onTradeComplete();
        onClose();
      } else {
        setError(response.message || 'Trade failed');
      }
    } catch (err: any) {
      setError(err.message || 'Trade failed');
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
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 text-2xl"
          >
            ×
          </button>
        </div>

        {quote && (
          <div className="mb-4 p-3 bg-gray-50 rounded">
            <div className="flex justify-between items-center">
              <div className="text-lg font-semibold">${quote.price.toFixed(2)}</div>
              <div className="text-xs text-gray-500">
                Live • {new Date(quote.timestamp).toLocaleTimeString()}
              </div>
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
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Trade Type
            </label>
            <div className="flex space-x-2">
              <button
                onClick={() => setTradeType('buy')}
                className={`flex-1 py-2 px-4 rounded ${
                  tradeType === 'buy'
                    ? 'bg-green-500 text-white'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                }`}
              >
                Buy
              </button>
              <button
                onClick={() => setTradeType('sell')}
                className={`flex-1 py-2 px-4 rounded ${
                  tradeType === 'sell'
                    ? 'bg-red-500 text-white'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                }`}
              >
                Sell
              </button>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Quantity
            </label>
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
              className={`flex-1 py-2 px-4 text-white rounded focus:outline-none disabled:opacity-50 ${
                tradeType === 'buy'
                  ? 'bg-green-500 hover:bg-green-600'
                  : 'bg-red-500 hover:bg-red-600'
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

export default TradingModal;