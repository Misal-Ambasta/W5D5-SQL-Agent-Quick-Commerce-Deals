import React, { useState, useMemo } from 'react';

interface ResultItem {
    product_name?: string;
    platform_name?: string;
    current_price?: number;
    original_price?: number;
    discount_percentage?: number;
    is_available?: boolean;
    last_updated?: string;
    category?: string;
    brand?: string;
    stock_quantity?: number;
}

interface ResultViewsProps {
    results: ResultItem[];
    bestDeal?: ResultItem;
}

interface FilterOptions {
    platform: string;
    priceRange: [number, number];
    minDiscount: number;
    availability: string;
    sortBy: string;
    sortOrder: 'asc' | 'desc';
}

export const TableView: React.FC<ResultViewsProps> = ({ results, bestDeal }) => {
    const [filters, setFilters] = useState<FilterOptions>({
        platform: 'All',
        priceRange: [0, 0],
        minDiscount: 0,
        availability: 'All',
        sortBy: 'current_price',
        sortOrder: 'asc'
    });

    // Temporary filters that change as user interacts with controls
    const [tempFilters, setTempFilters] = useState<FilterOptions>({
        platform: 'All',
        priceRange: [0, 0],
        minDiscount: 0,
        availability: 'All',
        sortBy: 'current_price',
        sortOrder: 'asc'
    });

    // Get unique platforms
    const platforms = useMemo(() => {
        const uniquePlatforms = [...new Set(results.map(r => r.platform_name || ''))].filter(Boolean);
        return ['All', ...uniquePlatforms];
    }, [results]);

    // Get price range
    const priceRange = useMemo(() => {
        const prices = results.map(r => r.current_price || 0).filter(p => p > 0);
        const min = Math.min(...prices);
        const max = Math.max(...prices);
        return [min, max] as [number, number];
    }, [results]);

    // Initialize price range filter
    React.useEffect(() => {
        if (priceRange[0] !== priceRange[1]) {
            const initialFilters = { 
                platform: 'All',
                priceRange,
                minDiscount: 0,
                availability: 'All',
                sortBy: 'current_price',
                sortOrder: 'asc' as 'asc' | 'desc'
            };
            setFilters(initialFilters);
            setTempFilters(initialFilters);
        }
    }, [priceRange]);

    // Apply filters function
    const applyFilters = () => {
        setFilters({ ...tempFilters });
    };

    // Reset filters function
    const resetFilters = () => {
        const resetFilters = {
            platform: 'All',
            priceRange,
            minDiscount: 0,
            availability: 'All',
            sortBy: 'current_price',
            sortOrder: 'asc' as 'asc' | 'desc'
        };
        setFilters(resetFilters);
        setTempFilters(resetFilters);
    };

    // Apply filters and sorting
    const filteredAndSortedResults = useMemo(() => {
        let filtered = results.filter(item => {
            // Platform filter
            if (filters.platform !== 'All' && item.platform_name !== filters.platform) return false;
            
            // Price range filter
            const price = item.current_price || 0;
            if (price < filters.priceRange[0] || price > filters.priceRange[1]) return false;
            
            // Discount filter
            if ((item.discount_percentage || 0) < filters.minDiscount) return false;
            
            // Availability filter
            if (filters.availability === 'Available Only' && !item.is_available) return false;
            if (filters.availability === 'Out of Stock Only' && item.is_available) return false;
            
            return true;
        });

        // Apply sorting
        filtered.sort((a, b) => {
            let aValue: any, bValue: any;
            
            switch (filters.sortBy) {
                case 'current_price':
                    aValue = a.current_price || 0;
                    bValue = b.current_price || 0;
                    break;
                case 'discount_percentage':
                    aValue = a.discount_percentage || 0;
                    bValue = b.discount_percentage || 0;
                    break;
                case 'product_name':
                    aValue = a.product_name || '';
                    bValue = b.product_name || '';
                    break;
                case 'platform_name':
                    aValue = a.platform_name || '';
                    bValue = b.platform_name || '';
                    break;
                default:
                    aValue = a.current_price || 0;
                    bValue = b.current_price || 0;
            }

            if (typeof aValue === 'string') {
                return filters.sortOrder === 'asc' 
                    ? aValue.localeCompare(bValue)
                    : bValue.localeCompare(aValue);
            }

            return filters.sortOrder === 'asc' ? aValue - bValue : bValue - aValue;
        });

        return filtered;
    }, [results, filters]);

    return (
        <div className="space-y-6">
            {/* Filter Controls */}
            <div className="bg-gray-50 p-4 rounded-lg">
                <h3 className="text-lg font-semibold mb-4">🔍 Filter Options</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    {/* Platform Filter */}
                    <div>
                        <label className="block text-sm font-medium mb-1">Platform</label>
                        <select
                            value={tempFilters.platform}
                            onChange={(e) => setTempFilters(prev => ({ ...prev, platform: e.target.value }))}
                            className="w-full p-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
                        >
                            {platforms.map(platform => (
                                <option key={platform} value={platform}>{platform}</option>
                            ))}
                        </select>
                    </div>

                    {/* Price Range */}
                    <div>
                        <label className="block text-sm font-medium mb-1">
                            Price Range (₹{tempFilters.priceRange[0].toFixed(0)} - ₹{tempFilters.priceRange[1].toFixed(0)})
                        </label>
                        <div className="space-y-2">
                            <div className="flex items-center space-x-2">
                                <span className="text-xs text-gray-500">Min</span>
                                <input
                                    type="range"
                                    min={priceRange[0]}
                                    max={priceRange[1]}
                                    value={tempFilters.priceRange[0]}
                                    onChange={(e) => setTempFilters(prev => ({ 
                                        ...prev, 
                                        priceRange: [Number(e.target.value), prev.priceRange[1]] 
                                    }))}
                                    className="flex-1"
                                />
                                <span className="text-xs text-gray-500">Max</span>
                            </div>
                            <input
                                type="range"
                                min={priceRange[0]}
                                max={priceRange[1]}
                                value={tempFilters.priceRange[1]}
                                onChange={(e) => setTempFilters(prev => ({ 
                                    ...prev, 
                                    priceRange: [prev.priceRange[0], Number(e.target.value)] 
                                }))}
                                className="w-full"
                            />
                        </div>
                    </div>

                    {/* Discount Filter */}
                    <div>
                        <label className="block text-sm font-medium mb-1">Min Discount (%)</label>
                        <input
                            type="number"
                            min="0"
                            max="100"
                            step="5"
                            value={tempFilters.minDiscount}
                            onChange={(e) => setTempFilters(prev => ({ ...prev, minDiscount: Number(e.target.value) }))}
                            className="w-full p-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
                        />
                    </div>

                    {/* Availability Filter */}
                    <div>
                        <label className="block text-sm font-medium mb-1">Availability</label>
                        <select
                            value={tempFilters.availability}
                            onChange={(e) => setTempFilters(prev => ({ ...prev, availability: e.target.value }))}
                            className="w-full p-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
                        >
                            <option value="All">All</option>
                            <option value="Available Only">Available Only</option>
                            <option value="Out of Stock Only">Out of Stock Only</option>
                        </select>
                    </div>
                </div>

                {/* Sorting Controls */}
                <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                        <label className="block text-sm font-medium mb-1">Sort By</label>
                        <select
                            value={tempFilters.sortBy}
                            onChange={(e) => setTempFilters(prev => ({ ...prev, sortBy: e.target.value }))}
                            className="w-full p-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
                        >
                            <option value="current_price">Current Price</option>
                            <option value="discount_percentage">Discount %</option>
                            <option value="product_name">Product Name</option>
                            <option value="platform_name">Platform</option>
                        </select>
                    </div>
                    <div>
                        <label className="block text-sm font-medium mb-1">Order</label>
                        <select
                            value={tempFilters.sortOrder}
                            onChange={(e) => setTempFilters(prev => ({ ...prev, sortOrder: e.target.value as 'asc' | 'desc' }))}
                            className="w-full p-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
                        >
                            <option value="asc">Ascending</option>
                            <option value="desc">Descending</option>
                        </select>
                    </div>
                </div>

                {/* Action Buttons */}
                <div className="mt-4 flex space-x-3">
                    <button
                        onClick={applyFilters}
                        className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 transition-colors"
                    >
                        Apply Filters
                    </button>
                    <button
                        onClick={resetFilters}
                        className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 focus:ring-2 focus:ring-gray-500 transition-colors"
                    >
                        Reset All
                    </button>
                </div>
            </div>

            {/* Results Table */}
            <div className="overflow-x-auto">
                <table className="min-w-full bg-white border border-gray-200">
                    <thead className="bg-gray-50">
                        <tr>
                            <th className="px-4 py-2 text-left text-sm font-medium text-gray-900">Product</th>
                            <th className="px-4 py-2 text-left text-sm font-medium text-gray-900">Platform</th>
                            <th className="px-4 py-2 text-left text-sm font-medium text-gray-900">Current Price</th>
                            <th className="px-4 py-2 text-left text-sm font-medium text-gray-900">Original Price</th>
                            <th className="px-4 py-2 text-left text-sm font-medium text-gray-900">Discount</th>
                            <th className="px-4 py-2 text-left text-sm font-medium text-gray-900">Savings</th>
                            <th className="px-4 py-2 text-left text-sm font-medium text-gray-900">Available</th>
                            <th className="px-4 py-2 text-left text-sm font-medium text-gray-900">Last Updated</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200">
                        {filteredAndSortedResults.map((item, index) => {
                            const isBestDeal = bestDeal && item === bestDeal;
                            const savings = (item.original_price || 0) - (item.current_price || 0);
                            
                            return (
                                <tr 
                                    key={index} 
                                    className={`${isBestDeal ? 'bg-green-50 border-green-200' : 'hover:bg-gray-50'}`}
                                >
                                    <td className="px-4 py-2 text-sm text-gray-900">
                                        {isBestDeal && <span className="mr-1">🏆</span>}
                                        {item.product_name || 'N/A'}
                                    </td>
                                    <td className="px-4 py-2 text-sm text-gray-900">{item.platform_name || 'N/A'}</td>
                                    <td className="px-4 py-2 text-sm font-semibold text-gray-900">
                                        ₹{(item.current_price || 0).toFixed(2)}
                                    </td>
                                    <td className="px-4 py-2 text-sm text-gray-500">
                                        {item.original_price ? `₹${item.original_price.toFixed(2)}` : '-'}
                                    </td>
                                    <td className="px-4 py-2 text-sm">
                                        {item.discount_percentage ? (
                                            <span className="text-red-600 font-medium">
                                                {item.discount_percentage.toFixed(1)}%
                                            </span>
                                        ) : '-'}
                                    </td>
                                    <td className="px-4 py-2 text-sm">
                                        {savings > 0 ? (
                                            <span className="text-green-600 font-medium">₹{savings.toFixed(2)}</span>
                                        ) : '-'}
                                    </td>
                                    <td className="px-4 py-2 text-sm">
                                        <span className={`px-2 py-1 rounded-full text-xs ${
                                            item.is_available 
                                                ? 'bg-green-100 text-green-800' 
                                                : 'bg-red-100 text-red-800'
                                        }`}>
                                            {item.is_available ? 'Available' : 'Out of Stock'}
                                        </span>
                                    </td>
                                    <td className="px-4 py-2 text-sm text-gray-500">
                                        {item.last_updated ? item.last_updated.split('T')[0] : '-'}
                                    </td>
                                </tr>
                            );
                        })}
                    </tbody>
                </table>
            </div>

            <div className="text-sm text-gray-600">
                Showing {filteredAndSortedResults.length} of {results.length} results
            </div>
        </div>
    );
};

