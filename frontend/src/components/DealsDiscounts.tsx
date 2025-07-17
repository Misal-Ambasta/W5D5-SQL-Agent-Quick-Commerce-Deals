import React, { useState, useEffect } from 'react';
import APIClient from './APIClient';

interface Deal {
    id: number;
    title: string;
    description: string;
    discount_type: string;
    discount_value: number;
    discount_percentage: number;
    max_discount_amount: number;
    min_order_amount: number;
    discount_code: string | null;
    platform_name: string;
    product_name: string | null;
    category_name: string | null;
    original_price: number;
    discounted_price: number;
    savings_amount: number;
    is_featured: boolean;
    start_date: string;
    end_date: string;
    usage_limit_per_user: number;
}

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
}

interface DealsResponse {
    deals: Deal[];
    total_deals: number;
    filters_applied: any;
    platforms_included: string[];
    categories_included: string[];
    execution_time: number;
}

interface CampaignsResponse {
    campaigns: Campaign[];
    total_campaigns: number;
    execution_time: number;
}

const DealsDiscounts: React.FC = () => {
    const [apiClient] = useState(() => new APIClient());
    const [deals, setDeals] = useState<Deal[]>([]);
    const [campaigns, setCampaigns] = useState<Campaign[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [activeTab, setActiveTab] = useState<'deals' | 'campaigns'>('deals');
    
    const [filters, setFilters] = useState({
        platform: '',
        category: '',
        minDiscount: 0,
        maxDiscount: 100,
        featuredOnly: false,
        activeOnly: true,
        limit: 50
    });

    const [campaignFilters, setCampaignFilters] = useState({
        platform: '',
        campaignType: '',
        featuredOnly: false,
        activeOnly: true,
        limit: 20
    });

    const [platforms, setPlatforms] = useState<string[]>([]);
    const [categories, setCategories] = useState<string[]>([]);

    useEffect(() => {
        loadDeals();
    }, []);

    const loadDeals = async () => {
        setLoading(true);
        setError(null);

        try {
            const response: DealsResponse = await apiClient.getDeals(filters);
            setDeals(response.deals || []);
            setPlatforms(response.platforms_included || []);
            setCategories(response.categories_included || []);
        } catch (err: any) {
            setError(err.message || 'Failed to load deals');
            console.error('Load deals error:', err);
        } finally {
            setLoading(false);
        }
    };

    const loadCampaigns = async () => {
        setLoading(true);
        setError(null);

        try {
            const response: CampaignsResponse = await apiClient.getPromotionalCampaigns(campaignFilters);
            setCampaigns(response.campaigns || []);
        } catch (err: any) {
            setError(err.message || 'Failed to load campaigns');
            console.error('Load campaigns error:', err);
        } finally {
            setLoading(false);
        }
    };

    const handleTabChange = (tab: 'deals' | 'campaigns') => {
        setActiveTab(tab);
        if (tab === 'campaigns' && campaigns.length === 0) {
            loadCampaigns();
        }
    };

    const applyFilters = () => {
        if (activeTab === 'deals') {
            loadDeals();
        } else {
            loadCampaigns();
        }
    };

    const resetFilters = () => {
        if (activeTab === 'deals') {
            setFilters({
                platform: '',
                category: '',
                minDiscount: 0,
                maxDiscount: 100,
                featuredOnly: false,
                activeOnly: true,
                limit: 50
            });
        } else {
            setCampaignFilters({
                platform: '',
                campaignType: '',
                featuredOnly: false,
                activeOnly: true,
                limit: 20
            });
        }
    };

    const calculateSavings = (deals: Deal[]) => {
        return deals.reduce((total, deal) => total + deal.savings_amount, 0);
    };

    const formatDate = (dateString: string) => {
        return new Date(dateString).toLocaleDateString('en-IN', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    };

    const isExpiringSoon = (endDate: string) => {
        const end = new Date(endDate);
        const now = new Date();
        const diffTime = end.getTime() - now.getTime();
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
        return diffDays <= 3 && diffDays > 0;
    };

    const featuredDeals = deals.filter(deal => deal.is_featured);
    const totalSavings = calculateSavings(deals);

    return (
        <div className="max-w-7xl mx-auto p-6 space-y-6">
            <div className="text-center mb-8">
                <h1 className="text-3xl font-bold text-gray-900 mb-2">💰 Deals & Discounts</h1>
                <p className="text-gray-600">Discover the best deals and promotional campaigns across platforms</p>
            </div>

            {/* Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                <div className="bg-gradient-to-r from-blue-500 to-blue-600 rounded-lg p-4 text-white">
                    <div className="text-2xl font-bold">{deals.length}</div>
                    <div className="text-blue-100">Active Deals</div>
                </div>
                <div className="bg-gradient-to-r from-green-500 to-green-600 rounded-lg p-4 text-white">
                    <div className="text-2xl font-bold">{featuredDeals.length}</div>
                    <div className="text-green-100">Featured Deals</div>
                </div>
                <div className="bg-gradient-to-r from-purple-500 to-purple-600 rounded-lg p-4 text-white">
                    <div className="text-2xl font-bold">₹{totalSavings.toFixed(0)}</div>
                    <div className="text-purple-100">Total Savings</div>
                </div>
                <div className="bg-gradient-to-r from-orange-500 to-orange-600 rounded-lg p-4 text-white">
                    <div className="text-2xl font-bold">{platforms.length}</div>
                    <div className="text-orange-100">Platforms</div>
                </div>
            </div>

            {/* Tab Navigation */}
            <div className="bg-white rounded-lg shadow-md">
                <div className="border-b border-gray-200">
                    <nav className="flex space-x-8 px-6">
                        <button
                            onClick={() => handleTabChange('deals')}
                            className={`py-4 px-1 border-b-2 font-medium text-sm ${
                                activeTab === 'deals'
                                    ? 'border-blue-500 text-blue-600'
                                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                            }`}
                        >
                            🎯 Deals & Discounts
                        </button>
                        <button
                            onClick={() => handleTabChange('campaigns')}
                            className={`py-4 px-1 border-b-2 font-medium text-sm ${
                                activeTab === 'campaigns'
                                    ? 'border-blue-500 text-blue-600'
                                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                            }`}
                        >
                            📢 Promotional Campaigns
                        </button>
                    </nav>
                </div>

                {/* Filters Section */}
                <div className="p-6 border-b border-gray-200">
                    {activeTab === 'deals' ? (
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                            <div>
                                <label className="block text-sm font-medium mb-2">Platform</label>
                                <select
                                    value={filters.platform}
                                    onChange={(e) => setFilters(prev => ({ ...prev, platform: e.target.value }))}
                                    className="w-full p-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
                                >
                                    <option value="">All Platforms</option>
                                    {platforms.map(platform => (
                                        <option key={platform} value={platform}>{platform}</option>
                                    ))}
                                </select>
                            </div>
                            <div>
                                <label className="block text-sm font-medium mb-2">Category</label>
                                <select
                                    value={filters.category}
                                    onChange={(e) => setFilters(prev => ({ ...prev, category: e.target.value }))}
                                    className="w-full p-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
                                >
                                    <option value="">All Categories</option>
                                    {categories.map(category => (
                                        <option key={category} value={category}>{category}</option>
                                    ))}
                                </select>
                            </div>
                            <div>
                                <label className="block text-sm font-medium mb-2">Discount Range (%)</label>
                                <div className="flex gap-2">
                                    <input
                                        type="number"
                                        min="0"
                                        max="100"
                                        value={filters.minDiscount}
                                        onChange={(e) => setFilters(prev => ({ ...prev, minDiscount: Number(e.target.value) }))}
                                        placeholder="Min"
                                        className="w-full p-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
                                    />
                                    <input
                                        type="number"
                                        min="0"
                                        max="100"
                                        value={filters.maxDiscount}
                                        onChange={(e) => setFilters(prev => ({ ...prev, maxDiscount: Number(e.target.value) }))}
                                        placeholder="Max"
                                        className="w-full p-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
                                    />
                                </div>
                            </div>
                            <div className="space-y-2">
                                <label className="flex items-center space-x-2">
                                    <input
                                        type="checkbox"
                                        checked={filters.featuredOnly}
                                        onChange={(e) => setFilters(prev => ({ ...prev, featuredOnly: e.target.checked }))}
                                        className="w-4 h-4 text-blue-600"
                                    />
                                    <span className="text-sm">Featured only</span>
                                </label>
                                <label className="flex items-center space-x-2">
                                    <input
                                        type="checkbox"
                                        checked={filters.activeOnly}
                                        onChange={(e) => setFilters(prev => ({ ...prev, activeOnly: e.target.checked }))}
                                        className="w-4 h-4 text-blue-600"
                                    />
                                    <span className="text-sm">Active only</span>
                                </label>
                            </div>
                        </div>
                    ) : (
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                            <div>
                                <label className="block text-sm font-medium mb-2">Platform</label>
                                <select
                                    value={campaignFilters.platform}
                                    onChange={(e) => setCampaignFilters(prev => ({ ...prev, platform: e.target.value }))}
                                    className="w-full p-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
                                >
                                    <option value="">All Platforms</option>
                                    {platforms.map(platform => (
                                        <option key={platform} value={platform}>{platform}</option>
                                    ))}
                                </select>
                            </div>
                            <div>
                                <label className="block text-sm font-medium mb-2">Campaign Type</label>
                                <select
                                    value={campaignFilters.campaignType}
                                    onChange={(e) => setCampaignFilters(prev => ({ ...prev, campaignType: e.target.value }))}
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
                            <div className="space-y-2">
                                <label className="flex items-center space-x-2">
                                    <input
                                        type="checkbox"
                                        checked={campaignFilters.featuredOnly}
                                        onChange={(e) => setCampaignFilters(prev => ({ ...prev, featuredOnly: e.target.checked }))}
                                        className="w-4 h-4 text-blue-600"
                                    />
                                    <span className="text-sm">Featured only</span>
                                </label>
                                <label className="flex items-center space-x-2">
                                    <input
                                        type="checkbox"
                                        checked={campaignFilters.activeOnly}
                                        onChange={(e) => setCampaignFilters(prev => ({ ...prev, activeOnly: e.target.checked }))}
                                        className="w-4 h-4 text-blue-600"
                                    />
                                    <span className="text-sm">Active only</span>
                                </label>
                            </div>
                        </div>
                    )}

                    <div className="flex gap-4 mt-4">
                        <button
                            onClick={applyFilters}
                            disabled={loading}
                            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 transition-colors"
                        >
                            {loading ? 'Loading...' : 'Apply Filters'}
                        </button>
                        <button
                            onClick={resetFilters}
                            className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
                        >
                            Reset
                        </button>
                    </div>
                </div>

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

                    {activeTab === 'deals' ? (
                        <div className="space-y-6">
                            {/* Featured Deals */}
                            {featuredDeals.length > 0 && (
                                <div>
                                    <h3 className="text-xl font-bold text-gray-900 mb-4">⭐ Featured Deals</h3>
                                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
                                        {featuredDeals.slice(0, 3).map((deal) => (
                                            <div key={deal.id} className="bg-gradient-to-br from-yellow-50 to-orange-50 border-2 border-yellow-200 rounded-lg p-6 relative">
                                                <div className="absolute top-2 right-2">
                                                    <span className="bg-yellow-400 text-yellow-900 px-2 py-1 rounded-full text-xs font-bold">FEATURED</span>
                                                </div>
                                                <div className="space-y-3">
                                                    <h4 className="font-bold text-lg text-gray-900">{deal.title}</h4>
                                                    <p className="text-gray-600 text-sm">{deal.description}</p>
                                                    <div className="flex justify-between items-center">
                                                        <div>
                                                            <span className="text-2xl font-bold text-green-600">{deal.discount_percentage != null ? `${deal.discount_percentage.toFixed(0)}% OFF` : '-'}</span>
                                                            <div className="text-sm text-gray-600">{deal.platform_name}</div>
                                                        </div>
                                                        <div className="text-right">
                                                            <div className="text-lg font-bold text-gray-900">{deal.discounted_price != null ? `₹${deal.discounted_price.toFixed(2)}` : '-'}</div>
                                                            <div className="text-sm text-gray-500 line-through">{deal.original_price != null ? `₹${deal.original_price.toFixed(2)}` : '-'}</div>
                                                        </div>
                                                    </div>
                                                    {deal.discount_code && (
                                                        <div className="bg-white border border-gray-300 rounded p-2">
                                                            <div className="text-xs text-gray-600">Use code:</div>
                                                            <div className="font-mono font-bold text-blue-600">{deal.discount_code}</div>
                                                        </div>
                                                    )}
                                                    <div className="text-xs text-gray-500">
                                                        Expires: {formatDate(deal.end_date)}
                                                        {isExpiringSoon(deal.end_date) && <span className="text-red-600 ml-2">⏰ Expires Soon!</span>}
                                                    </div>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {/* All Deals */}
                            <div>
                                <h3 className="text-xl font-bold text-gray-900 mb-4">All Deals ({deals.length})</h3>
                                <div className="grid gap-4">
                                    {deals.map((deal) => (
                                        <div key={deal.id} className={`bg-white border rounded-lg p-4 hover:shadow-md transition-shadow ${
                                            deal.is_featured ? 'border-yellow-300' : 'border-gray-200'
                                        }`}>
                                            <div className="flex justify-between items-start">
                                                <div className="flex-1">
                                                    <div className="flex items-center gap-2 mb-2">
                                                        <h4 className="font-bold text-lg text-gray-900">{deal.title}</h4>
                                                        {deal.is_featured && (
                                                            <span className="bg-yellow-100 text-yellow-800 px-2 py-1 rounded-full text-xs font-medium">Featured</span>
                                                        )}
                                                        {isExpiringSoon(deal.end_date) && (
                                                            <span className="bg-red-100 text-red-800 px-2 py-1 rounded-full text-xs font-medium">⏰ Expires Soon</span>
                                                        )}
                                                    </div>
                                                    <p className="text-gray-600 mb-3">{deal.description}</p>
                                                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                                                        <div>
                                                            <span className="text-gray-500">Platform:</span>
                                                            <div className="font-medium">{deal.platform_name}</div>
                                                        </div>
                                                        {deal.category_name && (
                                                            <div>
                                                                <span className="text-gray-500">Category:</span>
                                                                <div className="font-medium">{deal.category_name}</div>
                                                            </div>
                                                        )}
                                                        <div>
                                                            <span className="text-gray-500">Valid until:</span>
                                                            <div className="font-medium">{formatDate(deal.end_date)}</div>
                                                        </div>
                                                        {deal.min_order_amount > 0 && (
                                                            <div>
                                                                <span className="text-gray-500">Min order:</span>
                                                                <div className="font-medium">₹{deal.min_order_amount}</div>
                                                            </div>
                                                        )}
                                                    </div>
                                                    {deal.discount_code && (
                                                        <div className="mt-3 bg-gray-50 border border-gray-200 rounded p-2 inline-block">
                                                            <span className="text-xs text-gray-600 mr-2">Code:</span>
                                                            <span className="font-mono font-bold text-blue-600">{deal.discount_code}</span>
                                                        </div>
                                                    )}
                                                </div>
                                                <div className="text-right ml-4">
                                                    <div className="text-2xl font-bold text-green-600 mb-1">
                                                        {deal.discount_percentage != null ? `${deal.discount_percentage.toFixed(0)}% OFF` : '-'}
                                                    </div>
                                                    <div className="text-lg font-bold text-gray-900">{deal.discounted_price != null ? `₹${deal.discounted_price.toFixed(2)}` : '-'}</div>
                                                    <div className="text-sm text-gray-500 line-through">{deal.original_price != null ? `₹${deal.original_price.toFixed(2)}` : '-'}</div>
                                                    <div className="text-sm text-green-600 font-medium">
                                                        Save {deal.savings_amount != null ? `₹${deal.savings_amount.toFixed(2)}` : '-'}
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>
                    ) : (
                        <div className="space-y-6">
                            <h3 className="text-xl font-bold text-gray-900">Promotional Campaigns ({campaigns.length})</h3>
                            <div className="grid gap-6">
                                {campaigns.map((campaign) => (
                                    <div key={campaign.id} className={`bg-white border rounded-lg overflow-hidden hover:shadow-md transition-shadow ${
                                        campaign.is_featured ? 'border-purple-300' : 'border-gray-200'
                                    }`}>
                                        <div className="p-6">
                                            <div className="flex justify-between items-start mb-4">
                                                <div>
                                                    <div className="flex items-center gap-2 mb-2">
                                                        <h4 className="font-bold text-xl text-gray-900">{campaign.title}</h4>
                                                        {campaign.is_featured && (
                                                            <span className="bg-purple-100 text-purple-800 px-2 py-1 rounded-full text-xs font-medium">Featured</span>
                                                        )}
                                                    </div>
                                                    <p className="text-gray-600 mb-3">{campaign.description}</p>
                                                </div>
                                                <div className="text-right">
                                                    <div className="font-bold text-lg text-gray-900">{campaign.platform_name}</div>
                                                    <div className="text-sm text-gray-500">{campaign.campaign_type}</div>
                                                </div>
                                            </div>
                                            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                                                <div>
                                                    <span className="text-gray-500">Start Date:</span>
                                                    <div className="font-medium">{formatDate(campaign.start_date)}</div>
                                                </div>
                                                <div>
                                                    <span className="text-gray-500">End Date:</span>
                                                    <div className="font-medium">{formatDate(campaign.end_date)}</div>
                                                </div>
                                                <div>
                                                    <span className="text-gray-500">Type:</span>
                                                    <div className="font-medium capitalize">{campaign.campaign_type.replace('_', ' ')}</div>
                                                </div>
                                            </div>
                                            {campaign.terms_conditions && (
                                                <div className="mt-4 p-3 bg-gray-50 rounded">
                                                    <div className="text-xs text-gray-600 mb-1">Terms & Conditions:</div>
                                                    <div className="text-sm text-gray-700">{campaign.terms_conditions}</div>
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* No Results */}
                    {!loading && ((activeTab === 'deals' && deals.length === 0) || (activeTab === 'campaigns' && campaigns.length === 0)) && (
                        <div className="text-center py-12">
                            <div className="text-gray-400 text-6xl mb-4">
                                {activeTab === 'deals' ? '🎯' : '📢'}
                            </div>
                            <h3 className="text-xl font-medium text-gray-900 mb-2">
                                No {activeTab === 'deals' ? 'deals' : 'campaigns'} found
                            </h3>
                            <p className="text-gray-600 mb-4">
                                Try adjusting your filters or check back later
                            </p>
                            <button
                                onClick={resetFilters}
                                className="text-blue-600 hover:text-blue-700 font-medium"
                            >
                                Reset filters
                            </button>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default DealsDiscounts; 