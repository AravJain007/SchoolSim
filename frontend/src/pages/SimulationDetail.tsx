import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { ArrowLeft, AlertTriangle, CheckCircle, Loader2, ChevronDown } from 'lucide-react';
import {
    ResponsiveContainer,
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
} from 'recharts';
import {
    Collapsible,
    CollapsibleTrigger,
    CollapsibleContent,
} from '@/components/ui/collapsible';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface SimulationDetailApiResponse {
    id: string;
    topic: string;
    timestamp: string;
    status: string;
    total_runs: number;
    student_count: number;
    per_chunk_understanding: Record<string, number>;
    gap_chunks: string[];
    common_doubts: Record<string, string[]>;
    principal_notes: string[];
}

const formatChunkLabel = (chunkId: string): string =>
    chunkId.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());

const getStatusVariant = (status: string): 'default' | 'secondary' | 'destructive' | 'outline' => {
    switch (status) {
        case 'completed': return 'default';
        case 'in_progress':
        case 'running': return 'secondary';
        case 'failed': return 'destructive';
        default: return 'outline';
    }
};

const SimulationDetailPage: React.FC = () => {
    const { id } = useParams<{ id: string }>();
    const navigate = useNavigate();
    const [detail, setDetail] = useState<SimulationDetailApiResponse | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (!id) return;
        setLoading(true);
        setError(null);

        fetch(`http://localhost:8000/dashboard/simulation/${id}`)
            .then((res) => {
                if (!res.ok) throw new Error(`Failed to load simulation (${res.status})`);
                return res.json() as Promise<SimulationDetailApiResponse>;
            })
            .then((data) => setDetail(data))
            .catch((err) => setError(err.message || 'Failed to load simulation details'))
            .finally(() => setLoading(false));
    }, [id]);

    if (loading) {
        return (
            <div className="container mx-auto py-8 flex justify-center items-center min-h-[400px]">
                <Loader2 className="w-8 h-8 animate-spin text-primary" />
            </div>
        );
    }

    if (error) {
        return (
            <div className="container mx-auto py-8">
                <Button variant="ghost" className="mb-4" onClick={() => navigate('/dashboard')}>
                    <ArrowLeft className="mr-2 w-4 h-4" /> Back to Dashboard
                </Button>
                <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
                    {error}
                </div>
            </div>
        );
    }

    if (!detail) {
        return (
            <div className="container mx-auto py-8">
                <Button variant="ghost" className="mb-4" onClick={() => navigate('/dashboard')}>
                    <ArrowLeft className="mr-2 w-4 h-4" /> Back to Dashboard
                </Button>
                <p className="text-muted-foreground">Simulation not found.</p>
            </div>
        );
    }

    // Build bar chart data from per_chunk_understanding
    const chunkChartData = Object.entries(detail.per_chunk_understanding).map(
        ([chunkId, score]) => ({
            name: formatChunkLabel(chunkId),
            score: parseFloat(score.toFixed(2)),
            isGap: detail.gap_chunks.includes(chunkId),
        })
    );

    const avgUnderstanding =
        chunkChartData.length > 0
            ? chunkChartData.reduce((sum, c) => sum + c.score, 0) / chunkChartData.length
            : null;

    const commonDoubtEntries = Object.entries(detail.common_doubts);

    return (
        <div className="container mx-auto py-8">
            <Button variant="ghost" className="mb-4" onClick={() => navigate('/dashboard')}>
                <ArrowLeft className="mr-2 w-4 h-4" /> Back to Dashboard
            </Button>

            {/* Header */}
            <div className="flex justify-between items-start mb-6">
                <div>
                    <h1 className="text-3xl font-bold">{detail.topic}</h1>
                    <p className="text-gray-500 mt-1">
                        {detail.timestamp
                            ? new Date(detail.timestamp).toLocaleString()
                            : 'No date available'}
                    </p>
                </div>
                <Badge variant={getStatusVariant(detail.status)} className="text-sm px-3 py-1">
                    {detail.status}
                </Badge>
            </div>

            {/* Summary stats */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                <Card>
                    <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-medium text-muted-foreground">Total Runs</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-3xl font-bold">{detail.total_runs}</div>
                    </CardContent>
                </Card>
                <Card>
                    <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-medium text-muted-foreground">Avg. Understanding</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-3xl font-bold">
                            {avgUnderstanding !== null ? `${avgUnderstanding.toFixed(2)}/5` : '—'}
                        </div>
                    </CardContent>
                </Card>
                <Card>
                    <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-medium text-muted-foreground">Gaps Detected</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-3xl font-bold text-amber-600">{detail.gap_chunks.length}</div>
                    </CardContent>
                </Card>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
                {/* Per-chunk understanding chart */}
                <Card className="lg:col-span-2">
                    <CardHeader>
                        <CardTitle>Understanding by Chunk</CardTitle>
                        <CardDescription>Average student understanding score (out of 5) per topic chunk</CardDescription>
                    </CardHeader>
                    <CardContent className="h-[300px]">
                        {chunkChartData.length > 0 ? (
                            <ResponsiveContainer width="100%" height="100%">
                                <BarChart data={chunkChartData} margin={{ top: 5, right: 20, bottom: 60, left: 0 }}>
                                    <CartesianGrid strokeDasharray="3 3" />
                                    <XAxis
                                        dataKey="name"
                                        angle={-35}
                                        textAnchor="end"
                                        tick={{ fontSize: 12 }}
                                        interval={0}
                                    />
                                    <YAxis domain={[0, 5]} />
                                    <Tooltip formatter={(value: number) => [`${value}/5`, 'Avg. Understanding']} />
                                    <Bar
                                        dataKey="score"
                                        name="Avg. Understanding"
                                        fill="#6366f1"
                                        radius={[4, 4, 0, 0]}
                                    />
                                </BarChart>
                            </ResponsiveContainer>
                        ) : (
                            <div className="h-full flex items-center justify-center text-muted-foreground">
                                No chunk understanding data available
                            </div>
                        )}
                    </CardContent>
                </Card>

                {/* Gap chunks */}
                <Card>
                    <CardHeader>
                        <CardTitle>Teaching Gaps</CardTitle>
                        <CardDescription>Chunks where students consistently struggled</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-3">
                            {detail.gap_chunks.length > 0 ? (
                                detail.gap_chunks.map((chunkId) => (
                                    <div
                                        key={chunkId}
                                        className="flex items-start gap-3 p-3 border border-amber-100 bg-amber-50/50 rounded-lg"
                                    >
                                        <AlertTriangle className="h-5 w-5 text-amber-600 mt-0.5 shrink-0" />
                                        <span className="text-sm font-medium text-neutral-800">
                                            {formatChunkLabel(chunkId)}
                                        </span>
                                    </div>
                                ))
                            ) : (
                                <div className="flex items-center gap-2 p-3 border border-green-100 bg-green-50/50 rounded-lg text-green-700 text-sm">
                                    <CheckCircle className="h-5 w-5 shrink-0" />
                                    No teaching gaps detected
                                </div>
                            )}
                        </div>
                    </CardContent>
                </Card>

                {/* Common Doubts */}
                <Card>
                    <CardHeader>
                        <CardTitle>Common Student Doubts</CardTitle>
                        <CardDescription>Recurring questions across simulation runs</CardDescription>
                    </CardHeader>
                    <CardContent>
                        {commonDoubtEntries.length > 0 ? (
                            <div className="divide-y divide-neutral-100">
                                {commonDoubtEntries.map(([chunkId, doubts], i) => (
                                    <Collapsible key={i}>
                                        <CollapsibleTrigger className="flex w-full items-center justify-between py-3 text-left group">
                                            <div className="flex items-center gap-3">
                                                <Badge variant="outline" className="text-xs shrink-0">
                                                    {doubts.length}
                                                </Badge>
                                                <span className="font-medium text-sm text-neutral-800">
                                                    {formatChunkLabel(chunkId)}
                                                </span>
                                            </div>
                                            <ChevronDown className="h-4 w-4 text-neutral-400 shrink-0 transition-transform duration-200 group-data-[state=open]:rotate-180" />
                                        </CollapsibleTrigger>
                                        <CollapsibleContent className="pb-3">
                                            <ul className="space-y-2 pl-1">
                                                {doubts.map((doubt, j) => (
                                                    <li
                                                        key={j}
                                                        className="text-sm text-neutral-600 border-l-2 border-neutral-200 pl-3 py-0.5"
                                                    >
                                                        {doubt}
                                                    </li>
                                                ))}
                                            </ul>
                                        </CollapsibleContent>
                                    </Collapsible>
                                ))}
                            </div>
                        ) : (
                            <p className="text-sm text-muted-foreground">No common doubts recorded.</p>
                        )}
                    </CardContent>
                </Card>
            </div>

            {/* Principal Notes */}
            {detail.principal_notes.length > 0 && (
                <Card>
                    <CardHeader>
                        <CardTitle>Principal's Observations</CardTitle>
                        <CardDescription>Pedagogical analysis from the KLI framework</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <ScrollArea className="h-[300px] w-full rounded-md border p-4">
                            <div className="space-y-4">
                                {detail.principal_notes.map((note, i) => (
                                    <div
                                        key={i}
                                        className="text-sm text-neutral-700 border-l-2 border-neutral-300 pl-3 prose prose-sm prose-neutral max-w-none"
                                    >
                                        <ReactMarkdown remarkPlugins={[remarkGfm]}>{note}</ReactMarkdown>
                                    </div>
                                ))}
                            </div>
                        </ScrollArea>
                    </CardContent>
                </Card>
            )}
        </div>
    );
};

export default SimulationDetailPage;