export const CardView: React.FC<ResultViewsProps> = ({ results, bestDeal }) => {
    return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {results.map((item, index) => {
                const isBestDeal = bestDeal && item === bestDeal;
                const savings = (item.original_price || 0) - (item.current_price || 0);
                
                return (
                    <div 
                        key={index}
                        className={`border rounded-lg p-4 ${
                            isBestDeal 
                                ? 'border-green-400 bg-green-50 shadow-lg' 
                                : 'border-gray-200 bg-white hover:shadow-md'
                        } transition-shadow`}
                    >
                        {isBestDeal && (
                            <div className="flex items-center mb-2">
                                <span className="text-lg mr-1">🏆</span>
                                <span className="text-sm font-semibold text-green-700">BEST DEAL</span>
                            </div>
                        )}
                        
                        <div className="space-y-2">
                            <h3 className="font-semibold text-gray-900">{item.product_name || 'N/A'}</h3>
                            <p className="text-sm text-gray-600">{item.platform_name || 'N/A'}</p>
                            
                            <div className="flex items-center justify-between">
                                <div>
                                    <span className="text-lg font-bold text-gray-900">
                                        ₹{(item.current_price || 0).toFixed(2)}
                                    </span>
                                    {item.original_price && item.original_price > (item.current_price || 0) && (
                                        <span className="text-sm text-gray-500 line-through ml-2">
                                            ₹{item.original_price.toFixed(2)}
                                        </span>
                                    )}
                                </div>
                                
                                {item.discount_percentage && item.discount_percentage > 0 && (
                                    <span className="bg-red-100 text-red-800 text-xs font-medium px-2 py-1 rounded">
                                        {item.discount_percentage.toFixed(1)}% OFF
                                    </span>
                                )}
                            </div>
                            
                            {savings > 0 && (
                                <p className="text-sm text-green-600">
                                    You save: ₹{savings.toFixed(2)}
                                </p>
                            )}
                            
                            <div className="flex items-center justify-between">
                                <span className={`text-xs px-2 py-1 rounded-full ${
                                    item.is_available 
                                        ? 'bg-green-100 text-green-800' 
                                        : 'bg-red-100 text-red-800'
                                }`}>
                                    {item.is_available ? 'Available' : 'Out of Stock'}
                                </span>
                                
                                {item.last_updated && (
                                    <span className="text-xs text-gray-500">
                                        Updated: {item.last_updated.split('T')[0]}
                                    </span>
                                )}
                            </div>
                        </div>
                    </div>
                );
            })}
        </div>
    );
}; 