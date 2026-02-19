import React from 'react';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Simulation } from '@/types';
import { useNavigate } from 'react-router-dom';
import { Clock, Users, Activity } from 'lucide-react';

interface SimulationCardProps {
    simulation: Simulation;
}

const SimulationCard: React.FC<SimulationCardProps> = ({ simulation }) => {
    const navigate = useNavigate();

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'completed': return 'default'; // primary
            case 'in_progress': return 'secondary';
            case 'failed': return 'destructive';
            default: return 'outline';
        }
    };

    return (
        <Card className="hover:shadow-lg transition-shadow cursor-pointer" onClick={() => navigate(`/simulation/${simulation.id}/detail`)}>
            <CardHeader>
                <div className="flex justify-between items-start">
                    <div>
                        <CardTitle>{simulation.topic}</CardTitle>
                        <CardDescription>{new Date(simulation.timestamp).toLocaleDateString()}</CardDescription>
                    </div>
                    <Badge variant={getStatusColor(simulation.status)}>{simulation.status}</Badge>
                </div>
            </CardHeader>
            <CardContent>
                <div className="flex justify-between text-sm text-gray-500">
                    <div className="flex items-center gap-1">
                        <Clock className="w-4 h-4" />
                        <span>{Math.floor(simulation.durationSeconds / 60)} min</span>
                    </div>
                    <div className="flex items-center gap-1">
                        <Users className="w-4 h-4" />
                        <span>{simulation.studentCount} Students</span>
                    </div>
                    <div className="flex items-center gap-1">
                        <Activity className="w-4 h-4" />
                        <span>{Math.round(simulation.averageUnderstanding)}% Avg. Und.</span>
                    </div>
                </div>
            </CardContent>
            <CardFooter>
                <Button className="w-full" variant="outline">View Analysis</Button>
            </CardFooter>
        </Card>
    );
};

export default SimulationCard;
