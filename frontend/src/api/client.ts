import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000'; // Adjust if needed

export const apiClient = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

export const endpoints = {
    startSimulation: '/simulation/start',
    stopSimulation: (id: string) => `/simulation/${id}/stop`,
    getResults: (id: string) => `/simulation/${id}/results`,
    uploadMaterial: '/material/upload',
    getClasses: '/teacher/classes', // Mock or real endpoint for class list
    getClassesWithStudents: (teacherId: string) => `/teacher/${teacherId}/classes-with-students`,
    streamSimulation: (id: string) => `${API_BASE_URL}/simulation/${id}/stream`,

    // Downloads
    downloadHeatmap: (id: string) => `/heatmap/${id}`,
    downloadReport: (id: string, format: 'json' | 'pdf' = 'json') => `/report/${id}?format=${format}`,

    // Principal retry
    retryPrincipal: (id: string) => `/simulation/${id}/retry-principal`,

    // Dashboard & Analytics
    getSimulations: '/dashboard/simulations',
    getSimulationDetail: (id: string) => `/dashboard/simulation/${id}`,
    getAnalytics: '/dashboard/analytics',
};

// Generic request wrapper (optional, but good practice per user request)
export const apiRequest = async <T>(
    method: 'get' | 'post' | 'put' | 'delete',
    url: string,
    data?: any
): Promise<T> => {
    const response = await apiClient.request<T>({
        method,
        url,
        data,
    });
    return response.data;
};
