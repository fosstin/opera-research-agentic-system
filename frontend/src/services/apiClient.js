/**
 * API Client for Opera Research Platform
 *
 * Provides a centralized interface for all backend API calls.
 * Uses fetch API with proper error handling and request/response interceptors.
 */

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

class ApiClient {
  constructor(baseURL) {
    this.baseURL = baseURL;
    this.defaultHeaders = {
      'Content-Type': 'application/json',
    };
  }

  /**
   * Generic request method
   */
  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;

    const config = {
      ...options,
      headers: {
        ...this.defaultHeaders,
        ...options.headers,
      },
    };

    try {
      const response = await fetch(url, config);

      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || `HTTP ${response.status}: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`API Error [${endpoint}]:`, error.message);
      throw error;
    }
  }

  /**
   * GET request
   */
  async get(endpoint, params = {}) {
    const queryString = new URLSearchParams(params).toString();
    const url = queryString ? `${endpoint}?${queryString}` : endpoint;

    return this.request(url, {
      method: 'GET',
    });
  }

  /**
   * POST request
   */
  async post(endpoint, data) {
    return this.request(endpoint, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  /**
   * PUT request
   */
  async put(endpoint, data) {
    return this.request(endpoint, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  /**
   * DELETE request
   */
  async delete(endpoint) {
    return this.request(endpoint, {
      method: 'DELETE',
    });
  }

  // === COMPANIES ===

  /**
   * Get list of opera companies
   * @param {Object} filters - Query parameters (country, tier, limit, offset)
   */
  async getCompanies(filters = {}) {
    return this.get('/companies', filters);
  }

  /**
   * Get single company by ID
   * @param {string} companyId - Company UUID
   */
  async getCompany(companyId) {
    return this.get(`/companies/${companyId}`);
  }

  // === PRODUCTIONS ===

  /**
   * Get list of productions
   * @param {Object} filters - Query parameters (company_id, composer, season, limit, offset)
   */
  async getProductions(filters = {}) {
    return this.get('/productions', filters);
  }

  /**
   * Get single production by ID
   * @param {string} productionId - Production UUID
   */
  async getProduction(productionId) {
    return this.get(`/productions/${productionId}`);
  }

  // === ARTISTS ===

  /**
   * Get list of artists/performers
   * @param {Object} filters - Query parameters (voice_type, nationality, active_only, limit, offset)
   */
  async getArtists(filters = {}) {
    return this.get('/artists', filters);
  }

  /**
   * Get single artist by ID
   * @param {string} artistId - Artist UUID
   */
  async getArtist(artistId) {
    return this.get(`/artists/${artistId}`);
  }

  // === METADATA ===

  /**
   * Get scraping metadata and statistics
   */
  async getScrapingStats() {
    return this.get('/metadata/scraping-stats');
  }

  // === SEARCH (Future) ===

  /**
   * Semantic search (not yet implemented)
   * @param {string} query - Search query
   * @param {number} limit - Maximum results
   */
  async semanticSearch(query, limit = 10) {
    return this.get('/search/semantic', { query, limit });
  }

  // === LLM AGENT (Future) ===

  /**
   * Query LLM agent (not yet implemented)
   * @param {string} query - Natural language query
   */
  async queryAgent(query) {
    return this.post('/agent/query', { query });
  }
}

// Create and export singleton instance
export const apiClient = new ApiClient(API_BASE_URL);

// Export class for testing
export { ApiClient };

// Example usage:
// import { apiClient } from './services/apiClient';
//
// // Get all companies
// const companies = await apiClient.getCompanies();
//
// // Search productions
// const verdProductions = await apiClient.getProductions({
//   composer: 'Verdi',
//   limit: 20
// });
//
// // Get specific company
// const metOpera = await apiClient.getCompany('company-uuid-here');
