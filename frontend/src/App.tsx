import React, { useState, useEffect } from 'react';
import axios from 'axios';
import APIClient, { type QueryResult, type HealthStatus } from './components/APIClient';
import { TableView, CardView } from './components/ResultViews';
import ProductComparison from './components/ProductComparison';
import DealsDiscounts from './components/DealsDiscounts';
import AdvancedMonitoring from './components/AdvancedMonitoring';
import CampaignManagement from './components/CampaignManagement';
import './App.css';

// Sample queries equivalent to Streamlit version
const SAMPLE_QUERIES = [
    "Which app has cheapest onions right now?",
    "Show products with 30%+ discount on Blinkit",
    "Compare fruit prices between Zepto and Instamart",
    "Find best deals for ₹1000 grocery list",
    "Show me cheapest milk prices",
    "Which platform has best vegetable deals?",
    "Compare rice prices across all platforms",
    "Show products with maximum discount today"
];

interface ConnectionStatus {
    api: boolean;
    database: boolean;
    loading: boolean;
    error?: string;
}

interface QueryHistoryItem {
    query: string;
    timestamp: string;
    results_count: number;
    execution_time: number;
    platforms_searched: number;
    best_price: number;
    total_savings: number;
}

type PageType = 'search' | 'comparison' | 'deals' | 'campaigns' | 'monitoring' | 'advanced';
type ViewType = 'table' | 'card' | 'chart';

