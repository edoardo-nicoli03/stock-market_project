import { User, Stock, StockQuote, ApiResponse, LoginResponse, Portfolio, Transaction } from "../types";

const API_BASE_URL = 'http://localhost:5500/api';

class ApiService {
  private getAuthHeader(): HeadersInit {
    const token = localStorage.getItem('access_token');
    return token ? { Authorization: `Bearer ${token}` } : {};
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    const url = `${API_BASE_URL}${endpoint}`;
    const config: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...this.getAuthHeader(),
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(url, config);
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.message || 'Request failed');
      }
      
      return data;
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }

  // Authentication
  async login(email: string, password: string): Promise<ApiResponse<LoginResponse>> {
    return this.request<LoginResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
  }

  async register(userData: {
    email: string;
    password: string;
    first_name: string;
    last_name: string;
  }): Promise<ApiResponse<LoginResponse>> {
    return this.request<LoginResponse>('/auth/register', {
      method: 'POST',
      body: JSON.stringify(userData),
    });
  }

  async getProfile(): Promise<ApiResponse<{ user: User }>> {
    return this.request<{ user: User }>('/auth/profile');
  }

  // Stocks
  async getStocks(page = 1, search?: string): Promise<ApiResponse<{ items: Stock[]; pagination: any }>> {
    const params = new URLSearchParams({ page: page.toString() });
    if (search) params.append('search', search);
    
    return this.request<{ items: Stock[]; pagination: any }>(`/stocks?${params}`);
  }

  async getStockQuote(symbol: string): Promise<ApiResponse<{ quote: StockQuote }>> {
    return this.request<{ quote: StockQuote }>(`/stocks/${symbol}/quote`);
  }

  async getStockHistory(symbol: string, days = 30): Promise<ApiResponse<any>> {
    return this.request(`/stocks/${symbol}/history?days=${days}`);
  }

  // Portfolio
  async getPortfolio(): Promise<ApiResponse<{ portfolio: Portfolio }>> {
    return this.request<{ portfolio: Portfolio }>('/portfolio');
  }

  async buyStock(symbol: string, quantity: number): Promise<ApiResponse<any>> {
    return this.request('/portfolio/buy', {
      method: 'POST',
      body: JSON.stringify({ symbol, quantity }),
    });
  }

  async sellStock(symbol: string, quantity: number): Promise<ApiResponse<any>> {
    return this.request('/portfolio/sell', {
      method: 'POST',
      body: JSON.stringify({ symbol, quantity }),
    });
  }

  async getTransactions(page = 1): Promise<ApiResponse<{ items: Transaction[]; pagination: any }>> {
    return this.request<{ items: Transaction[]; pagination: any }>(`/portfolio/transactions?page=${page}`);
  }
}

export const apiService = new ApiService();