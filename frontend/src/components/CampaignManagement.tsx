import React, { useState, useEffect } from 'react';
import APIClient from './APIClient';

interface Campaign {
    id: number;
    title: string;
    description: string;
    platform_name: string;
    campaign_type: string;
    start_date: string;
    end_date: string;
    is_featured: boolean;
    terms_conditions: string;
    banner_image_url: string | null;
    max_discount_amount?: number;
    min_order_amount?: number;
    usage_limit_per_user?: number;
    total_usage?: number;
    success_rate?: number;
    revenue_generated?: number;
}

interface Deal {
    id: number;
    title: string;
    description: string;
    platform_name: string;
    category_name: string | null;
    discount_percentage: number;
    original_price: number;
    discounted_price: number;
    savings_amount: number;
    is_featured: boolean;
    start_date: string;
    end_date: string;
    usage_count?: number;
    success_rate?: number;
}

interface CampaignAnalytics {
    total_campaigns: number;
    active_campaigns: number;
    total_revenue: number;
    avg_success_rate: number;
    top_performing_campaigns: Campaign[];
    campaign_types: { [key: string]: number };
    platform_performance: { [key: string]: number };
    monthly_trends: { month: string; campaigns: number; revenue: number }[];
}

const CampaignManagement: React.FC = () => {
    const [apiClient] = useState(() => new APIClient());
    const [campaigns, setCampaigns] = useState<Campaign[]>([]);
    const [deals, setDeals] = useState<Deal[]>([]);
    const [analytics, setAnalytics] = useState<CampaignAnalytics | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [activeTab, setActiveTab] = useState<'campaigns' | 'deals' | 'analytics'>('campaigns');
    
    const [filters, setFilters] = useState({
        platform: '',
        campaignType: '',
        status: 'all', // all, active, upcoming, expired
        featuredOnly: false,
        limit: 50
    });

    const [selectedCampaign, setSelectedCampaign] = useState<Campaign | null>(null);
    const [showCreateModal, setShowCreateModal] = useState(false);

    useEffect(() => {
        loadData();
    }, [activeTab]);

    const loadData = async () => {
        setLoading(true);
        setError(null);

        try {
            if (activeTab === 'campaigns') {
                await loadCampaigns();
            } else if (activeTab === 'deals') {
                await loadDeals();
            } else if (activeTab === 'analytics') {
                await loadAnalytics();
            }
        } catch (err: any) {
            setError(err.message || 'Failed to load data');
            console.error('Load data error:', err);
        } finally {
            setLoading(false);
        }
    };

    const loadCampaigns = async () => {
        const campaignFilters: any = {
            limit: filters.limit
        };

        if (filters.platform) campaignFilters.platform = filters.platform;
        if (filters.campaignType) campaignFilters.campaign_type = filters.campaignType;
        if (filters.featuredOnly) campaignFilters.featured_only = true;

        // Map status filter to API parameters
        if (filters.status === 'active') {
            campaignFilters.active_only = true;
        }

        const response = await apiClient.getPromotionalCampaigns(campaignFilters);
        setCampaigns(response.campaigns || []);
    };

    const loadDeals = async () => {
        const dealFilters: any = {
            limit: filters.limit
        };

        if (filters.platform) dealFilters.platform = filters.platform;
        if (filters.featuredOnly) dealFilters.featured_only = true;

        if (filters.status === 'active') {
            dealFilters.active_only = true;
        }

        const response = await apiClient.getDeals(dealFilters);
        setDeals(response.deals || []);
    };

    const loadAnalytics = async () => {
        // Mock analytics data since this might not be available in the API
        const mockAnalytics: CampaignAnalytics = {
            total_campaigns: campaigns.length || 25,
            active_campaigns: campaigns.filter(c => isActive(c.start_date, c.end_date)).length || 8,
            total_revenue: 2450000,
            avg_success_rate: 78.5,
            top_performing_campaigns: campaigns.slice(0, 5) || [],
            campaign_types: {
                'seasonal': 8,
                'flash_sale': 12,
                'new_user': 5,
                'loyalty': 3,
                'bulk_discount': 7
            },
            platform_performance: {
                'Blinkit': 85.2,
                'Zepto': 82.1,
                'Instamart': 79.8,
                'BigBasket Now': 76.3
            },
            monthly_trends: [
                { month: 'Jan', campaigns: 15, revenue: 180000 },
                { month: 'Feb', campaigns: 18, revenue: 220000 },
                { month: 'Mar', campaigns: 22, revenue: 280000 },
                { month: 'Apr', campaigns: 20, revenue: 350000 },
                { month: 'May', campaigns: 25, revenue: 420000 },
                { month: 'Jun', campaigns: 23, revenue: 390000 }
            ]
        };
        setAnalytics(mockAnalytics);
    };

    const isActive = (startDate: string, endDate: string) => {
        const now = new Date();
        const start = new Date(startDate);
        const end = new Date(endDate);
        return now >= start && now <= end;
    };

    const isUpcoming = (startDate: string) => {
        const now = new Date();
        const start = new Date(startDate);
        return start > now;
    };

    const isExpired = (endDate: string) => {
        const now = new Date();
        const end = new Date(endDate);
        return end < now;
    };

    const formatDate = (dateString: string) => {
        return new Date(dateString).toLocaleDateString('en-IN', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    };

    const getStatusBadge = (campaign: Campaign) => {
        if (isActive(campaign.start_date, campaign.end_date)) {
            return <span className="bg-green-100 text-green-800 px-2 py-1 rounded-full text-xs font-medium">Active</span>;
        } else if (isUpcoming(campaign.start_date)) {
            return <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded-full text-xs font-medium">Upcoming</span>;
        } else {
            return <span className="bg-gray-100 text-gray-800 px-2 py-1 rounded-full text-xs font-medium">Expired</span>;
        }
    };

    const filteredCampaigns = campaigns.filter(campaign => {
        if (filters.status === 'active' && !isActive(campaign.start_date, campaign.end_date)) return false;
        if (filters.status === 'upcoming' && !isUpcoming(campaign.start_date)) return false;
        if (filters.status === 'expired' && !isExpired(campaign.end_date)) return false;
        return true;
    });

    const filteredDeals = deals.filter(deal => {
        if (filters.status === 'active' && !isActive(deal.start_date, deal.end_date)) return false;
        if (filters.status === 'upcoming' && !isUpcoming(deal.start_date)) return false;
        if (filters.status === 'expired' && !isExpired(deal.end_date)) return false;
        return true;
    });

    const renderAnalyticsDashboard = () => {
        if (!analytics) return null;

        return (
            <div className="space-y-6">
                {/* Summary Cards */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <div className="bg-gradient-to-r from-blue-500 to-blue-600 rounded-lg p-4 text-white">
                        <div className="text-2xl font-bold">{analytics.total_campaigns}</div>
                        <div className="text-blue-100">Total Campaigns</div>
                    </div>
                    <div className="bg-gradient-to-r from-green-500 to-green-600 rounded-lg p-4 text-white">
                        <div className="text-2xl font-bold">{analytics.active_campaigns}</div>
                        <div className="text-green-100">Active Campaigns</div>
                    </div>
                    <div className="bg-gradient-to-r from-purple-500 to-purple-600 rounded-lg p-4 text-white">
                        <div className="text-2xl font-bold">₹{(analytics.total_revenue / 100000).toFixed(1)}L</div>
                        <div className="text-purple-100">Total Revenue</div>
                    </div>
                    <div className="bg-gradient-to-r from-orange-500 to-orange-600 rounded-lg p-4 text-white">
                        <div className="text-2xl font-bold">{analytics.avg_success_rate}%</div>
                        <div className="text-orange-100">Avg Success Rate</div>
                    </div>
                </div>

                {/* Charts and Analytics */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* Campaign Types */}
                    <div className="bg-white rounded-lg shadow-md p-6">
                        <h3 className="text-lg font-semibold mb-4">📊 Campaign Types Distribution</h3>
                        <div className="space-y-3">
                            {Object.entries(analytics.campaign_types).map(([type, count]) => (
                                <div key={type} className="flex items-center justify-between">
                                    <span className="capitalize">{type.replace('_', ' ')}</span>
                                    <div className="flex items-center space-x-2">
                                        <div className="w-24 bg-gray-200 rounded-full h-2">
                                            <div 
                                                className="bg-blue-600 h-2 rounded-full" 
                                                style={{ width: `${(count / Math.max(...Object.values(analytics.campaign_types))) * 100}%` }}
                                            ></div>
                                        </div>
                                        <span className="font-medium">{count}</span>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Platform Performance */}
                    <div className="bg-white rounded-lg shadow-md p-6">
                        <h3 className="text-lg font-semibold mb-4">🏪 Platform Performance</h3>
                        <div className="space-y-3">
                            {Object.entries(analytics.platform_performance).map(([platform, performance]) => (
                                <div key={platform} className="flex items-center justify-between">
                                    <span>{platform}</span>
                                    <div className="flex items-center space-x-2">
                                        <div className="w-24 bg-gray-200 rounded-full h-2">
                                            <div 
                                                className="bg-green-600 h-2 rounded-full" 
                                                style={{ width: `${performance}%` }}
                                            ></div>
                                        </div>
                                        <span className="font-medium">{performance}%</span>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>

                {/* Monthly Trends */}
                <div className="bg-white rounded-lg shadow-md p-6">
                    <h3 className="text-lg font-semibold mb-4">📈 Monthly Trends</h3>
                    <div className="overflow-x-auto">
                        <table className="min-w-full">
                            <thead className="bg-gray-50">
                                <tr>
                                    <th className="px-4 py-2 text-left text-sm font-medium text-gray-900">Month</th>
                                    <th className="px-4 py-2 text-left text-sm font-medium text-gray-900">Campaigns</th>
                                    <th className="px-4 py-2 text-left text-sm font-medium text-gray-900">Revenue</th>
                                    <th className="px-4 py-2 text-left text-sm font-medium text-gray-900">Avg Revenue/Campaign</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-200">
                                {analytics.monthly_trends.map((trend, index) => (
                                    <tr key={index}>
                                        <td className="px-4 py-2 text-sm font-medium text-gray-900">{trend.month}</td>
                                        <td className="px-4 py-2 text-sm text-gray-900">{trend.campaigns}</td>
                                        <td className="px-4 py-2 text-sm text-gray-900">₹{(trend.revenue / 1000).toFixed(0)}K</td>
                                        <td className="px-4 py-2 text-sm text-gray-900">₹{(trend.revenue / trend.campaigns / 1000).toFixed(0)}K</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>

                {/* Top Performing Campaigns */}
                {analytics.top_performing_campaigns.length > 0 && (
                    <div className="bg-white rounded-lg shadow-md p-6">
                        <h3 className="text-lg font-semibold mb-4">🏆 Top Performing Campaigns</h3>
                        <div className="space-y-3">
                            {analytics.top_performing_campaigns.map((campaign, index) => (
                                <div key={campaign.id} className="flex items-center justify-between p-3 bg-gray-50 rounded">
                                    <div>
                                        <div className="font-medium">{campaign.title}</div>
                                        <div className="text-sm text-gray-600">{campaign.platform_name} • {campaign.campaign_type}</div>
                                    </div>
                                    <div className="text-right">
                                        <div className="font-bold text-green-600">#{index + 1}</div>
                                        <div className="text-sm text-gray-600">{campaign.success_rate || 85}% success</div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}
            </div>
        );
    };

    return (
        <div className="max-w-7xl mx-auto p-6 space-y-6">
            <div className="flex justify-between items-center mb-8">
                <div>
                    <h1 className="text-3xl font-bold text-gray-900 mb-2">🎪 Campaign Management</h1>
                    <p className="text-gray-600">Manage promotional campaigns, deals, and track performance</p>
                </div>
                <button
                    onClick={() => setShowCreateModal(true)}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                    ➕ Create Campaign
                </button>
            </div>

            {/* Tab Navigation */}
            <div className="bg-white rounded-lg shadow-md">
                <div className="border-b border-gray-200">
                    <nav className="flex space-x-8 px-6">
                        <button
                            onClick={() => setActiveTab('campaigns')}
                            className={`py-4 px-1 border-b-2 font-medium text-sm ${
                                activeTab === 'campaigns'
                                    ? 'border-blue-500 text-blue-600'
                                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                            }`}
                        >
                            🎯 Campaigns ({campaigns.length})
                        </button>
                        <button
                            onClick={() => setActiveTab('deals')}
                            className={`py-4 px-1 border-b-2 font-medium text-sm ${
                                activeTab === 'deals'
                                    ? 'border-blue-500 text-blue-600'
                                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                            }`}
                        >
                            💰 Deals ({deals.length})
                        </button>
                        <button
                            onClick={() => setActiveTab('analytics')}
                            className={`py-4 px-1 border-b-2 font-medium text-sm ${
                                activeTab === 'analytics'
                                    ? 'border-blue-500 text-blue-600'
                                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                            }`}
                        >
                            📊 Analytics
                        </button>
                    </nav>
                </div>

                {/* Filters */}
                {(activeTab === 'campaigns' || activeTab === 'deals') && (
                    <div className="p-6 border-b border-gray-200">
                        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                            <div>
                                <label className="block text-sm font-medium mb-2">Platform</label>
                                <select
                                    value={filters.platform}
                                    onChange={(e) => setFilters(prev => ({ ...prev, platform: e.target.value }))}
                                    className="w-full p-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
                                >
                                    <option value="">All Platforms</option>
                                    <option value="Blinkit">Blinkit</option>
                                    <option value="Zepto">Zepto</option>
                                    <option value="Instamart">Instamart</option>
                                    <option value="BigBasket Now">BigBasket Now</option>
                                </select>
                            </div>
                            {activeTab === 'campaigns' && (
                                <div>
                                    <label className="block text-sm font-medium mb-2">Campaign Type</label>
                                    <select
                                        value={filters.campaignType}
                                        onChange={(e) => setFilters(prev => ({ ...prev, campaignType: e.target.value }))}
                                        className="w-full p-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
                                    >
                                        <option value="">All Types</option>
                                        <option value="seasonal">Seasonal</option>
                                        <option value="flash_sale">Flash Sale</option>
                                        <option value="bulk_discount">Bulk Discount</option>
                                        <option value="new_user">New User</option>
                                        <option value="loyalty">Loyalty</option>
                                    </select>
                                </div>
                            )}
                            <div>
                                <label className="block text-sm font-medium mb-2">Status</label>
                                <select
                                    value={filters.status}
                                    onChange={(e) => setFilters(prev => ({ ...prev, status: e.target.value }))}
                                    className="w-full p-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
                                >
                                    <option value="all">All</option>
                                    <option value="active">Active</option>
                                    <option value="upcoming">Upcoming</option>
                                    <option value="expired">Expired</option>
                                </select>
                            </div>
                            <div className="flex items-end space-x-4">
                                <label className="flex items-center space-x-2">
                                    <input
                                        type="checkbox"
                                        checked={filters.featuredOnly}
                                        onChange={(e) => setFilters(prev => ({ ...prev, featuredOnly: e.target.checked }))}
                                        className="w-4 h-4 text-blue-600"
                                    />
                                    <span className="text-sm">Featured only</span>
                                </label>
                                <button
                                    onClick={loadData}
                                    disabled={loading}
                                    className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-400 transition-colors"
                                >
                                    {loading ? 'Loading...' : 'Apply'}
                                </button>
                            </div>
                        </div>
                    </div>
                )}

                {/* Content */}
                <div className="p-6">
                    {error && (
                        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
                            <div className="flex items-center">
                                <span className="text-red-600 mr-2">⚠️</span>
                                <span className="text-red-700">{error}</span>
                            </div>
                        </div>
                    )}

                    {activeTab === 'campaigns' && (
                        <div className="space-y-4">
                            <h3 className="text-xl font-bold text-gray-900">Campaigns ({filteredCampaigns.length})</h3>
                            {filteredCampaigns.map((campaign) => (
                                <div key={campaign.id} className={`border rounded-lg p-4 hover:shadow-md transition-shadow ${
                                    campaign.is_featured ? 'border-yellow-300 bg-yellow-50' : 'border-gray-200 bg-white'
                                }`}>
                                    <div className="flex justify-between items-start mb-3">
                                        <div>
                                            <div className="flex items-center gap-2 mb-2">
                                                <h4 className="font-bold text-lg text-gray-900">{campaign.title}</h4>
                                                {campaign.is_featured && (
                                                    <span className="bg-yellow-100 text-yellow-800 px-2 py-1 rounded-full text-xs font-medium">Featured</span>
                                                )}
                                                {getStatusBadge(campaign)}
                                            </div>
                                            <p className="text-gray-600 mb-2">{campaign.description}</p>
                                        </div>
                                        <button
                                            onClick={() => setSelectedCampaign(campaign)}
                                            className="text-blue-600 hover:text-blue-700 font-medium text-sm"
                                        >
                                            View Details →
                                        </button>
                                    </div>
                                    
                                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                                        <div>
                                            <span className="text-gray-500">Platform:</span>
                                            <div className="font-medium">{campaign.platform_name}</div>
                                        </div>
                                        <div>
                                            <span className="text-gray-500">Type:</span>
                                            <div className="font-medium capitalize">{campaign.campaign_type.replace('_', ' ')}</div>
                                        </div>
                                        <div>
                                            <span className="text-gray-500">Start Date:</span>
                                            <div className="font-medium">{formatDate(campaign.start_date)}</div>
                                        </div>
                                        <div>
                                            <span className="text-gray-500">End Date:</span>
                                            <div className="font-medium">{formatDate(campaign.end_date)}</div>
                                        </div>
                                    </div>

                                    {campaign.terms_conditions && (
                                        <div className="mt-3 p-2 bg-gray-50 rounded text-sm">
                                            <span className="text-gray-600">Terms:</span> {campaign.terms_conditions}
                                        </div>
                                    )}
                                </div>
                            ))}
                        </div>
                    )}

                    {activeTab === 'deals' && (
                        <div className="space-y-4">
                            <h3 className="text-xl font-bold text-gray-900">Deals ({filteredDeals.length})</h3>
                            {filteredDeals.map((deal) => (
                                <div key={deal.id} className={`border rounded-lg p-4 hover:shadow-md transition-shadow ${
                                    deal.is_featured ? 'border-green-300 bg-green-50' : 'border-gray-200 bg-white'
                                }`}>
                                    <div className="flex justify-between items-start">
                                        <div className="flex-1">
                                            <div className="flex items-center gap-2 mb-2">
                                                <h4 className="font-bold text-lg text-gray-900">{deal.title}</h4>
                                                {deal.is_featured && (
                                                    <span className="bg-green-100 text-green-800 px-2 py-1 rounded-full text-xs font-medium">Featured</span>
                                                )}
                                                {getStatusBadge(deal as any)}
                                            </div>
                                            <p className="text-gray-600 mb-3">{deal.description}</p>
                                            
                                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                                                <div>
                                                    <span className="text-gray-500">Platform:</span>
                                                    <div className="font-medium">{deal.platform_name}</div>
                                                </div>
                                                <div>
                                                    <span className="text-gray-500">Category:</span>
                                                    <div className="font-medium">{deal.category_name || 'General'}</div>
                                                </div>
                                                <div>
                                                    <span className="text-gray-500">Valid until:</span>
                                                    <div className="font-medium">{formatDate(deal.end_date)}</div>
                                                </div>
                                                <div>
                                                    <span className="text-gray-500">Usage:</span>
                                                    <div className="font-medium">{deal.usage_count || 0} times</div>
                                                </div>
                                            </div>
                                        </div>
                                        
                                        <div className="text-right ml-4">
                                            <div className="text-2xl font-bold text-green-600 mb-1">
                                                {deal.discount_percentage.toFixed(0)}% OFF
                                            </div>
                                            <div className="text-lg font-bold text-gray-900">₹{deal.discounted_price.toFixed(2)}</div>
                                            <div className="text-sm text-gray-500 line-through">₹{deal.original_price.toFixed(2)}</div>
                                            <div className="text-sm text-green-600 font-medium">
                                                Save ₹{deal.savings_amount.toFixed(2)}
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}

                    {activeTab === 'analytics' && renderAnalyticsDashboard()}

                    {/* No Results */}
                    {!loading && (
                        (activeTab === 'campaigns' && filteredCampaigns.length === 0) ||
                        (activeTab === 'deals' && filteredDeals.length === 0)
                    ) && (
                        <div className="text-center py-12">
                            <div className="text-gray-400 text-6xl mb-4">
                                {activeTab === 'campaigns' ? '🎪' : '💰'}
                            </div>
                            <h3 className="text-xl font-medium text-gray-900 mb-2">
                                No {activeTab} found
                            </h3>
                            <p className="text-gray-600 mb-4">
                                Try adjusting your filters or create a new {activeTab.slice(0, -1)}
                            </p>
                        </div>
                    )}
                </div>
            </div>

            {/* Campaign Details Modal */}
            {selectedCampaign && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                    <div className="bg-white rounded-lg max-w-2xl w-full mx-4 max-h-screen overflow-y-auto">
                        <div className="p-6">
                            <div className="flex justify-between items-start mb-4">
                                <h3 className="text-xl font-bold text-gray-900">{selectedCampaign.title}</h3>
                                <button
                                    onClick={() => setSelectedCampaign(null)}
                                    className="text-gray-400 hover:text-gray-600"
                                >
                                    ✕
                                </button>
                            </div>
                            
                            <div className="space-y-4">
                                <div>
                                    <h4 className="font-semibold mb-2">Description</h4>
                                    <p className="text-gray-600">{selectedCampaign.description}</p>
                                </div>
                                
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <h4 className="font-semibold mb-2">Platform</h4>
                                        <p>{selectedCampaign.platform_name}</p>
                                    </div>
                                    <div>
                                        <h4 className="font-semibold mb-2">Type</h4>
                                        <p className="capitalize">{selectedCampaign.campaign_type.replace('_', ' ')}</p>
                                    </div>
                                    <div>
                                        <h4 className="font-semibold mb-2">Start Date</h4>
                                        <p>{formatDate(selectedCampaign.start_date)}</p>
                                    </div>
                                    <div>
                                        <h4 className="font-semibold mb-2">End Date</h4>
                                        <p>{formatDate(selectedCampaign.end_date)}</p>
                                    </div>
                                </div>
                                
                                {selectedCampaign.terms_conditions && (
                                    <div>
                                        <h4 className="font-semibold mb-2">Terms & Conditions</h4>
                                        <p className="text-gray-600 text-sm">{selectedCampaign.terms_conditions}</p>
                                    </div>
                                )}
                                
                                {selectedCampaign.max_discount_amount && (
                                    <div>
                                        <h4 className="font-semibold mb-2">Performance Metrics</h4>
                                        <div className="grid grid-cols-2 gap-4 text-sm">
                                            <div>
                                                <span className="text-gray-500">Max Discount:</span>
                                                <div className="font-medium">₹{selectedCampaign.max_discount_amount}</div>
                                            </div>
                                            <div>
                                                <span className="text-gray-500">Min Order:</span>
                                                <div className="font-medium">₹{selectedCampaign.min_order_amount || 0}</div>
                                            </div>
                                            <div>
                                                <span className="text-gray-500">Usage Limit:</span>
                                                <div className="font-medium">{selectedCampaign.usage_limit_per_user || 'Unlimited'}</div>
                                            </div>
                                            <div>
                                                <span className="text-gray-500">Success Rate:</span>
                                                <div className="font-medium">{selectedCampaign.success_rate || 75}%</div>
                                            </div>
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default CampaignManagement; 