function App() {
    const [currentPage, setCurrentPage] = useState<PageType>('search');
    const [query, setQuery] = useState('');
    const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>({
        api: false,
        database: false,
        loading: true
    });
    const [results, setResults] = useState<QueryResult | null>(null);
    const [isSearching, setIsSearching] = useState(false);
    const [queryHistory, setQueryHistory] = useState<QueryHistoryItem[]>([]);
    const [savedSearches, setSavedSearches] = useState<string[]>([]);
    const [currentView, setCurrentView] = useState<ViewType>('table');
    const [apiClient] = useState(new APIClient());
    
    // Advanced search options
    const [advancedMode, setAdvancedMode] = useState(false);
    const [pageSize, setPageSize] = useState(20);
    const [currentPageNum, setCurrentPageNum] = useState(1);
    const [resultFormat, setResultFormat] = useState('structured');
    const [samplingMethod, setSamplingMethod] = useState('none');
    const [sampleSize, setSampleSize] = useState(1000);
    const [queryOptimization, setQueryOptimization] = useState(false);
    const [totalPages, setTotalPages] = useState(1);

    // Check API and Database connection status
    useEffect(() => {
        checkConnectionStatus();
        const interval = setInterval(checkConnectionStatus, 30000);
        return () => clearInterval(interval);
    }, []);

    // Auto-search when page changes in advanced mode
    useEffect(() => {
        if (advancedMode && currentPageNum > 1 && query.trim()) {
            handleSearch();
        }
    }, [currentPageNum]);

    const checkConnectionStatus = async () => {
        try {
            setConnectionStatus(prev => ({ ...prev, loading: true }));
            const healthData = await apiClient.healthCheck();
            
            setConnectionStatus({
                api: healthData.status === 'healthy',
                database: healthData.database === 'connected',
                loading: false,
                error: healthData.message
            });
        } catch (error: any) {
            console.error('Health check failed:', error);
            setConnectionStatus({
                api: false,
                database: false,
                loading: false,
                error: 'Failed to connect to API'
            });
        }
    };

    const addToHistory = (query: string, results: QueryResult, executionTime: number) => {
        const resultsArray = results.results || [];
        const platforms = new Set(resultsArray.map(item => item.platform_name || '')).size;
        const bestPrice = Math.min(...resultsArray.map(item => item.current_price || Infinity));
        const totalSavings = resultsArray.reduce((sum, item) => {
            const savings = (item.original_price || 0) - (item.current_price || 0);
            return sum + (savings > 0 ? savings : 0);
        }, 0);

        const historyItem: QueryHistoryItem = {
            query,
            timestamp: new Date().toISOString(),
            results_count: resultsArray.length,
            execution_time: executionTime,
            platforms_searched: platforms,
            best_price: isFinite(bestPrice) ? bestPrice : 0,
            total_savings: totalSavings
        };

        setQueryHistory(prev => [historyItem, ...prev.slice(0, 49)]);
    };

    const handleSearch = async () => {
        if (!query.trim()) {
            alert('Please enter a query to search.');
            return;
        }

        if (!connectionStatus.api || !connectionStatus.database) {
            alert('API or Database is not connected. Please wait for connection.');
            return;
        }

        setIsSearching(true);
        setResults(null);

        try {
            const startTime = Date.now();
            let response: QueryResult;

            if (advancedMode) {
                response = await apiClient.processAdvancedQuery({
                    query: query.trim(),
                    page: currentPageNum,
                    page_size: pageSize,
                    sampling_method: samplingMethod,
                    sample_size: sampleSize,
                    result_format: resultFormat
                });
                
                // Calculate total pages from response
                if (response.total_results) {
                    setTotalPages(Math.ceil(response.total_results / pageSize));
                }
            } else {
                response = await apiClient.processNaturalLanguageQuery(query.trim());
                setTotalPages(1);
                setCurrentPageNum(1);
            }

            const executionTime = (Date.now() - startTime) / 1000;
            
            setResults({
                ...response,
                execution_time: response.execution_time || executionTime
            });

            // Add to query history
            addToHistory(query.trim(), response, response.execution_time || executionTime);

        } catch (error: any) {
            console.error('Query failed:', error);
            let errorMessage = 'Query failed. Please try again.';
            
            if (error.response?.data?.error) {
                errorMessage = error.response.data.error;
            } else if (error.message) {
                errorMessage = error.message;
            }

            setResults({
                error: errorMessage,
                query: query.trim()
            });
        } finally {
            setIsSearching(false);
        }
    };

    const handleSampleQuery = (sampleQuery: string) => {
        setQuery(sampleQuery);
    };

    const handleKeyPress = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSearch();
        }
    };

    const exportResults = (format: 'json' | 'csv') => {
        if (!results?.results) return;

        let content: string;
        let filename: string;
        let mimeType: string;

        if (format === 'json') {
            content = JSON.stringify(results, null, 2);
            filename = `search-results-${Date.now()}.json`;
            mimeType = 'application/json';
        } else {
            // CSV format
            const headers = ['Product', 'Platform', 'Current Price', 'Original Price', 'Discount %', 'Available'];
            const rows = results.results.map(item => [
                item.product_name || '',
                item.platform_name || '',
                item.current_price || 0,
                item.original_price || 0,
                item.discount_percentage || 0,
                item.is_available ? 'Yes' : 'No'
            ]);
            
            content = [headers, ...rows].map(row => row.join(',')).join('\n');
            filename = `search-results-${Date.now()}.csv`;
            mimeType = 'text/csv';
        }

        const blob = new Blob([content], { type: mimeType });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.click();
        URL.revokeObjectURL(url);
    };

    const getBestDeal = () => {
        if (!results?.results) return null;
        return results.results.reduce((best, current) => 
            (current.current_price || Infinity) < (best.current_price || Infinity) ? current : best
        );
    };

    const renderNavigationMenu = () => (
        <div className="bg-white border-b border-gray-200">
            <div className="max-w-7xl mx-auto px-4">
                <nav className="flex space-x-8 overflow-x-auto">
                    {[
                        { id: 'search', label: 'Natural Language Search', icon: '🔍' },
                        { id: 'comparison', label: 'Product Comparison', icon: '🔄' },
                        { id: 'deals', label: 'Deals & Discounts', icon: '🎯' },
                        { id: 'campaigns', label: 'Promotional Campaigns', icon: '🎪' },
                        { id: 'monitoring', label: 'System Monitoring', icon: '📊' },
                        { id: 'advanced', label: 'Advanced Options', icon: '⚙️' }
                    ].map(page => (
                        <button
                            key={page.id}
                            onClick={() => setCurrentPage(page.id as PageType)}
                            className={`py-4 px-2 border-b-2 font-medium text-sm whitespace-nowrap ${
                                currentPage === page.id
                                    ? 'border-blue-500 text-blue-600'
                                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                            }`}
                        >
                            <span className="mr-1">{page.icon}</span>
                            {page.label}
                        </button>
                    ))}
                </nav>
            </div>
        </div>
    );

    const renderSearchPage = () => (
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
            {/* Sidebar */}
            <div className="lg:col-span-1">
                <div className="bg-white rounded-lg shadow-sm p-6 space-y-6">
                    {/* Connection Status */}
                    <div>
                        <h3 className="text-lg font-semibold mb-4">🔌 Connection Status</h3>
                        <div className="space-y-2">
                            {connectionStatus.loading ? (
                                <div className="text-yellow-600">⏳ Checking connections...</div>
                            ) : (
                                <>
                                    <div className={`flex items-center space-x-2 ${connectionStatus.api ? 'text-green-600' : 'text-red-600'}`}>
                                        <span>{connectionStatus.api ? '✅' : '❌'}</span>
                                        <span>API Connected</span>
                                    </div>
                                    <div className={`flex items-center space-x-2 ${connectionStatus.database ? 'text-green-600' : 'text-red-600'}`}>
                                        <span>{connectionStatus.database ? '✅' : '❌'}</span>
                                        <span>Database Connected</span>
                                    </div>
                                </>
                            )}
                            {connectionStatus.error && (
                                <div className="text-red-600 text-sm">
                                    Error: {connectionStatus.error}
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Advanced Mode Toggle */}
                    <div>
                        <h3 className="text-lg font-semibold mb-4">⚙️ Search Options</h3>
                        <div className="space-y-3">
                            <label className="flex items-center">
                                <input
                                    type="checkbox"
                                    checked={advancedMode}
                                    onChange={(e) => setAdvancedMode(e.target.checked)}
                                    className="mr-2"
                                />
                                Advanced Mode
                            </label>
                            
                            {advancedMode && (
                                <div className="space-y-3 pl-4">
                                    <div>
                                        <label className="block text-sm font-medium mb-1">Page Size</label>
                                        <select
                                            value={pageSize}
                                            onChange={(e) => {
                                                setPageSize(Number(e.target.value));
                                                setCurrentPageNum(1);
                                            }}
                                            className="w-full p-1 border border-gray-300 rounded text-sm"
                                        >
                                            <option value={10}>10</option>
                                            <option value={20}>20</option>
                                            <option value={50}>50</option>
                                            <option value={100}>100</option>
                                        </select>
                                    </div>
                                    
                                    <div>
                                        <label className="block text-sm font-medium mb-1">Result Format</label>
                                        <select
                                            value={resultFormat}
                                            onChange={(e) => setResultFormat(e.target.value)}
                                            className="w-full p-1 border border-gray-300 rounded text-sm"
                                        >
                                            <option value="structured">Structured</option>
                                            <option value="raw">Raw</option>
                                            <option value="summary">Summary</option>
                                            <option value="comparison">Comparison</option>
                                            <option value="chart_data">Chart Data</option>
                                        </select>
                                    </div>

                                    <div>
                                        <label className="block text-sm font-medium mb-1">Sampling Method</label>
                                        <select
                                            value={samplingMethod}
                                            onChange={(e) => setSamplingMethod(e.target.value)}
                                            className="w-full p-1 border border-gray-300 rounded text-sm"
                                        >
                                            <option value="none">No Sampling</option>
                                            <option value="random">Random</option>
                                            <option value="systematic">Systematic</option>
                                            <option value="stratified">Stratified</option>
                                            <option value="top_n">Top N</option>
                                        </select>
                                    </div>

                                    {samplingMethod !== 'none' && (
                                        <div>
                                            <label className="block text-sm font-medium mb-1">Sample Size</label>
                                            <select
                                                value={sampleSize}
                                                onChange={(e) => setSampleSize(Number(e.target.value))}
                                                className="w-full p-1 border border-gray-300 rounded text-sm"
                                            >
                                                <option value={100}>100</option>
                                                <option value={500}>500</option>
                                                <option value={1000}>1000</option>
                                                <option value={5000}>5000</option>
                                                <option value={10000}>10000</option>
                                            </select>
                                        </div>
                                    )}

                                    <label className="flex items-center">
                                        <input
                                            type="checkbox"
                                            checked={queryOptimization}
                                            onChange={(e) => setQueryOptimization(e.target.checked)}
                                            className="mr-2"
                                        />
                                        <span className="text-sm">Query Optimization</span>
                                    </label>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Sample Queries */}
                    <div>
                        <h3 className="text-lg font-semibold mb-4">🚀 Sample Queries</h3>
                        <div className="space-y-2">
                            {SAMPLE_QUERIES.slice(0, 6).map((sampleQuery, index) => (
                                <button
                                    key={index}
                                    onClick={() => handleSampleQuery(sampleQuery)}
                                    className="w-full text-left p-2 text-sm bg-blue-50 hover:bg-blue-100 rounded border text-blue-700 transition-colors"
                                >
                                    {sampleQuery}
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Query History */}
                    {queryHistory.length > 0 && (
                        <div>
                            <h3 className="text-lg font-semibold mb-4">📚 Recent Queries</h3>
                            <div className="space-y-1 max-h-64 overflow-y-auto">
                                {queryHistory.slice(0, 10).map((historyQuery, index) => (
                                    <div key={index} className="bg-gray-50 p-2 rounded text-sm">
                                        <button
                                            onClick={() => setQuery(historyQuery.query)}
                                            className="w-full text-left hover:text-blue-600 truncate"
                                            title={historyQuery.query}
                                        >
                                            {historyQuery.query}
                                        </button>
                                        <div className="text-xs text-gray-500 mt-1">
                                            {historyQuery.results_count} results • {historyQuery.execution_time.toFixed(2)}s
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            </div>

            {/* Main Content */}
            <div className="lg:col-span-3">
                <div className="bg-white rounded-lg shadow-sm p-6">
                    {/* Search Section */}
                    <div className="mb-8">
                        <h2 className="text-xl font-semibold mb-4">🔍 Ask Your Question</h2>
                        
                        <div className="space-y-4">
                            <div>
                                <textarea
                                    value={query}
                                    onChange={(e) => setQuery(e.target.value)}
                                    onKeyPress={handleKeyPress}
                                    placeholder="Type your question here... (e.g., 'Which app has cheapest onions right now?')"
                                    className="w-full p-4 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                                    rows={3}
                                    disabled={isSearching}
                                />
                            </div>
                            
                            <div className="flex flex-wrap gap-2">
                                <button
                                    onClick={handleSearch}
                                    disabled={isSearching || !connectionStatus.api || !connectionStatus.database}
                                    className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center space-x-2 transition-colors"
                                >
                                    {isSearching ? (
                                        <>
                                            <span className="animate-spin">⏳</span>
                                            <span>Searching...</span>
                                        </>
                                    ) : (
                                        <>
                                            <span>🔍</span>
                                            <span>Search</span>
                                        </>
                                    )}
                                </button>
                                
                                <button
                                    onClick={() => handleSampleQuery(SAMPLE_QUERIES[Math.floor(Math.random() * SAMPLE_QUERIES.length)])}
                                    className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
                                >
                                    🎲 Random Query
                                </button>
                                
                                <button
                                    onClick={() => {
                                        setQuery('');
                                        setResults(null);
                                    }}
                                    className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
                                >
                                    🗑️ Clear
                                </button>
                            </div>
                        </div>
                    </div>

                    {/* Results Section */}
                    {results && (
                        <div className="border-t pt-6">
                            {results.error ? (
                                <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                                    <div className="flex items-center space-x-2 text-red-800">
                                        <span>❌</span>
                                        <span className="font-semibold">Issue: API Error</span>
                                    </div>
                                    <p className="text-red-700 mt-2">{results.error}</p>
                                    {results.query && (
                                        <p className="text-red-600 text-sm mt-2">Query: "{results.query}"</p>
                                    )}
                                </div>
                            ) : results.results && results.results.length > 0 ? (
                                <div>
                                    {/* Results Summary */}
                                    <div className="mb-6">
                                        <div className="flex items-center justify-between mb-4">
                                            <h3 className="text-lg font-semibold">📊 Search Results</h3>
                                            <div className="flex items-center space-x-4">
                                                {results.execution_time && (
                                                    <span className="text-sm text-gray-500">
                                                        {results.execution_time.toFixed(2)}s
                                                    </span>
                                                )}
                                                {results.cached && (
                                                    <span className="text-sm text-blue-600">📋 Cached</span>
                                                )}
                                            </div>
                                        </div>

                                        {/* Metrics */}
                                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                                            <div className="bg-blue-50 p-3 rounded">
                                                <div className="text-sm text-blue-600">Total Results</div>
                                                <div className="text-lg font-semibold">{results.results.length}</div>
                                            </div>
                                            <div className="bg-green-50 p-3 rounded">
                                                <div className="text-sm text-green-600">Platforms</div>
                                                <div className="text-lg font-semibold">
                                                    {new Set(results.results.map(r => r.platform_name)).size}
                                                </div>
                                            </div>
                                            <div className="bg-yellow-50 p-3 rounded">
                                                <div className="text-sm text-yellow-600">Avg Discount</div>
                                                <div className="text-lg font-semibold">
                                                    {(results.results.reduce((sum, r) => sum + (r.discount_percentage || 0), 0) / results.results.length).toFixed(1)}%
                                                </div>
                                            </div>
                                            <div className="bg-purple-50 p-3 rounded">
                                                <div className="text-sm text-purple-600">Best Price</div>
                                                <div className="text-lg font-semibold">
                                                    ₹{Math.min(...results.results.map(r => r.current_price || Infinity)).toFixed(2)}
                                                </div>
                                            </div>
                                        </div>

                                        {/* Best Deal Highlight */}
                                        {getBestDeal() && (
                                            <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-4">
                                                <div className="flex items-center space-x-2">
                                                    <span className="text-lg">🏆</span>
                                                    <span className="font-semibold text-green-800">Best Deal:</span>
                                                    <span className="text-green-700">
                                                        {getBestDeal()?.product_name} at {getBestDeal()?.platform_name} for ₹{getBestDeal()?.current_price?.toFixed(2)}
                                                    </span>
                                                </div>
                                            </div>
                                        )}

                                        {/* Export Options */}
                                        <div className="flex items-center justify-between mb-4">
                                            <div className="flex space-x-2">
                                                <button
                                                    onClick={() => setCurrentView('table')}
                                                    className={`px-3 py-1 rounded text-sm ${currentView === 'table' ? 'bg-blue-100 text-blue-800' : 'bg-gray-100 text-gray-700'}`}
                                                >
                                                    📋 Table
                                                </button>
                                                <button
                                                    onClick={() => setCurrentView('card')}
                                                    className={`px-3 py-1 rounded text-sm ${currentView === 'card' ? 'bg-blue-100 text-blue-800' : 'bg-gray-100 text-gray-700'}`}
                                                >
                                                    🃏 Cards
                                                </button>
                                            </div>
                                            
                                            <div className="flex space-x-2">
                                                <button
                                                    onClick={() => exportResults('json')}
                                                    className="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
                                                >
                                                    📄 Export JSON
                                                </button>
                                                <button
                                                    onClick={() => exportResults('csv')}
                                                    className="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
                                                >
                                                    📊 Export CSV
                                                </button>
                                            </div>
                                        </div>
                                    </div>

                                    {/* Results Display */}
                                    {currentView === 'table' ? (
                                        <TableView results={results.results} bestDeal={getBestDeal()} />
                                    ) : (
                                        <CardView results={results.results} bestDeal={getBestDeal()} />
                                    )}

                                    {/* Pagination Controls */}
                                    {advancedMode && totalPages > 1 && (
                                        <div className="mt-6 flex items-center justify-between">
                                            <div className="text-sm text-gray-700">
                                                Showing page {currentPageNum} of {totalPages}
                                                {results.total_results && (
                                                    <span> ({results.total_results} total results)</span>
                                                )}
                                            </div>
                                            <div className="flex items-center space-x-2">
                                                <button
                                                    onClick={() => {
                                                        setCurrentPageNum(Math.max(1, currentPageNum - 1));
                                                    }}
                                                    disabled={currentPageNum <= 1 || isSearching}
                                                    className="px-3 py-1 border border-gray-300 rounded text-sm hover:bg-gray-50 disabled:bg-gray-100 disabled:cursor-not-allowed"
                                                >
                                                    ← Previous
                                                </button>

                                                <div className="flex items-center space-x-1">
                                                    {[...Array(Math.min(5, totalPages))].map((_, index) => {
                                                        let pageNum = currentPageNum - 2 + index;
                                                        
                                                        if (pageNum < 1) {
                                                            pageNum = index + 1;
                                                        }
                                                        
                                                        if (pageNum > totalPages) {
                                                            pageNum = totalPages - (4 - index);
                                                        }
                                                        
                                                        if (pageNum < 1 || pageNum > totalPages) return null;
                                                        
                                                        return (
                                                            <button
                                                                key={pageNum}
                                                                onClick={() => setCurrentPageNum(pageNum)}
                                                                disabled={isSearching}
                                                                className={`px-3 py-1 text-sm border rounded ${
                                                                    currentPageNum === pageNum
                                                                        ? 'bg-blue-600 text-white border-blue-600'
                                                                        : 'border-gray-300 hover:bg-gray-50'
                                                                } disabled:bg-gray-100 disabled:cursor-not-allowed`}
                                                            >
                                                                {pageNum}
                                                            </button>
                                                        );
                                                    })}
                                                </div>

                                                <button
                                                    onClick={() => {
                                                        setCurrentPageNum(Math.min(totalPages, currentPageNum + 1));
                                                    }}
                                                    disabled={currentPageNum >= totalPages || isSearching}
                                                    className="px-3 py-1 border border-gray-300 rounded text-sm hover:bg-gray-50 disabled:bg-gray-100 disabled:cursor-not-allowed"
                                                >
                                                    Next →
                                                </button>
                                            </div>
                                        </div>
                                    )}

                                    {/* Advanced Metrics */}
                                    {advancedMode && results.total_results && (
                                        <div className="mt-6 p-4 bg-gray-50 rounded-lg">
                                            <h4 className="font-semibold text-gray-900 mb-3">📈 Advanced Analytics</h4>
                                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                                                <div>
                                                    <span className="text-gray-600">Query Complexity:</span>
                                                    <div className="font-medium">{results.query_complexity || 'Standard'}</div>
                                                </div>
                                                <div>
                                                    <span className="text-gray-600">Sampling Method:</span>
                                                    <div className="font-medium capitalize">{samplingMethod.replace('_', ' ')}</div>
                                                </div>
                                                {samplingMethod !== 'none' && (
                                                    <div>
                                                        <span className="text-gray-600">Sample Size:</span>
                                                        <div className="font-medium">{sampleSize.toLocaleString()}</div>
                                                    </div>
                                                )}
                                                <div>
                                                    <span className="text-gray-600">Result Format:</span>
                                                    <div className="font-medium capitalize">{resultFormat.replace('_', ' ')}</div>
                                                </div>
                                                {results.relevant_tables && (
                                                    <div className="col-span-2 md:col-span-4">
                                                        <span className="text-gray-600">Tables Accessed:</span>
                                                        <div className="font-medium">{results.relevant_tables.join(', ')}</div>
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    )}
                                </div>
                            ) : (
                                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                                    <div className="flex items-center space-x-2 text-yellow-800">
                                        <span>ℹ️</span>
                                        <span>No results found for your query.</span>
                                    </div>
                                    {results.suggestions && results.suggestions.length > 0 && (
                                        <div className="mt-3">
                                            <p className="text-sm text-yellow-700 mb-2">Try these suggestions:</p>
                                            {results.suggestions.map((suggestion, index) => (
                                                <button
                                                    key={index}
                                                    onClick={() => setQuery(suggestion)}
                                                    className="block text-sm text-blue-600 hover:text-blue-800 mb-1"
                                                >
                                                    🔄 {suggestion}
                                                </button>
                                            ))}
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );

    const renderPlaceholderPage = (title: string, description: string) => (
        <div className="text-center py-12">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">{title}</h2>
            <p className="text-gray-600 mb-8">{description}</p>
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 max-w-md mx-auto">
                <p className="text-blue-800">This feature will be implemented to match the streamlit functionality.</p>
                <p className="text-blue-600 text-sm mt-2">Currently available: Natural Language Search with advanced filtering and export options.</p>
            </div>
        </div>
    );

    return (
        <div className="min-h-screen bg-gray-50">
            {/* Header */}
            <header className="bg-white shadow-sm border-b">
                <div className="max-w-7xl mx-auto px-4 py-6">
                    <h1 className="text-3xl font-bold text-blue-600 text-center">
                        🛒 Quick Commerce Price Comparison
                    </h1>
                    <p className="text-center text-gray-600 mt-2">
                        Find the best prices and deals across Blinkit, Zepto, Instamart, BigBasket Now, and more!
                    </p>
                </div>
            </header>

            {/* Navigation */}
            {renderNavigationMenu()}

            {/* Main Content */}
            <div className="max-w-7xl mx-auto px-4 py-8">
                {currentPage === 'search' && renderSearchPage()}
                {currentPage === 'comparison' && <ProductComparison />}
                {currentPage === 'deals' && <DealsDiscounts />}
                {currentPage === 'campaigns' && <CampaignManagement />}
                {currentPage === 'monitoring' && <AdvancedMonitoring />}
                {currentPage === 'advanced' && renderPlaceholderPage(
                    '⚙️ Advanced Query Options',
                    'Advanced search options are now integrated into the main search page. Enable "Advanced Mode" in the search section to access pagination, sampling methods, result formats, and query optimization features.'
                )}
            </div>
        </div>
    );
}

export default App;
