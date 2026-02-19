import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ChunkAnalysis } from '@/types';

interface EffectivenessChartProps {
    data: ChunkAnalysis[];
}

const EffectivenessChart: React.FC<EffectivenessChartProps> = ({ data }) => {
    const chartData = data.map((chunk, index) => ({
        name: `Chunk ${index + 1}`,
        score: chunk.effectivenessMetric,
        timestamp: new Date(chunk.timestamp).toLocaleTimeString(),
    }));

    return (
        <Card>
            <CardHeader>
                <CardTitle>Effectiveness Trend (IRF R+)</CardTitle>
            </CardHeader>
            <CardContent className="h-[300px]">
                <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={chartData}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="name" />
                        <YAxis domain={[0, 100]} />
                        <Tooltip />
                        <Legend />
                        <Line type="monotone" dataKey="score" stroke="#8884d8" name="Effectiveness Score" strokeWidth={2} />
                    </LineChart>
                </ResponsiveContainer>
            </CardContent>
        </Card>
    );
};

export default EffectivenessChart;
