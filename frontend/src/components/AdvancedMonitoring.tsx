import React, { useState, useEffect, useCallback } from 'react';
import APIClient from './APIClient';

interface HealthStatus {
    status: string;
    timestamp: string;
    version: string;
    components: {
        database: {
            status: string;
            message: string;
            connection_pool?: any;
            recent_errors?: number;
            recommendations?: string[];
        };
        cache: {
            status: string;
            memory_cache?: any;
            redis_cache?: any;
        };
        system?: {
            status: string;
            message: string;
        };
    };
}

interface DatabasePerformance {
    connection_pool: {
        active_connections: number;
        idle_connections: number;
        total_connections: number;
        max_connections: number;
        connection_wait_time: number;
    };
    query_performance: {
        avg_query_time: number;
        slow_queries_count: number;
        queries_per_second: number;
        cache_hit_ratio: number;
    };
    resource_usage: {
        cpu_usage: number;
        memory_usage: number;
        disk_usage: number;
        network_io: number;
    };
    recent_errors: any[];
    recommendations: string[];
}

interface CacheStats {
    overall_status: string;
    memory_cache: {
        status: string;
        hit_rate: number;
        miss_rate: number;
        total_requests: number;
        cache_size: number;
        max_size: number;
        eviction_count: number;
    };
    redis_cache: {
        status: string;
        memory_usage: number;
        memory_usage_human: string;
        connected_clients: number;
        total_commands_processed: number;
        keyspace_hits: number;
        keyspace_misses: number;
        hit_rate: number;
    };
    performance_metrics: {
        avg_response_time: number;
        cache_efficiency: number;
        memory_efficiency: number;
    };
}

interface MetricsSummary {
    summary: {
        system_efficiency_score: number;
        performance_grade: string;
        uptime: string;
        total_api_calls: number;
    };
    database: {
        avg_response_time: number;
        active_connections: number;
        query_success_rate: number;
    };
    cache: {
        hit_rate: number;
        memory_usage: number;
        avg_response_time: number;
    };
    api: {
        requests_per_minute: number;
        error_rate: number;
        avg_response_time: number;
    };
    alerts: any[];
}

interface RealtimeMetrics {
    timestamp: string;
    system: {
        cpu_usage: number;
        memory_usage: number;
        disk_usage: number;
        network_io: number;
    };
    database: {
        active_queries: number;
        connections: number;
        query_time: number;
    };
    cache: {
        requests_per_second: number;
        hit_rate: number;
        memory_usage: number;
    };
    api: {
        requests_per_second: number;
        active_connections: number;
        response_time: number;
    };
}

