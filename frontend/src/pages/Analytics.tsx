import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Loader2 } from 'lucide-react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, LineChart, Line } from 'recharts';

interface AnalyticsApiResponse {
    total_simulations: number;
    total_time_spent: number;
    average_effectiveness: number;
    common_gaps: { gap: string; count: number }[];
    improvement_trend: { date: string; score: number }[];
}

const Analytics: React.FC = () => {
    const navigate = useNavigate();
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [data, setData] = useState<AnalyticsApiResponse | null>(null);

    useEffect(() => {
        const fetchAnalytics = async () => {
            setLoading(true);
            setError(null);

            try {
                // Get teacher ID from localStorage if available
                let teacherId: string | undefined;
                const stored = localStorage.getItem('currentTeacher');
                if (stored) {
                    try {
                        const parsed = JSON.parse(stored);
                        teacherId = parsed.teacher_id;
                    } catch { }
                }

                const params = teacherId ? `?teacher_id=${teacherId}` : '';
                const response = await fetch(`http://localhost:8000/dashboard/analytics${params}`);

                if (!response.ok) {
                    throw new Error('Failed to fetch analytics');
                }

                const analyticsData: AnalyticsApiResponse = await response.json();
                setData(analyticsData);
            } catch (err: any) {
                console.error("Failed to fetch analytics", err);
                setError(err.message || 'Failed to load analytics');
            } finally {
                setLoading(false);
            }
        };

        fetchAnalytics();
    }, []);

    if (loading) {
        return (
            <div className="container mx-auto py-8 flex justify-center items-center min-h-[400px]">
                <Loader2 className="w-8 h-8 animate-spin text-primary" />
            </div>
        );
    }

    const hasData = data && (data.total_simulations > 0 || data.common_gaps.length > 0);

    return (
        <div className="container mx-auto py-8">
            <Button variant="ghost" className="mb-4" onClick={() => navigate('/dashboard')}>
                <ArrowLeft className="mr-2 w-4 h-4" /> Back to Dashboard
            </Button>
            <h1 className="text-3xl font-bold mb-8">Performance Analytics</h1>

            {error && (
                <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-6">
                    {error}
                </div>
            )}

            {!hasData ? (
                <Card className="p-8 text-center">
                    <p className="text-muted-foreground">No analytics data yet.</p>
                    <p className="text-sm text-muted-foreground mt-2">
                        Run some simulations to see analytics here.
                    </p>
                    <Button className="mt-4" onClick={() => navigate('/setup')}>
                        Create a Simulation
                    </Button>
                </Card>
            ) : (
                <>
                    {/* Summary Cards */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                        <Card>
                            <CardHeader className="pb-2">
                                <CardTitle className="text-sm font-medium">Total Simulations</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <div className="text-3xl font-bold">{data.total_simulations}</div>
                            </CardContent>
                        </Card>
                        <Card>
                            <CardHeader className="pb-2">
                                <CardTitle className="text-sm font-medium">Time Invested</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <div className="text-3xl font-bold">{data.total_time_spent} min</div>
                            </CardContent>
                        </Card>
                        <Card>
                            <CardHeader className="pb-2">
                                <CardTitle className="text-sm font-medium">Avg Effectiveness</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <div className="text-3xl font-bold">{data.average_effectiveness}%</div>
                            </CardContent>
                        </Card>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                        {/* Improvement Trend */}
                        <Card>
                            <CardHeader>
                                <CardTitle>Effectiveness Trend</CardTitle>
                            </CardHeader>
                            <CardContent className="h-[300px]">
                                {data.improvement_trend.length > 0 ? (
                                    <ResponsiveContainer width="100%" height="100%">
                                        <LineChart data={data.improvement_trend}>
                                            <CartesianGrid strokeDasharray="3 3" />
                                            <XAxis dataKey="date" />
                                            <YAxis domain={[0, 100]} />
                                            <Tooltip />
                                            <Legend />
                                            <Line
                                                type="monotone"
                                                dataKey="score"
                                                stroke="#82ca9d"
                                                name="Effectiveness Score"
                                                strokeWidth={2}
                                            />
                                        </LineChart>
                                    </ResponsiveContainer>
                                ) : (
                                    <div className="h-full flex items-center justify-center text-muted-foreground">
                                        No trend data available yet
                                    </div>
                                )}
                            </CardContent>
                        </Card>

                        {/* Common Gaps */}
                        <Card>
                            <CardHeader>
                                <CardTitle>Common Teaching Gaps</CardTitle>
                            </CardHeader>
                            <CardContent className="h-[300px]">
                                {data.common_gaps.length > 0 ? (
                                    <ResponsiveContainer width="100%" height="100%">
                                        <BarChart layout="vertical" data={data.common_gaps}>
                                            <CartesianGrid strokeDasharray="3 3" />
                                            <XAxis type="number" />
                                            <YAxis dataKey="gap" type="category" width={120} />
                                            <Tooltip />
                                            <Bar dataKey="count" fill="#8884d8" name="Frequency" />
                                        </BarChart>
                                    </ResponsiveContainer>
                                ) : (
                                    <div className="h-full flex items-center justify-center text-muted-foreground">
                                        No gaps identified yet
                                    </div>
                                )}
                            </CardContent>
                        </Card>
                    </div>
                </>
            )}
        </div>
    );
};

export default Analytics;
