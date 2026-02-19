import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { useNavigate, useLocation } from 'react-router-dom';
import SimulationCard from '@/components/dashboard/SimulationCard';
import { Simulation, AnalyticsData } from '@/types';
import { Plus, BarChart2, Loader2 } from 'lucide-react';

interface SimulationListItem {
    id: string;
    topic: string;
    timestamp: string;
    status: string;
    student_count: number;
    average_understanding: number;
    effectiveness_score: number;
}

interface AnalyticsApiResponse {
    total_simulations: number;
    total_time_spent: number;
    average_effectiveness: number;
    common_gaps: { gap: string; count: number }[];
    improvement_trend: { date: string; score: number }[];
}

interface LocationState {
    teacherId?: string;
    teacherName?: string;
}

const Dashboard: React.FC = () => {
    const navigate = useNavigate();
    const location = useLocation();
    const state = location.state as LocationState | null;

    // Get teacher info from navigation state or localStorage
    const getTeacherInfo = () => {
        if (state?.teacherId) {
            return { teacherId: state.teacherId, teacherName: state.teacherName };
        }
        const stored = localStorage.getItem('currentTeacher');
        if (stored) {
            try {
                const parsed = JSON.parse(stored);
                return { teacherId: parsed.teacher_id, teacherName: parsed.name };
            } catch {
                return { teacherId: undefined, teacherName: undefined };
            }
        }
        return { teacherId: undefined, teacherName: undefined };
    };

    const { teacherId, teacherName } = getTeacherInfo();

    const [simulations, setSimulations] = useState<Simulation[]>([]);
    const [stats, setStats] = useState<AnalyticsData | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchData = async () => {
            setLoading(true);
            setError(null);

            try {
                // Build query params
                const params = teacherId ? `?teacher_id=${teacherId}` : '';

                // Fetch simulations
                const simsRes = await fetch(`http://localhost:8000/dashboard/simulations${params}`);
                if (!simsRes.ok) throw new Error('Failed to fetch simulations');
                const simsData: SimulationListItem[] = await simsRes.json();

                // Transform to frontend format
                const transformedSims: Simulation[] = simsData.map(sim => ({
                    id: sim.id,
                    topic: sim.topic,
                    timestamp: sim.timestamp,
                    durationSeconds: 0, // Not tracked yet
                    studentCount: sim.student_count,
                    averageUnderstanding: sim.average_understanding,
                    status: sim.status as 'completed' | 'in_progress' | 'failed',
                    effectivenessScore: sim.effectiveness_score,
                }));
                setSimulations(transformedSims);

                // Fetch analytics
                const analyticsRes = await fetch(`http://localhost:8000/dashboard/analytics${params}`);
                if (!analyticsRes.ok) throw new Error('Failed to fetch analytics');
                const analyticsData: AnalyticsApiResponse = await analyticsRes.json();

                // Transform to frontend format
                const transformedStats: AnalyticsData = {
                    totalSimulations: analyticsData.total_simulations,
                    totalTimeSpent: analyticsData.total_time_spent,
                    averageEffectiveness: analyticsData.average_effectiveness,
                    commonGaps: analyticsData.common_gaps,
                    improvementTrend: analyticsData.improvement_trend.map(t => ({
                        date: t.date,
                        score: t.score,
                    })),
                };
                setStats(transformedStats);

            } catch (err: any) {
                console.error("Failed to fetch dashboard data", err);
                setError(err.message || 'Failed to load data');
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, [teacherId]);

    if (loading) {
        return (
            <div className="container mx-auto py-8 flex justify-center items-center min-h-[400px]">
                <Loader2 className="w-8 h-8 animate-spin text-primary" />
            </div>
        );
    }

    return (
        <div className="container mx-auto py-8">
            <div className="flex justify-between items-center mb-8">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight">
                        {teacherName ? `${teacherName}'s Dashboard` : 'Teacher Dashboard'}
                    </h1>
                    <p className="text-gray-500 mt-2">Manage your simulations and track student progress.</p>
                </div>
                <div className="flex gap-4">
                    <Button variant="outline" onClick={() => navigate('/analytics')}>
                        <BarChart2 className="mr-2 w-4 h-4" /> Analytics
                    </Button>
                    <Button onClick={() => navigate('/setup')}>
                        <Plus className="mr-2 w-4 h-4" /> New Simulation
                    </Button>
                </div>
            </div>

            {error && (
                <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-6">
                    {error}
                </div>
            )}

            {/* Quick Stats Row */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Total Runs</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{stats?.totalSimulations || 0}</div>
                        <p className="text-xs text-muted-foreground">Lifetime simulations</p>
                    </CardContent>
                </Card>
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Avg Effectiveness</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{stats?.averageEffectiveness || 0}%</div>
                        <p className="text-xs text-muted-foreground">Across all topics</p>
                    </CardContent>
                </Card>
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Common Gap</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold truncate">
                            {stats?.commonGaps[0]?.gap || "None"}
                        </div>
                        <p className="text-xs text-muted-foreground">Most frequent issue</p>
                    </CardContent>
                </Card>
            </div>

            <h2 className="text-xl font-semibold mb-4">Recent Simulations</h2>
            {simulations.length === 0 ? (
                <Card className="p-8 text-center">
                    <p className="text-muted-foreground">No simulations yet.</p>
                    <Button className="mt-4" onClick={() => navigate('/setup')}>
                        <Plus className="mr-2 w-4 h-4" /> Create Your First Simulation
                    </Button>
                </Card>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {simulations.map(sim => (
                        <SimulationCard key={sim.id} simulation={sim} />
                    ))}
                </div>
            )}
        </div>
    );
};

export default Dashboard;
