import { useState, useEffect } from 'react';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Loader2 } from "lucide-react";
import { UserDetails } from '../StudentBig5Page';

interface Teacher {
    teacher_id: string;
    name: string;
}

interface IntroStepProps {
    onStart: (details: UserDetails) => void;
    isTeacher?: boolean;
    teacherId?: string;
    teacherName?: string;
}

export default function IntroStep({ onStart, isTeacher, teacherId, teacherName }: IntroStepProps) {
    const [name, setName] = useState('');
    const [collegeId, setCollegeId] = useState('');
    const [selectedTeacherId, setSelectedTeacherId] = useState('');
    const [classLocation, setClassLocation] = useState('');
    const [error, setError] = useState('');

    // API-driven data
    const [teachers, setTeachers] = useState<Teacher[]>([]);
    const [classes, setClasses] = useState<string[]>([]);
    const [loadingTeachers, setLoadingTeachers] = useState(false);
    const [loadingClasses, setLoadingClasses] = useState(false);

    // Fetch teachers for student flow
    useEffect(() => {
        if (!isTeacher) {
            setLoadingTeachers(true);
            fetch('http://localhost:8000/teacher/list')
                .then(res => res.json())
                .then((data: Teacher[]) => setTeachers(data))
                .catch(err => {
                    console.error("Failed to load teachers", err);
                    setTeachers([]);
                })
                .finally(() => setLoadingTeachers(false));
        }
    }, [isTeacher]);

    // Fetch classes when teacher is selected (student flow)
    useEffect(() => {
        if (!isTeacher && selectedTeacherId) {
            setLoadingClasses(true);
            setClassLocation(''); // Reset class selection
            fetch(`http://localhost:8000/teacher/${selectedTeacherId}/classes`)
                .then(res => res.json())
                .then((data: string[]) => setClasses(data))
                .catch(err => {
                    console.error("Failed to load classes", err);
                    setClasses([]);
                })
                .finally(() => setLoadingClasses(false));
        }
    }, [isTeacher, selectedTeacherId]);

    const getSelectedTeacherName = () => {
        const teacher = teachers.find(t => t.teacher_id === selectedTeacherId);
        return teacher?.name || '';
    };

    const handleSubmit = () => {
        if (isTeacher) {
            // Teacher validation - only name required
            if (!name) {
                setError('Please enter your name.');
                return;
            }

            onStart({
                name,
                collegeId: '', // Teachers don't have college ID
                teacherName: teacherName || name,
                classLocation: '',
                isTeacher: true,
                teacherId: teacherId,
            });
        } else {
            // Student validation
            if (!name || !collegeId || !selectedTeacherId || !classLocation) {
                setError('Please fill in all required fields.');
                return;
            }

            // Basic alphanumeric check for location
            if (!/^[a-z0-9]+$/i.test(classLocation)) {
                setError('Class location must be alphanumeric.');
                return;
            }

            onStart({
                name,
                collegeId,
                teacherName: getSelectedTeacherName(),
                classLocation,
            });
        }
    };

    // Teacher Form - simplified, no teacher/class fields
    if (isTeacher) {
        return (
            <Card>
                <CardHeader>
                    <CardTitle>Welcome, {teacherName || 'Teacher'} 👋</CardTitle>
                    <CardDescription>
                        Please confirm your details before reporting your Big 5 scores.
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="space-y-2">
                        <Label htmlFor="name">Your Name</Label>
                        <Input
                            id="name"
                            placeholder="Your full name"
                            value={name || teacherName || ''}
                            onChange={(e) => setName(e.target.value)}
                        />
                    </div>

                    <div className="p-4 bg-indigo-50 rounded-lg text-sm text-indigo-700">
                        <p className="font-medium">Teacher Self-Report</p>
                        <p className="text-indigo-600 mt-1">
                            Report your Big 5 personality scores from an external test.
                            This helps calibrate your teaching style in simulations.
                        </p>
                    </div>

                    {error && (
                        <div className="text-sm text-red-500 font-medium">{error}</div>
                    )}

                    <Button onClick={handleSubmit} className="w-full">Continue to Report Scores</Button>
                </CardContent>
            </Card>
        );
    }

    // Student Form - full form with API-driven teacher/class selection
    return (
        <Card>
            <CardHeader>
                <CardTitle>Welcome 👋</CardTitle>
                <CardDescription>Please provide a few details before reporting your Big 5 scores.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
                <div className="space-y-2">
                    <Label htmlFor="name">Full Name</Label>
                    <Input
                        id="name"
                        placeholder="Jane Doe"
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                    />
                </div>

                <div className="space-y-2">
                    <Label htmlFor="collegeId">College ID</Label>
                    <Input
                        id="collegeId"
                        placeholder="e.g., 22CSE001"
                        value={collegeId}
                        onChange={(e) => setCollegeId(e.target.value)}
                    />
                </div>

                <div className="space-y-2">
                    <Label htmlFor="teacherName">Class Teacher</Label>
                    <Select value={selectedTeacherId} onValueChange={setSelectedTeacherId}>
                        <SelectTrigger>
                            <SelectValue placeholder="Select teacher" />
                        </SelectTrigger>
                        <SelectContent>
                            {loadingTeachers ? (
                                <div className="flex justify-center p-2">
                                    <Loader2 className="w-4 h-4 animate-spin text-muted-foreground" />
                                </div>
                            ) : teachers.length === 0 ? (
                                <div className="p-2 text-center text-muted-foreground text-sm">
                                    No teachers registered yet
                                </div>
                            ) : (
                                teachers.map((t) => (
                                    <SelectItem key={t.teacher_id} value={t.teacher_id}>
                                        {t.name}
                                    </SelectItem>
                                ))
                            )}
                        </SelectContent>
                    </Select>
                </div>

                <div className="space-y-2">
                    <Label htmlFor="classLocation">Class Location</Label>
                    <Select
                        value={classLocation}
                        onValueChange={setClassLocation}
                        disabled={!selectedTeacherId || loadingClasses}
                    >
                        <SelectTrigger>
                            <SelectValue placeholder={
                                !selectedTeacherId
                                    ? "Select teacher first"
                                    : loadingClasses
                                        ? "Loading..."
                                        : "Select class"
                            } />
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
                                    <SelectItem key={cls} value={cls}>
                                        {cls}
                                    </SelectItem>
                                ))
                            )}
                        </SelectContent>
                    </Select>
                </div>

                {error && (
                    <div className="text-sm text-red-500 font-medium">{error}</div>
                )}

                <Button onClick={handleSubmit} className="w-full">Continue to Report Scores</Button>
            </CardContent>
        </Card>
    );
}