const AdvancedMonitoring: React.FC = () => {
    const [apiClient] = useState(() => new APIClient());
    const [health, setHealth] = useState<HealthStatus | null>(null);
    const [dbPerformance, setDbPerformance] = useState<DatabasePerformance | null>(null);
    const [cacheStats, setCacheStats] = useState<CacheStats | null>(null);
    const [metricsSummary, setMetricsSummary] = useState<MetricsSummary | null>(null);
    const [realtimeMetrics, setRealtimeMetrics] = useState<RealtimeMetrics | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [autoRefresh, setAutoRefresh] = useState(true);
    const [refreshInterval, setRefreshInterval] = useState(5000);

    const loadAllMetrics = useCallback(async () => {
        setLoading(true);
        setError(null);

        try {
            const [healthRes, dbRes, cacheRes, summaryRes, realtimeRes] = await Promise.allSettled([
                apiClient.getSystemHealth(),
                apiClient.getDatabasePerformance(),
                apiClient.getCacheStats(),
                apiClient.getMetricsSummary(),
                apiClient.getRealtimeMetrics()
            ]);

            if (healthRes.status === 'fulfilled') {
                setHealth(healthRes.value);
            }
            if (dbRes.status === 'fulfilled') {
                setDbPerformance(dbRes.value);
            }
            if (cacheRes.status === 'fulfilled') {
                setCacheStats(cacheRes.value);
            }
            if (summaryRes.status === 'fulfilled') {
                setMetricsSummary(summaryRes.value);
            }
            if (realtimeRes.status === 'fulfilled') {
                setRealtimeMetrics(realtimeRes.value);
            }

            // Check if any failed
            const failedCount = [healthRes, dbRes, cacheRes, summaryRes, realtimeRes]
                .filter(res => res.status === 'rejected').length;
            
            if (failedCount > 0) {
                setError(`${failedCount} monitoring endpoints failed to load`);
            }

        } catch (err: any) {
            setError(err.message || 'Failed to load monitoring data');
            console.error('Monitoring error:', err);
        } finally {
            setLoading(false);
        }
    }, [apiClient]);

    useEffect(() => {
        loadAllMetrics();
    }, [loadAllMetrics]);

    useEffect(() => {
        if (autoRefresh) {
            const interval = setInterval(loadAllMetrics, refreshInterval);
            return () => clearInterval(interval);
        }
    }, [autoRefresh, refreshInterval, loadAllMetrics]);

    const getStatusColor = (status: string | undefined | null) => {
        if (!status) return 'text-gray-600 bg-gray-100';
        switch (status.toLowerCase()) {
            case 'healthy': return 'text-green-600 bg-green-100';
            case 'degraded': return 'text-yellow-600 bg-yellow-100';
            case 'unhealthy': return 'text-red-600 bg-red-100';
            default: return 'text-gray-600 bg-gray-100';
        }
    };

    const getPerformanceColor = (percentage: number) => {
        if (percentage >= 90) return 'text-green-600';
        if (percentage >= 70) return 'text-yellow-600';
        return 'text-red-600';
    };

    const formatBytes = (bytes: number) => {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    };

    const formatUptime = (uptimeStr: string) => {
        // Convert uptime string to readable format
        return uptimeStr || 'Unknown';
    };

    return (
        <div className="max-w-7xl mx-auto p-6 space-y-6">
            <div className="flex justify-between items-center mb-8">
                <div>
                    <h1 className="text-3xl font-bold text-gray-900 mb-2">📊 Advanced System Monitoring</h1>
                    <p className="text-gray-600">Real-time system health, performance metrics, and analytics</p>
                </div>
                <div className="flex items-center space-x-4">
                    <label className="flex items-center space-x-2">
                        <input
                            type="checkbox"
                            checked={autoRefresh}
                            onChange={(e) => setAutoRefresh(e.target.checked)}
                            className="w-4 h-4 text-blue-600"
                        />
                        <span className="text-sm">Auto Refresh</span>
                    </label>
                    <select
                        value={refreshInterval}
                        onChange={(e) => setRefreshInterval(Number(e.target.value))}
                        disabled={!autoRefresh}
                        className="p-2 border border-gray-300 rounded text-sm"
                    >
                        <option value={5000}>5s</option>
                        <option value={10000}>10s</option>
                        <option value={30000}>30s</option>
                        <option value={60000}>1m</option>
                    </select>
                    <button
                        onClick={loadAllMetrics}
                        disabled={loading}
                        className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 transition-colors"
                    >
                        {loading ? 'Refreshing...' : 'Refresh'}
                    </button>
                </div>
            </div>

            {error && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                    <div className="flex items-center">
                        <span className="text-red-600 mr-2">⚠️</span>
                        <span className="text-red-700">{error}</span>
                    </div>
                </div>
            )}

            {/* System Health Overview */}
            {health && (
                <div className="bg-white rounded-lg shadow-md p-6">
                    <h2 className="text-xl font-bold text-gray-900 mb-4">🏥 System Health Overview</h2>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div className="text-center">
                            <div className={`inline-flex px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(health.status)}`}>
                                {health.status.toUpperCase()}
                            </div>
                            <div className="text-sm text-gray-600 mt-1">Overall Status</div>
                        </div>
                        <div className="text-center">
                            <div className="text-lg font-bold text-gray-900">{health.version}</div>
                            <div className="text-sm text-gray-600">Version</div>
                        </div>
                        <div className="text-center">
                            <div className="text-lg font-bold text-gray-900">
                                {new Date(health.timestamp).toLocaleTimeString()}
                            </div>
                            <div className="text-sm text-gray-600">Last Updated</div>
                        </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
                        {Object.entries(health.components).map(([component, data]) => (
                            <div key={component} className="border border-gray-200 rounded-lg p-4">
                                <div className="flex items-center justify-between mb-2">
                                    <h3 className="font-semibold capitalize">{component}</h3>
                                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(data.status)}`}>
                                        {data.status}
                                    </span>
                                </div>
                                <p className="text-sm text-gray-600">{data.message}</p>
                                {data.recommendations && data.recommendations.length > 0 && (
                                    <div className="mt-2">
                                        <div className="text-xs text-gray-500">Recommendations:</div>
                                        <ul className="text-xs text-gray-600 list-disc list-inside">
                                            {data.recommendations.slice(0, 2).map((rec, idx) => (
                                                <li key={idx}>{rec}</li>
                                            ))}
                                        </ul>
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Performance Summary */}
            {metricsSummary && (
                <div className="bg-white rounded-lg shadow-md p-6">
                    <h2 className="text-xl font-bold text-gray-900 mb-4">⚡ Performance Summary</h2>
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                        <div className="text-center">
                            <div className={`text-3xl font-bold ${getPerformanceColor(metricsSummary.summary.system_efficiency_score)}`}>
                                {metricsSummary.summary.system_efficiency_score}%
                            </div>
                            <div className="text-sm text-gray-600">System Efficiency</div>
                            <div className="text-xs text-gray-500">Grade: {metricsSummary.summary.performance_grade}</div>
                        </div>
                        <div className="text-center">
                            <div className="text-2xl font-bold text-gray-900">{formatUptime(metricsSummary.summary.uptime)}</div>
                            <div className="text-sm text-gray-600">Uptime</div>
                        </div>
                        <div className="text-center">
                            <div className="text-2xl font-bold text-gray-900">{metricsSummary.summary.total_api_calls?.toLocaleString() || '0'}</div>
                            <div className="text-sm text-gray-600">Total API Calls</div>
                        </div>
                        <div className="text-center">
                            <div className="text-2xl font-bold text-gray-900">{metricsSummary.alerts?.length || 0}</div>
                            <div className="text-sm text-gray-600">Active Alerts</div>
                        </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        <div className="space-y-3">
                            <h3 className="font-semibold text-gray-900">🗄️ Database</h3>
                            <div className="space-y-2 text-sm">
                                <div className="flex justify-between">
                                    <span>Response Time:</span>
                                    <span className="font-medium">{metricsSummary.database?.avg_response_time != null ? `${metricsSummary.database.avg_response_time?.toFixed(2)}ms` : '-'}</span>
                                </div>
                                <div className="flex justify-between">
                                    <span>Active Connections:</span>
                                    <span className="font-medium">{metricsSummary.database?.active_connections != null ? metricsSummary.database.active_connections : '-'}</span>
                                </div>
                                <div className="flex justify-between">
                                    <span>Success Rate:</span>
                                    <span className={`font-medium ${getPerformanceColor(metricsSummary.database?.query_success_rate)}`}>{metricsSummary.database?.query_success_rate != null ? `${metricsSummary.database.query_success_rate?.toFixed(1)}%` : '-'}</span>
                                </div>
                            </div>
                        </div>

                        <div className="space-y-3">
                            <h3 className="font-semibold text-gray-900">🚀 Cache</h3>
                            <div className="space-y-2 text-sm">
                                <div className="flex justify-between">
                                    <span>Hit Rate:</span>
                                    <span className={`font-medium ${getPerformanceColor(metricsSummary.cache?.hit_rate)}`}>{metricsSummary.cache?.hit_rate != null ? `${metricsSummary.cache.hit_rate?.toFixed(1)}%` : '-'}</span>
                                </div>
                                <div className="flex justify-between">
                                    <span>Memory Usage:</span>
                                    <span className="font-medium">{metricsSummary.cache?.memory_usage != null ? formatBytes(metricsSummary.cache.memory_usage) : '-'}</span>
                                </div>
                                <div className="flex justify-between">
                                    <span>Response Time:</span>
                                    <span className="font-medium">{metricsSummary.cache?.avg_response_time != null ? `${metricsSummary.cache.avg_response_time?.toFixed(2)}ms` : '-'}</span>
                                </div>
                            </div>
                        </div>

                        <div className="space-y-3">
                            <h3 className="font-semibold text-gray-900">🌐 API</h3>
                            <div className="space-y-2 text-sm">
                                <div className="flex justify-between">
                                    <span>Requests/minute:</span>
                                    <span className="font-medium">{metricsSummary.api?.requests_per_minute != null ? metricsSummary.api.requests_per_minute : '-'}</span>
                                </div>
                                <div className="flex justify-between">
                                    <span>Error Rate:</span>
                                    <span className={`font-medium ${metricsSummary.api?.error_rate != null && metricsSummary.api.error_rate > 5 ? 'text-red-600' : 'text-green-600'}`}>{metricsSummary.api?.error_rate != null ? `${metricsSummary.api.error_rate?.toFixed(2)}%` : '-'}</span>
                                </div>
                                <div className="flex justify-between">
                                    <span>Response Time:</span>
                                    <span className="font-medium">{metricsSummary.api?.avg_response_time != null ? `${metricsSummary.api.avg_response_time?.toFixed(2)}ms` : '-'}</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Real-time Metrics */}
            {realtimeMetrics && (
                <div className="bg-white rounded-lg shadow-md p-6">
                    <h2 className="text-xl font-bold text-gray-900 mb-4">⏱️ Real-time Metrics</h2>
                    <div className="text-sm text-gray-600 mb-4">
                        Last updated: {new Date(realtimeMetrics.timestamp).toLocaleString()}
                    </div>
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                        <div className="space-y-3">
                            <h3 className="font-semibold text-gray-900">💻 System</h3>
                            <div className="space-y-2 text-sm">
                                <div className="flex justify-between">
                                    <span>CPU Usage:</span>
                                    <span className={`font-medium ${getPerformanceColor(100 - realtimeMetrics.system.cpu_usage)}`}>
                                        {realtimeMetrics?.system.cpu_usage?.toFixed(1)}%
                                    </span>
                                </div>
                                <div className="flex justify-between">
                                    <span>Memory:</span>
                                    <span className={`font-medium ${getPerformanceColor(100 - realtimeMetrics.system.memory_usage)}`}>
                                        {realtimeMetrics?.system.memory_usage?.toFixed(1)}%
                                    </span>
                                </div>
                                <div className="flex justify-between">
                                    <span>Disk:</span>
                                    <span className={`font-medium ${getPerformanceColor(100 - realtimeMetrics.system.disk_usage)}`}>
                                        {realtimeMetrics?.system.disk_usage?.toFixed(1)}%
                                    </span>
                                </div>
                                <div className="flex justify-between">
                                    <span>Network I/O:</span>
                                    <span className="font-medium">{realtimeMetrics?.system?.network_io != null ? `${formatBytes(realtimeMetrics.system.network_io)}/s` : '-'}</span>
                                </div>
                            </div>
                        </div>

                        <div className="space-y-3">
                            <h3 className="font-semibold text-gray-900">🗃️ Database</h3>
                            <div className="space-y-2 text-sm">
                                <div className="flex justify-between">
                                    <span>Active Queries:</span>
                                    <span className="font-medium">{realtimeMetrics?.database?.active_queries != null ? realtimeMetrics.database.active_queries : '-'}</span>
                                </div>
                                <div className="flex justify-between">
                                    <span>Connections:</span>
                                    <span className="font-medium">{realtimeMetrics?.database?.connections != null ? realtimeMetrics.database.connections : '-'}</span>
                                </div>
                                <div className="flex justify-between">
                                    <span>Query Time:</span>
                                    <span className="font-medium">{realtimeMetrics?.database?.query_time != null ? `${realtimeMetrics.database.query_time.toFixed(2)}ms` : '-'}</span>
                                </div>
                            </div>
                        </div>

                        <div className="space-y-3">
                            <h3 className="font-semibold text-gray-900">⚡ Cache</h3>
                            <div className="space-y-2 text-sm">
                                <div className="flex justify-between">
                                    <span>Requests/sec:</span>
                                    <span className="font-medium">{realtimeMetrics?.cache?.requests_per_second != null ? realtimeMetrics.cache.requests_per_second : '-'}</span>
                                </div>
                                <div className="flex justify-between">
                                    <span>Hit Rate:</span>
                                    <span className={`font-medium ${getPerformanceColor(realtimeMetrics?.cache?.hit_rate)}`}>{realtimeMetrics?.cache?.hit_rate != null ? `${realtimeMetrics.cache.hit_rate.toFixed(1)}%` : '-'}</span>
                                </div>
                                <div className="flex justify-between">
                                    <span>Memory:</span>
                                    <span className="font-medium">{realtimeMetrics?.cache?.memory_usage != null ? formatBytes(realtimeMetrics.cache.memory_usage) : '-'}</span>
                                </div>
                            </div>
                        </div>

                        <div className="space-y-3">
                            <h3 className="font-semibold text-gray-900">🌍 API</h3>
                            <div className="space-y-2 text-sm">
                                <div className="flex justify-between">
                                    <span>Requests/sec:</span>
                                    <span className="font-medium">{realtimeMetrics?.api?.requests_per_second != null ? realtimeMetrics.api.requests_per_second : '-'}</span>
                                </div>
                                <div className="flex justify-between">
                                    <span>Active Connections:</span>
                                    <span className="font-medium">{realtimeMetrics?.api?.active_connections != null ? realtimeMetrics.api.active_connections : '-'}</span>
                                </div>
                                <div className="flex justify-between">
                                    <span>Response Time:</span>
                                    <span className="font-medium">{realtimeMetrics?.api?.response_time != null ? `${realtimeMetrics.api.response_time.toFixed(2)}ms` : '-'}</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Database Performance Details */}
            {dbPerformance && (
                <div className="bg-white rounded-lg shadow-md p-6">
                    <h2 className="text-xl font-bold text-gray-900 mb-4">🗄️ Database Performance Details</h2>
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div>
                            <h3 className="font-semibold text-gray-900 mb-3">Connection Pool</h3>
                            <div className="space-y-2 text-sm">
                                <div className="flex justify-between">
                                    <span>Active Connections:</span>
                                    <span className="font-medium">{dbPerformance.connection_pool.active_connections}</span>
                                </div>
                                <div className="flex justify-between">
                                    <span>Idle Connections:</span>
                                    <span className="font-medium">{dbPerformance.connection_pool.idle_connections}</span>
                                </div>
                                <div className="flex justify-between">
                                    <span>Total / Max:</span>
                                    <span className="font-medium">
                                        {dbPerformance.connection_pool.total_connections} / {dbPerformance.connection_pool.max_connections}
                                    </span>
                                </div>
                                <div className="flex justify-between">
                                    <span>Wait Time:</span>
                                    <span className="font-medium">{dbPerformance.connection_pool.connection_wait_time?.toFixed(2)}ms</span>
                                </div>
                            </div>
                        </div>

                        <div>
                            <h3 className="font-semibold text-gray-900 mb-3">Query Performance</h3>
                            <div className="space-y-2 text-sm">
                                <div className="flex justify-between">
                                    <span>Avg Query Time:</span>
                                    <span className="font-medium">{dbPerformance.query_performance?.avg_query_time?.toFixed(2)}ms</span>
                                </div>
                                <div className="flex justify-between">
                                    <span>Slow Queries:</span>
                                    <span className="font-medium">{dbPerformance.query_performance?.slow_queries_count}</span>
                                </div>
                                <div className="flex justify-between">
                                    <span>Queries/sec:</span>
                                    <span className="font-medium">{dbPerformance.query_performance?.queries_per_second?.toFixed(1)}</span>
                                </div>
                                <div className="flex justify-between">
                                    <span>Cache Hit Ratio:</span>
                                    <span className={`font-medium ${getPerformanceColor(dbPerformance?.query_performance?.cache_hit_ratio)}`}>{dbPerformance?.query_performance?.cache_hit_ratio != null ? `${dbPerformance.query_performance.cache_hit_ratio.toFixed(1)}%` : '-'}</span>
                                </div>
                            </div>
                        </div>
                    </div>

                    {dbPerformance.recommendations && dbPerformance.recommendations.length > 0 && (
                        <div className="mt-6">
                            <h3 className="font-semibold text-gray-900 mb-3">💡 Recommendations</h3>
                            <ul className="list-disc list-inside space-y-1 text-sm text-gray-700">
                                {dbPerformance.recommendations.map((rec, idx) => (
                                    <li key={idx}>{rec}</li>
                                ))}
                            </ul>
                        </div>
                    )}
                </div>
            )}

            {/* Cache Performance Details */}
            {cacheStats && (
                <div className="bg-white rounded-lg shadow-md p-6">
                    <h2 className="text-xl font-bold text-gray-900 mb-4">🚀 Cache Performance Details</h2>
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div>
                            <h3 className="font-semibold text-gray-900 mb-3">Memory Cache</h3>
                            <div className="space-y-2 text-sm">
                                <div className="flex justify-between">
                                    <span>Status:</span>
                                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(cacheStats.memory_cache?.status)}`}>{cacheStats.memory_cache?.status || '-'}</span>
                                </div>
                                <div className="flex justify-between">
                                    <span>Hit Rate:</span>
                                    <span className="font-medium">{cacheStats.memory_cache?.hit_rate != null ? `${cacheStats.memory_cache.hit_rate.toFixed(1)}%` : '-'}</span>
                                </div>
                                <div className="flex justify-between">
                                    <span>Total Requests:</span>
                                    <span className="font-medium">{cacheStats.memory_cache?.total_requests != null ? cacheStats.memory_cache.total_requests.toLocaleString() : '-'}</span>
                                </div>
                                <div className="flex justify-between">
                                    <span>Cache Size:</span>
                                    <span className="font-medium">{cacheStats.memory_cache?.cache_size != null && cacheStats.memory_cache?.max_size != null ? `${formatBytes(cacheStats.memory_cache.cache_size)} / ${formatBytes(cacheStats.memory_cache.max_size)}` : '-'}</span>
                                </div>
                                <div className="flex justify-between">
                                    <span>Evictions:</span>
                                    <span className="font-medium">{cacheStats.memory_cache?.eviction_count != null ? cacheStats.memory_cache.eviction_count : '-'}</span>
                                </div>
                            </div>
                        </div>
                        <div>
                            <h3 className="font-semibold text-gray-900 mb-3">Redis Cache</h3>
                            <div className="space-y-2 text-sm">
                                <div className="flex justify-between">
                                    <span>Status:</span>
                                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(cacheStats.redis_cache?.status)}`}>{cacheStats.redis_cache?.status || '-'}</span>
                                </div>
                                <div className="flex justify-between">
                                    <span>Hit Rate:</span>
                                    <span className="font-medium">{cacheStats.redis_cache?.hit_rate != null ? `${cacheStats.redis_cache.hit_rate.toFixed(1)}%` : '-'}</span>
                                </div>
                                <div className="flex justify-between">
                                    <span>Memory Usage:</span>
                                    <span className="font-medium">{cacheStats.redis_cache?.memory_usage_human || '-'}</span>
                                </div>
                                <div className="flex justify-between">
                                    <span>Connected Clients:</span>
                                    <span className="font-medium">{cacheStats.redis_cache?.connected_clients != null ? cacheStats.redis_cache.connected_clients : '-'}</span>
                                </div>
                                <div className="flex justify-between">
                                    <span>Commands Processed:</span>
                                    <span className="font-medium">{cacheStats.redis_cache?.total_commands_processed != null ? cacheStats.redis_cache.total_commands_processed.toLocaleString() : '-'}</span>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div className="mt-6">
                        <h3 className="font-semibold text-gray-900 mb-3">Performance Metrics</h3>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                            <div className="text-center">
                                <div className="text-2xl font-bold text-gray-900">{cacheStats.performance_metrics?.avg_response_time != null ? `${cacheStats.performance_metrics.avg_response_time.toFixed(2)}ms` : '-'}</div>
                                <div className="text-gray-600">Avg Response Time</div>
                            </div>
                            <div className="text-center">
                                <div className={`text-2xl font-bold ${getPerformanceColor(cacheStats.performance_metrics?.cache_efficiency)}`}>{cacheStats.performance_metrics?.cache_efficiency != null ? `${cacheStats.performance_metrics.cache_efficiency.toFixed(1)}%` : '-'}</div>
                                <div className="text-gray-600">Cache Efficiency</div>
                            </div>
                            <div className="text-center">
                                <div className={`text-2xl font-bold ${getPerformanceColor(cacheStats.performance_metrics?.memory_efficiency)}`}>{cacheStats.performance_metrics?.memory_efficiency != null ? `${cacheStats.performance_metrics.memory_efficiency.toFixed(1)}%` : '-'}</div>
                                <div className="text-gray-600">Memory Efficiency</div>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default AdvancedMonitoring;