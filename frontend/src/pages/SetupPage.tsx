import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Slider } from '@/components/ui/slider';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Loader2, AlertTriangle } from 'lucide-react';
import { apiClient, endpoints } from '@/api/client';

interface ClassWithStudents {
    name: string;
    student_count: number;
}

interface Teacher {
    teacher_id: string;
    name: string;
    big5_scores?: Record<string, any>;
}

export default function SetupPage() {
    const navigate = useNavigate();
    const [classes, setClasses] = useState<ClassWithStudents[]>([]);
    const [selectedClass, setSelectedClass] = useState<string>('');
    const [numRuns, setNumRuns] = useState<number[]>([3]);
    const [file, setFile] = useState<File | null>(null);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [loadingClasses, setLoadingClasses] = useState(false);
    const [teacher, setTeacher] = useState<Teacher | null>(null);
    const [error, setError] = useState<string | null>(null);

    // Get selected class info
    const selectedClassInfo = classes.find(c => c.name === selectedClass);
    const hasNoStudents = selectedClassInfo && selectedClassInfo.student_count === 0;

    // Fetch teacher from localStorage
    useEffect(() => {
        const storedTeacher = localStorage.getItem('currentTeacher');
        if (storedTeacher) {
            try {
                const parsed = JSON.parse(storedTeacher);
                setTeacher(parsed);
            } catch (e) {
                console.error('Failed to parse teacher from localStorage', e);
            }
        }
    }, []);

    // Fetch teacher's classes with student counts when teacher is available
    useEffect(() => {
        if (!teacher?.teacher_id) return;

        setLoadingClasses(true);
        apiClient.get(endpoints.getClassesWithStudents(teacher.teacher_id))
            .then(res => {
                setClasses(res.data);
            })
            .catch(err => {
                console.error('Failed to load classes', err);
                setClasses([]);
            })
            .finally(() => setLoadingClasses(false));
    }, [teacher?.teacher_id]);

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            setFile(e.target.files[0]);
            setError(null);
        }
    };

    const handleStart = async () => {
        if (!selectedClass || !file || !teacher) return;

        // Check for students
        if (hasNoStudents) {
            setError(`No students found in "${selectedClass}". Students must complete the Big5 assessment before running a simulation.`);
            return;
        }

        setIsSubmitting(true);
        setError(null);

        try {
            // 1. Upload Material
            const formData = new FormData();
            formData.append('file', file);
            const uploadRes = await apiClient.post(endpoints.uploadMaterial, formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });
            const materialFilePath = uploadRes.data.file_path;

            // 2. Start Simulation
            const simulationRequest = {
                class_name: selectedClass,
                teacher_id: teacher.teacher_id,
                teacher_name: teacher.name,
                teacher_personality: "Professional and encouraging teaching style", // Default
                teacher_big5: teacher.big5_scores || {},
                material_file_path: materialFilePath,
                professor_name: teacher.name,
                num_runs: numRuns[0],
                model_provider: "lightning",
                model_name: "lightning-ai/gpt-oss-120b"
            };

            const res = await apiClient.post(endpoints.startSimulation, simulationRequest);
            const simulationId = res.data.simulation_id;

            navigate(`/simulation/${simulationId}`);
        } catch (err: any) {
            console.error("Failed to start simulation", err);
            const message = err.response?.data?.detail || "Failed to start simulation. Please try again.";
            setError(message);
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <div className="flex items-center justify-center min-h-[80vh]">
            <Card className="w-full max-w-lg">
                <CardHeader>
                    <CardTitle>Start New Simulation</CardTitle>
                    <CardDescription>
                        Configure the classroom environment and upload teaching material.
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">

                    <div className="space-y-2">
                        <Label htmlFor="class-select">Select Class</Label>
                        <Select onValueChange={(value) => { setSelectedClass(value); setError(null); }} value={selectedClass}>
                            <SelectTrigger id="class-select">
                                <SelectValue placeholder="Choose a class..." />
                            </SelectTrigger>
                            <SelectContent>
                                {loadingClasses ? (
                                    <div className="flex justify-center p-2">
                                        <Loader2 className="w-4 h-4 animate-spin text-muted-foreground" />
                                    </div>
                                ) : classes.length === 0 ? (
                                    <div className="p-2 text-center text-muted-foreground text-sm">
                                        No classes available
                                    </div>
                                ) : (
                                    classes.map((cls) => (
                                        <SelectItem key={cls.name} value={cls.name}>
                                            {cls.name} ({cls.student_count} student{cls.student_count !== 1 ? 's' : ''})
                                        </SelectItem>
                                    ))
                                )}
                            </SelectContent>
                        </Select>
                        {hasNoStudents && (
                            <div className="flex items-center gap-2 text-amber-600 text-sm mt-2">
                                <AlertTriangle className="w-4 h-4" />
                                <span>This class has no students. Students must take the Big5 assessment first.</span>
                            </div>
                        )}
                    </div>

                    <div className="space-y-2">
                        <Label htmlFor="material-upload">Upload Material (PDF, PPTX, DOCX)</Label>
                        <div className="border-2 border-dashed border-neutral-300 rounded-lg p-6 flex flex-col items-center justify-center bg-neutral-50 hover:bg-neutral-100 transition-colors">
                            <Input
                                id="material-upload"
                                type="file"
                                accept=".pdf,.pptx,.docx"
                                onChange={handleFileChange}
                                className="cursor-pointer"
                            />
                            <p className="text-xs text-neutral-500 mt-2">
                                {file ? `Selected: ${file.name}` : "Drag & drop or click to upload"}
                            </p>
                        </div>
                    </div>

                    <div className="space-y-2">
                        <div className="flex justify-between">
                            <Label>Number of Runs</Label>
                            <span className="text-sm font-medium text-neutral-500">{numRuns[0]} Runs</span>
                        </div>
                        <Slider
                            value={numRuns}
                            onValueChange={setNumRuns}
                            min={1}
                            max={10}
                            step={1}
                            className="py-4"
                        />
                        <p className="text-xs text-neutral-500">
                            More runs provide better statistical confidence but take longer.
                        </p>
                    </div>

                    {error && (
                        <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                            {error}
                        </div>
                    )}

                </CardContent>
                <CardFooter>
                    <Button
                        className="w-full"
                        onClick={handleStart}
                        disabled={!selectedClass || !file || isSubmitting || hasNoStudents}
                    >
                        {isSubmitting ? (
                            <>
                                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                Starting...
                            </>
                        ) : (
                            "Start Simulation"
                        )}
                    </Button>
                </CardFooter>
            </Card>
        </div>
    );
}
