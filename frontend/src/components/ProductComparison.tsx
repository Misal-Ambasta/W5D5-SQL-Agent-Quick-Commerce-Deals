import React, { useState, useEffect } from 'react';
import APIClient from './APIClient';

interface Platform {
    platform_id: number;
    platform_name: string;
    current_price: number;
    original_price: number;
    discount_percentage: number;
    is_available: boolean;
    stock_status: string;
    delivery_time_minutes: number;
    last_updated: string;
}

interface Product {
    id: number;
    name: string;
    brand: string;
    category: string;
    description: string;
    pack_size: string;
    is_organic: boolean;
}

interface Comparison {
    product: Product;
    platforms: Platform[];
    best_deal: {
        platform_name: string;
        current_price: number;
        savings: number;
    };
    savings_potential: number;
    price_range: {
        min: number;
        max: number;
    };
}

interface ComparisonResponse {
    query: string;
    comparisons: Comparison[];
    total_products: number;
    platforms_compared: string[];
    execution_time: number;
}

const ProductComparison: React.FC = () => {
    const [apiClient] = useState(() => new APIClient());
    const [searchQuery, setSearchQuery] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [comparisons, setComparisons] = useState<Comparison[]>([]);
    const [filters, setFilters] = useState({
        platforms: [] as string[],
        category: '',
        brand: '',
        minPrice: 0,
        maxPrice: 1000,
        availableOnly: false
    });
    const [allPlatforms, setAllPlatforms] = useState<string[]>([]);
    const [selectedComparison, setSelectedComparison] = useState<Comparison | null>(null);

    const handleSearch = async () => {
        if (!searchQuery.trim()) return;

        setLoading(true);
        setError(null);

        try {
            const params: any = {
                product_name: searchQuery
            };

            if (filters.platforms.length > 0) {
                params.platforms = filters.platforms.join(',');
            }
            if (filters.category) {
                params.category = filters.category;
            }
            if (filters.brand) {
                params.brand = filters.brand;
            }

            const response: ComparisonResponse = await apiClient.compareProducts(params);
            
            // Apply client-side filters
            let filteredComparisons = response.comparisons || [];
            
            if (filters.availableOnly) {
                filteredComparisons = filteredComparisons.map(comp => ({
                    ...comp,
                    platforms: comp.platforms.filter(p => p.is_available)
                })).filter(comp => comp.platforms.length > 0);
            }

            if (filters.minPrice > 0 || filters.maxPrice < 1000) {
                filteredComparisons = filteredComparisons.map(comp => ({
                    ...comp,
                    platforms: comp.platforms.filter(p => 
                        p.current_price >= filters.minPrice && p.current_price <= filters.maxPrice
                    )
                })).filter(comp => comp.platforms.length > 0);
            }

            setComparisons(filteredComparisons);
            
            // Extract all platforms for filter dropdown
            const platforms = new Set<string>();
            response.comparisons.forEach(comp => {
                comp.platforms.forEach(p => platforms.add(p.platform_name));
            });
            setAllPlatforms(Array.from(platforms));

        } catch (err: any) {
            setError(err.message || 'Search failed');
            console.error('Search error:', err);
        } finally {
            setLoading(false);
        }
    };

    const handleKeyPress = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter') {
            handleSearch();
        }
    };

    const togglePlatformFilter = (platform: string) => {
        setFilters(prev => ({
            ...prev,
            platforms: prev.platforms.includes(platform)
                ? prev.platforms.filter(p => p !== platform)
                : [...prev.platforms, platform]
        }));
    };

    const clearFilters = () => {
        setFilters({
            platforms: [],
            category: '',
            brand: '',
            minPrice: 0,
            maxPrice: 1000,
            availableOnly: false
        });
    };

    return (
        <div className="max-w-7xl mx-auto p-6 space-y-6">
            <div className="text-center mb-8">
                <h1 className="text-3xl font-bold text-gray-900 mb-2">🔍 Product Comparison</h1>
                <p className="text-gray-600">Compare prices across multiple platforms to find the best deals</p>
            </div>

            {/* Search Section */}
            <div className="bg-white p-6 rounded-lg shadow-md">
                <div className="flex gap-4 mb-4">
                    <div className="flex-1">
                        <input
                            type="text"
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            onKeyPress={handleKeyPress}
                            placeholder="Enter product name (e.g., onions, milk, bread)..."
                            className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        />
                    </div>
                    <button
                        onClick={handleSearch}
                        disabled={loading || !searchQuery.trim()}
                        className="px-6 py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
                    >
                        {loading ? 'Searching...' : 'Compare Prices'}
                    </button>
                </div>

                {/* Advanced Filters */}
                <div className="border-t pt-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                        <div>
                            <label className="block text-sm font-medium mb-2">Category</label>
                            <input
                                type="text"
                                value={filters.category}
                                onChange={(e) => setFilters(prev => ({ ...prev, category: e.target.value }))}
                                placeholder="e.g., Vegetables, Dairy"
                                className="w-full p-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium mb-2">Brand</label>
                            <input
                                type="text"
                                value={filters.brand}
                                onChange={(e) => setFilters(prev => ({ ...prev, brand: e.target.value }))}
                                placeholder="e.g., Amul, Tata"
                                className="w-full p-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium mb-2">Price Range (₹)</label>
                            <div className="flex gap-2">
                                <input
                                    type="number"
                                    value={filters.minPrice}
                                    onChange={(e) => setFilters(prev => ({ ...prev, minPrice: Number(e.target.value) }))}
                                    placeholder="Min"
                                    className="w-full p-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
                                />
                                <input
                                    type="number"
                                    value={filters.maxPrice}
                                    onChange={(e) => setFilters(prev => ({ ...prev, maxPrice: Number(e.target.value) }))}
                                    placeholder="Max"
                                    className="w-full p-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
                                />
                            </div>
                        </div>
                        <div className="flex items-end">
                            <label className="flex items-center space-x-2">
                                <input
                                    type="checkbox"
                                    checked={filters.availableOnly}
                                    onChange={(e) => setFilters(prev => ({ ...prev, availableOnly: e.target.checked }))}
                                    className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                                />
                                <span className="text-sm">Available only</span>
                            </label>
                        </div>
                    </div>

                    {/* Platform Filters */}
                    {allPlatforms.length > 0 && (
                        <div className="mt-4">
                            <label className="block text-sm font-medium mb-2">Filter by Platforms:</label>
                            <div className="flex flex-wrap gap-2">
                                {allPlatforms.map(platform => (
                                    <button
                                        key={platform}
                                        onClick={() => togglePlatformFilter(platform)}
                                        className={`px-3 py-1 rounded-full text-sm transition-colors ${
                                            filters.platforms.includes(platform)
                                                ? 'bg-blue-600 text-white'
                                                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                                        }`}
                                    >
                                        {platform}
                                    </button>
                                ))}
                                <button
                                    onClick={clearFilters}
                                    className="px-3 py-1 rounded-full text-sm bg-red-100 text-red-700 hover:bg-red-200 transition-colors"
                                >
                                    Clear All
                                </button>
                            </div>
                        </div>
                    )}
                </div>
            </div>

            {/* Error Display */}
            {error && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                    <div className="flex items-center">
                        <span className="text-red-600 mr-2">⚠️</span>
                        <span className="text-red-700">{error}</span>
                    </div>
                </div>
            )}

            {/* Results */}
            {comparisons.length > 0 && (
                <div className="space-y-6">
                    <div className="flex justify-between items-center">
                        <h2 className="text-2xl font-bold text-gray-900">
                            Comparison Results ({comparisons.length} products)
                        </h2>
                    </div>

                    {/* Product Comparison Cards */}
                    <div className="grid gap-6">
                        {comparisons.map((comparison, index) => (
                            <div key={index} className="bg-white rounded-lg shadow-md overflow-hidden">
                                <div className="p-6 border-b border-gray-200">
                                    <div className="flex justify-between items-start mb-4">
                                        <div>
                                            <h3 className="text-xl font-bold text-gray-900">{comparison.product.name}</h3>
                                            <div className="text-sm text-gray-600 space-x-4">
                                                <span>Brand: {comparison.product.brand}</span>
                                                <span>Category: {comparison.product.category}</span>
                                                <span>Size: {comparison.product.pack_size}</span>
                                                {comparison.product.is_organic && (
                                                    <span className="bg-green-100 text-green-800 px-2 py-1 rounded-full text-xs">Organic</span>
                                                )}
                                            </div>
                                        </div>
                                        <div className="text-right">
                                            <div className="text-sm text-gray-600">Price Range</div>
                                            <div className="text-lg font-bold">
                                                ₹{comparison.price_range.min.toFixed(2)} - ₹{comparison.price_range.max.toFixed(2)}
                                            </div>
                                            {comparison.savings_potential > 0 && (
                                                <div className="text-green-600 text-sm">
                                                    Save up to ₹{comparison.savings_potential.toFixed(2)}
                                                </div>
                                            )}
                                        </div>
                                    </div>

                                    {/* Best Deal Highlight */}
                                    {comparison.best_deal && (
                                        <div className="bg-green-50 border border-green-200 rounded-lg p-3 mb-4">
                                            <div className="flex items-center justify-between">
                                                <div className="flex items-center">
                                                    <span className="text-green-600 mr-2">🏆</span>
                                                    <span className="font-medium text-green-900">Best Deal</span>
                                                </div>
                                                <div className="text-right">
                                                    <div className="font-bold text-green-900">
                                                        {comparison.best_deal.platform_name} - ₹{comparison.best_deal.current_price.toFixed(2)}
                                                    </div>
                                                    <div className="text-green-700 text-sm">
                                                        Save ₹{comparison.best_deal.savings.toFixed(2)}
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    )}
                                </div>

                                {/* Platform Comparison Table */}
                                <div className="overflow-x-auto">
                                    <table className="w-full">
                                        <thead className="bg-gray-50">
                                            <tr>
                                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Platform</th>
                                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Current Price</th>
                                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Original Price</th>
                                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Discount</th>
                                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Availability</th>
                                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Delivery</th>
                                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Updated</th>
                                            </tr>
                                        </thead>
                                        <tbody className="bg-white divide-y divide-gray-200">
                                            {comparison.platforms.map((platform, platformIndex) => {
                                                const isBestDeal = platform.platform_name === comparison.best_deal?.platform_name;
                                                return (
                                                    <tr key={platformIndex} className={isBestDeal ? 'bg-green-50' : ''}>
                                                        <td className="px-6 py-4 whitespace-nowrap">
                                                            <div className="flex items-center">
                                                                {isBestDeal && <span className="mr-2">🏆</span>}
                                                                <span className="font-medium text-gray-900">{platform.platform_name}</span>
                                                            </div>
                                                        </td>
                                                        <td className="px-6 py-4 whitespace-nowrap">
                                                            <span className="text-lg font-bold text-gray-900">₹{platform.current_price.toFixed(2)}</span>
                                                        </td>
                                                        <td className="px-6 py-4 whitespace-nowrap">
                                                            {platform.original_price > platform.current_price ? (
                                                                <span className="text-gray-500 line-through">₹{platform.original_price.toFixed(2)}</span>
                                                            ) : (
                                                                <span className="text-gray-500">₹{platform.original_price.toFixed(2)}</span>
                                                            )}
                                                        </td>
                                                        <td className="px-6 py-4 whitespace-nowrap">
                                                            {platform.discount_percentage > 0 ? (
                                                                <span className="bg-red-100 text-red-800 px-2 py-1 rounded-full text-xs font-medium">
                                                                    {platform.discount_percentage.toFixed(1)}% OFF
                                                                </span>
                                                            ) : (
                                                                <span className="text-gray-400">-</span>
                                                            )}
                                                        </td>
                                                        <td className="px-6 py-4 whitespace-nowrap">
                                                            <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                                                                platform.is_available 
                                                                    ? 'bg-green-100 text-green-800' 
                                                                    : 'bg-red-100 text-red-800'
                                                            }`}>
                                                                {platform.is_available ? 'Available' : 'Out of Stock'}
                                                            </span>
                                                        </td>
                                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                                            {platform.delivery_time_minutes} min
                                                        </td>
                                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                                            {new Date(platform.last_updated).toLocaleDateString()}
                                                        </td>
                                                    </tr>
                                                );
                                            })}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* No Results */}
            {!loading && searchQuery && comparisons.length === 0 && !error && (
                <div className="text-center py-12">
                    <div className="text-gray-400 text-6xl mb-4">🔍</div>
                    <h3 className="text-xl font-medium text-gray-900 mb-2">No products found</h3>
                    <p className="text-gray-600 mb-4">
                        Try adjusting your search terms or filters
                    </p>
                    <button
                        onClick={clearFilters}
                        className="text-blue-600 hover:text-blue-700 font-medium"
                    >
                        Clear all filters
                    </button>
                </div>
            )}

            {/* Initial State */}
            {!searchQuery && (
                <div className="text-center py-12">
                    <div className="text-gray-400 text-6xl mb-4">🛒</div>
                    <h3 className="text-xl font-medium text-gray-900 mb-2">Start comparing products</h3>
                    <p className="text-gray-600">
                        Enter a product name above to compare prices across platforms
                    </p>
                </div>
            )}
        </div>
    );
};

export default ProductComparison; 