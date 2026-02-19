import React, { useState } from 'react';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ChunkAnalysis } from '@/types';
import { ChevronDown, ChevronUp, AlertCircle, MessageCircle } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

interface ChunkAnalysisComponentProps {
    chunk: ChunkAnalysis;
    index: number;
}

const ChunkAnalysisComponent: React.FC<ChunkAnalysisComponentProps> = ({ chunk, index }) => {
    const [isExpanded, setIsExpanded] = useState(false);

    return (
        <Card className="mb-4">
            <CardHeader className="py-4 cursor-pointer hover:bg-slate-50" onClick={() => setIsExpanded(!isExpanded)}>
                <div className="flex justify-between items-center">
                    <div className="flex items-center gap-4">
                        <div className="bg-slate-100 w-8 h-8 flex items-center justify-center rounded-full font-bold text-slate-600">
                            {index + 1}
                        </div>
                        <div>
                            <h4 className="font-semibold text-sm">Teacher Input</h4>
                            <p className="text-sm text-gray-600 truncate max-w-md">{chunk.teacherInput}</p>
                        </div>
                    </div>
                    <div className="flex items-center gap-4">
                        <Badge variant={chunk.effectivenessMetric > 70 ? "default" : chunk.effectivenessMetric > 40 ? "secondary" : "destructive"}>
                            Score: {chunk.effectivenessMetric}
                        </Badge>
                        <Button variant="ghost" size="sm">
                            {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                        </Button>
                    </div>
                </div>
            </CardHeader>
            {isExpanded && (
                <CardContent className="pt-0 pb-4 px-6 border-t bg-slate-50/50">
                    <div className="mt-4 grid grid-cols-1 lg:grid-cols-2 gap-6">
                        <div>
                            <h5 className="text-sm font-semibold mb-2 flex items-center gap-2">
                                <MessageCircle className="w-4 h-4" /> Student Responses
                            </h5>
                            <div className="space-y-3">
                                {chunk.studentResponses.map((resp, idx) => (
                                    <div key={idx} className="bg-white p-3 rounded border text-sm">
                                        <div className="flex justify-between mb-1">
                                            <span className="font-medium text-xs">{resp.studentName}</span>
                                            <span className={`text-xs px-2 py-0.5 rounded-full ${resp.sentiment === 'positive' ? 'bg-green-100 text-green-700' :
                                                resp.sentiment === 'negative' ? 'bg-red-100 text-red-700' : 'bg-gray-100 text-gray-700'
                                                }`}>
                                                {resp.sentiment}
                                            </span>
                                        </div>
                                        <p className="text-gray-700">{resp.response}</p>
                                    </div>
                                ))}
                            </div>
                        </div>

                        <div>
                            <h5 className="text-sm font-semibold mb-2 flex items-center gap-2">
                                <AlertCircle className="w-4 h-4" /> Gaps Identified
                            </h5>
                            {chunk.gapsIdentified.length > 0 ? (
                                <div className="flex flex-wrap gap-2">
                                    {chunk.gapsIdentified.map((gap, idx) => (
                                        <Badge key={idx} variant="outline" className="bg-orange-50 text-orange-700 border-orange-200">
                                            {gap}
                                        </Badge>
                                    ))}
                                </div>
                            ) : (
                                <p className="text-sm text-gray-500 italic">No specific gaps identified in this chunk.</p>
                            )}

                            <div className="mt-6">
                                <h5 className="text-sm font-semibold mb-2">Full Teacher Input</h5>
                                <p className="text-sm text-gray-700 bg-white p-3 rounded border">
                                    {chunk.teacherInput}
                                </p>
                            </div>
                        </div>
                    </div>
                </CardContent>
            )}
        </Card>
    );
};

export default ChunkAnalysisComponent;
