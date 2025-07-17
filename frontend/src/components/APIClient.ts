import axios from 'axios';
// import type { AxiosResponse } from 'axios';

export interface QueryResult {
    results?: any[];
    error?: string;
    query?: string;
    execution_time?: number;
    total_results?: number;
    cached?: boolean;
    relevant_tables?: string[];
    query_complexity?: string;
    suggestions?: string[];
}

export interface HealthStatus {
    status: string;
    database: string;
    message?: string;
}

export interface ProductComparisonParams {
    product_name: string;
    platforms?: string;
    category?: string;
    brand?: string;
}



export interface AdvancedQueryParams {
    query: string;
    page?: number;
    page_size?: number;
    sampling_method?: string;
    sample_size?: number;
    result_format?: string;
    user_id?: string;
    context?: any;
}

class APIClient {
    private baseUrl: string;
    private apiUrl: string;
    private timeout: number;

    constructor(baseUrl: string = 'http://localhost:8000') {
        this.baseUrl = baseUrl;
        this.apiUrl = `${baseUrl}/api/v1`;
        this.timeout = 30000;
        
        // Configure axios defaults
        axios.defaults.headers.common['Content-Type'] = 'application/json';
        axios.defaults.headers.common['Accept'] = 'application/json';
    }

    async healthCheck(): Promise<HealthStatus> {
        try {
            const response = await axios.get(`${this.baseUrl}/health`, { timeout: 5000 });
            return response.data;
        } catch (error: any) {
            console.error('Health check failed:', error);
            return { status: 'error', database: 'disconnected', message: error.message };
        }
    }

    async processNaturalLanguageQuery(query: string, userId?: string, context?: any): Promise<QueryResult> {
        try {
            const payload: any = { query };
            if (userId) payload.user_id = userId;
            if (context) payload.context = context;

            const response = await axios.post(
                `${this.apiUrl}/query/`,
                payload,
                { timeout: this.timeout }
            );
            return response.data;
        } catch (error: any) {
            console.error('Natural language query failed:', error);
            throw error;
        }
    }

    async processAdvancedQuery(params: AdvancedQueryParams): Promise<QueryResult> {
        try {
            const payload: any = { query: params.query };
            if (params.user_id) payload.user_id = params.user_id;
            if (params.context) payload.context = params.context;

            const queryParams = {
                page: params.page || 1,
                page_size: params.page_size || 20,
                sampling_method: params.sampling_method || 'none',
                sample_size: params.sample_size || 1000,
                result_format: params.result_format || 'structured'
            };

            const response = await axios.post(
                `${this.apiUrl}/query/advanced`,
                payload,
                { params: queryParams, timeout: this.timeout }
            );
            return response.data;
        } catch (error: any) {
            console.error('Advanced query failed:', error);
            throw error;
        }
    }

    async compareProducts(params: ProductComparisonParams): Promise<any> {
        try {
            const queryParams: any = { product_name: params.product_name };
            if (params.platforms) queryParams.platforms = params.platforms;
            if (params.category) queryParams.category = params.category;
            if (params.brand) queryParams.brand = params.brand;

            const response = await axios.get(
                `${this.apiUrl}/products/compare`,
                { params: queryParams, timeout: this.timeout }
            );
            return response.data;
        } catch (error: any) {
            console.error('Product comparison failed:', error);
            throw error;
        }
    }

    async getDeals(params: {
        platform?: string;
        category?: string;
        min_discount?: number;
        max_discount?: number;
        featured_only?: boolean;
        active_only?: boolean;
        limit?: number;
    } = {}): Promise<any> {
        try {
            const queryParams: any = {};
            if (params.platform) queryParams.platform = params.platform;
            if (params.category) queryParams.category = params.category;
            if (params.min_discount !== undefined) queryParams.min_discount = params.min_discount;
            if (params.max_discount !== undefined) queryParams.max_discount = params.max_discount;
            if (params.featured_only !== undefined) queryParams.featured_only = params.featured_only;
            if (params.active_only !== undefined) queryParams.active_only = params.active_only;
            if (params.limit !== undefined) queryParams.limit = params.limit;

            const response = await axios.get(
                `${this.apiUrl}/deals/`,
                { params: queryParams, timeout: this.timeout }
            );
            return response.data;
        } catch (error: any) {
            console.error('Get deals failed:', error);
            throw error;
        }
    }

