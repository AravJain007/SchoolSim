
export interface Simulation {
    id: string;
    timestamp: string; // ISO date string
    topic: string;
    durationSeconds: number;
    studentCount: number;
    averageUnderstanding: number;
    status: 'completed' | 'in_progress' | 'failed';
    effectivenessScore: number;
}

export interface ChunkAnalysis {
    id: string; // chunk id
    timestamp: string;
    teacherInput: string;
    studentResponses: {
        studentName: string;
        response: string;
        sentiment: 'positive' | 'neutral' | 'negative';
        understanding: number; // 0-100
    }[];
    gapsIdentified: string[];
    effectivenessMetric: number; // IRF R+
}

export interface StudentState {
    id: string;
    name: string;
    initialUnderstanding: number;
    currentUnderstanding: number;
    doubtsAsked: number;
    personality: {
        openness: number;
        conscientiousness: number;
        extraversion: number;
        agreeableness: number;
        neuroticism: number;
    };
}

export interface AnalyticsData {
    totalSimulations: number;
    totalTimeSpent: number; // minutes
    averageEffectiveness: number;
    commonGaps: { gap: string; count: number }[];
    improvementTrend: { date: string; score: number }[];
}

export interface SimulationDetail extends Simulation {
    chunks: ChunkAnalysis[];
    students: StudentState[];
    principalAnalysis: string;
}
