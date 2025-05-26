export interface User {
    id: number;
    email: string;
    first_name: string;
    last_name: string;
    is_admin: boolean;
    is_active: boolean;
    created_at: string;
    updated_at: string;
  }
  
  export interface Stock {
    id: number;
    symbol: string;
    name: string;
    sector: string;
    industry: string;
    market_cap: number;
    description: string;
    is_active: boolean;
    created_at: string;
    updated_at: string;
  }
  
  export interface StockQuote {
    stock: Stock;
    price: number;
    open: number | null;
    high: number | null;
    low: number | null;
    volume: number;
    change: number;
    change_percent: number;
    timestamp: string;
  }
  
  export interface Portfolio {
    holdings: PortfolioHolding[];
    summary: PortfolioSummary;
  }
  
  export interface PortfolioHolding {
    stock_symbol: string;
    stock_name: string;
    quantity: number;
    average_price: number;
    current_price: number;
    market_value: number;
    cost_basis: number;
    unrealized_gain_loss: number;
    unrealized_gain_loss_percent: number;
    last_updated: string;
  }
  
  export interface PortfolioSummary {
    total_value: number;
    total_cost: number;
    total_gain_loss: number;
    total_gain_loss_percent: number;
    holdings_count: number;
  }
  
  export interface Transaction {
    id: number;
    user_id: number;
    stock_id: number;
    stock_symbol: string;
    stock_name: string;
    transaction_type: 'buy' | 'sell';
    quantity: number;
    price: number;
    total_amount: number;
    timestamp: string;
  }
  
  export interface ApiResponse<T = any> {
    success: boolean;
    message: string;
    data?: T;
    errors?: string[];
  }
  
  export interface AuthTokens {
    access_token: string;
    refresh_token: string;
    token_type: string;
    expires_in: number;
  }
  
  export interface LoginResponse {
    user: User;
    tokens: AuthTokens;
  }
  