    async getDealsPost(params: {
        platform?: string;
        category?: string;
        min_discount?: number;
        max_discount?: number;
        featured_only?: boolean;
        active_only?: boolean;
        limit?: number;
    }): Promise<any> {
        try {
            const response = await axios.post(
                `${this.apiUrl}/deals/`,
                params,
                { timeout: this.timeout }
            );
            return response.data;
        } catch (error: any) {
            console.error('Get deals (POST) failed:', error);
            throw error;
        }
    }

    // Enhanced monitoring endpoints
    async getSystemHealth(): Promise<any> {
        try {
            const response = await axios.get(
                `${this.apiUrl}/monitoring/health`,
                { timeout: this.timeout }
            );
            return response.data;
        } catch (error: any) {
            console.error('Get system health failed:', error);
            throw error;
        }
    }

    async getDatabasePerformance(): Promise<any> {
        try {
            const response = await axios.get(
                `${this.apiUrl}/monitoring/database/performance`,
                { timeout: this.timeout }
            );
            return response.data;
        } catch (error: any) {
            console.error('Get database performance failed:', error);
            throw error;
        }
    }

    async getCacheStats(): Promise<any> {
        try {
            const response = await axios.get(
                `${this.apiUrl}/monitoring/cache/stats`,
                { timeout: this.timeout }
            );
            return response.data;
        } catch (error: any) {
            console.error('Get cache stats failed:', error);
            throw error;
        }
    }

    async getMetricsSummary(): Promise<any> {
        try {
            const response = await axios.get(
                `${this.apiUrl}/monitoring/metrics/summary`,
                { timeout: this.timeout }
            );
            return response.data;
        } catch (error: any) {
            console.error('Get metrics summary failed:', error);
            throw error;
        }
    }

    async getRealtimeMetrics(): Promise<any> {
        try {
            const response = await axios.get(
                `${this.apiUrl}/monitoring/metrics/realtime`,
                { timeout: this.timeout }
            );
            return response.data;
        } catch (error: any) {
            console.error('Get realtime metrics failed:', error);
            throw error;
        }
    }

    async getPromotionalCampaigns(params: {
        platform?: string;
        campaign_type?: string;
        featured_only?: boolean;
        active_only?: boolean;
        limit?: number;
    } = {}): Promise<any> {
        try {
            const queryParams: any = {};
            if (params.platform) queryParams.platform = params.platform;
            if (params.campaign_type) queryParams.campaign_type = params.campaign_type;
            if (params.featured_only !== undefined) queryParams.featured_only = params.featured_only;
            if (params.active_only !== undefined) queryParams.active_only = params.active_only;
            if (params.limit !== undefined) queryParams.limit = params.limit;

            const response = await axios.get(
                `${this.apiUrl}/deals/campaigns`,
                { params: queryParams, timeout: this.timeout }
            );
            return response.data;
        } catch (error: any) {
            console.error('Get promotional campaigns failed:', error);
            throw error;
        }
    }

    async compareProductsPost(params: ProductComparisonParams): Promise<any> {
        try {
            const response = await axios.post(
                `${this.apiUrl}/products/compare`,
                params,
                { timeout: this.timeout }
            );
            return response.data;
        } catch (error: any) {
            console.error('Product comparison (POST) failed:', error);
            throw error;
        }
    }

    async getBestDeals(limit: number = 10): Promise<any> {
        try {
            const response = await axios.get(
                `${this.apiUrl}/deals/best`,
                { params: { limit }, timeout: this.timeout }
            );
            return response.data;
        } catch (error: any) {
            console.error('Get best deals failed:', error);
            throw error;
        }
    }
}

export default APIClient; 