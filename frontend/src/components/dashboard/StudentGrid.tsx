import React from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { StudentState } from '@/types';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';

interface StudentGridProps {
    students: StudentState[];
}

const StudentGrid: React.FC<StudentGridProps> = ({ students }) => {
    // Helper to find dominant personality trait
    const getDominantTrait = (p: StudentState['personality']) => {
        const traits = Object.entries(p);
        return traits.reduce((a, b) => (a[1] > b[1] ? a : b))[0];
    };

    return (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {students.map((student) => {
                const domTrait = getDominantTrait(student.personality);
                return (
                    <Card key={student.id} className="overflow-hidden hover:shadow-md transition-shadow">
                        <CardContent className="p-6">
                            <div className="flex items-start justify-between mb-6">
                                <div className="flex items-center gap-4">
                                    <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center text-lg font-bold text-primary">
                                        {student.name.charAt(0)}
                                    </div>
                                    <div>
                                        <h4 className="font-bold text-lg">{student.name}</h4>
                                        <div className="flex items-center gap-2 text-sm text-muted-foreground">
                                            <span>Doubts: {student.doubtsAsked}</span>
                                            <span>•</span>
                                            <span className="capitalize">{domTrait}</span>
                                        </div>
                                    </div>
                                </div>
                                {/* Badge for Understanding Level */}
                                <Badge variant={student.currentUnderstanding >= 80 ? "default" : student.currentUnderstanding >= 50 ? "secondary" : "destructive"} className="text-xs px-2 py-1">
                                    {student.currentUnderstanding >= 80 ? "Mastered" : student.currentUnderstanding >= 50 ? "Learning" : "Struggling"}
                                </Badge>
                            </div>

                            <div className="space-y-4">
                                <div>
                                    <div className="flex justify-between text-sm mb-2">
                                        <span className="text-muted-foreground">Understanding Progress</span>
                                        <span className="font-bold">{Math.round(student.currentUnderstanding)}%</span>
                                    </div>
                                    <Progress value={student.currentUnderstanding} className="h-3 rounded-full" />
                                </div>

                                <div className="grid grid-cols-2 gap-4 pt-2">
                                    <div className="bg-slate-50 p-3 rounded-lg text-center">
                                        <div className="text-xs text-muted-foreground uppercase tracking-wider mb-1">Initial</div>
                                        <div className="font-semibold">{Math.round(student.initialUnderstanding)}%</div>
                                    </div>
                                    <div className="bg-slate-50 p-3 rounded-lg text-center">
                                        <div className="text-xs text-muted-foreground uppercase tracking-wider mb-1">Improvement</div>
                                        <div className={`font-semibold ${student.currentUnderstanding >= student.initialUnderstanding ? 'text-green-600' : 'text-red-600'}`}>
                                            {student.currentUnderstanding >= student.initialUnderstanding ? '+' : ''}
                                            {Math.round(student.currentUnderstanding - student.initialUnderstanding)}%
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                );
            })}
        </div>
    );
};

export default StudentGrid;
