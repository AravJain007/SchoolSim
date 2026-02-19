import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { GraduationCap, School, ChevronRight, LayoutDashboard, FileText, Loader2, UserPlus, X } from "lucide-react";

interface Teacher {
    teacher_id: string;
    name: string;
}

export default function WelcomePage() {
    const navigate = useNavigate();
    const [role, setRole] = useState<'student' | 'teacher' | null>(null);
    const [teachers, setTeachers] = useState<Teacher[]>([]);
    const [selectedTeacherId, setSelectedTeacherId] = useState<string>("");
    const [loadingTeachers, setLoadingTeachers] = useState(false);

    // Registration form state
    const [showRegister, setShowRegister] = useState(false);
    const [registerName, setRegisterName] = useState("");
    const [registerEmail, setRegisterEmail] = useState("");
    const [registerDepartment, setRegisterDepartment] = useState("");
    const [registerClasses, setRegisterClasses] = useState("");
    const [registering, setRegistering] = useState(false);
    const [registerError, setRegisterError] = useState("");

    const fetchTeachers = () => {
        setLoadingTeachers(true);
        fetch('http://localhost:8000/teacher/list')
            .then(res => res.json())
            .then((data: Teacher[]) => setTeachers(data))
            .catch(err => {
                console.error("Failed to load teachers", err);
                setTeachers([]);
            })
            .finally(() => setLoadingTeachers(false));
    };

    useEffect(() => {
        if (role === 'teacher') {
            fetchTeachers();
        }
    }, [role]);

    const handleStudentClick = () => {
        navigate('/big5', { state: { isTeacher: false } });
    };

    const handleTeacherClick = () => {
        setRole('teacher');
    };

    const getSelectedTeacher = () => {
        return teachers.find(t => t.teacher_id === selectedTeacherId);
    };

    const handleTeacherAction = (action: 'big5' | 'dashboard') => {
        const teacher = getSelectedTeacher();
        if (!teacher) return;

        // Store in localStorage for persistence
        localStorage.setItem('currentTeacher', JSON.stringify(teacher));

        if (action === 'big5') {
            navigate('/big5', {
                state: {
                    isTeacher: true,
                    teacherId: teacher.teacher_id,
                    teacherName: teacher.name
                }
            });
        } else {
            navigate('/dashboard', {
                state: {
                    teacherId: teacher.teacher_id,
                    teacherName: teacher.name
                }
            });
        }
    };

    const handleRegister = async () => {
        if (!registerName.trim()) {
            setRegisterError("Name is required");
            return;
        }

        const classes = registerClasses
            .split(',')
            .map(c => c.trim())
            .filter(c => c.length > 0);

        if (classes.length === 0) {
            setRegisterError("At least one class is required");
            return;
        }

        setRegistering(true);
        setRegisterError("");

        try {
            const response = await fetch('http://localhost:8000/teacher/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name: registerName.trim(),
                    email: registerEmail.trim() || null,
                    department: registerDepartment.trim() || null,
                    classes: classes,
                }),
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Registration failed');
            }

            // Registration successful - refresh teacher list and close form
            setShowRegister(false);
            setRegisterName("");
            setRegisterEmail("");
            setRegisterDepartment("");
            setRegisterClasses("");
            fetchTeachers();
        } catch (err: any) {
            setRegisterError(err.message || 'Registration failed');
        } finally {
            setRegistering(false);
        }
    };

    // Registration Form Modal
    if (showRegister) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-indigo-50 via-white to-purple-50 p-4">
                <Card className="w-full max-w-md shadow-xl border-t-4 border-purple-500 animate-in fade-in zoom-in-95 duration-300">
                    <CardHeader className="text-center pb-2">
                        <div className="flex justify-between items-start">
                            <div className="flex-1" />
                            <div className="flex-1 text-center">
                                <CardTitle className="text-2xl font-bold text-slate-800">Register as Teacher</CardTitle>
                                <CardDescription>Create your teacher profile</CardDescription>
                            </div>
                            <div className="flex-1 flex justify-end">
                                <Button variant="ghost" size="icon" onClick={() => setShowRegister(false)}>
                                    <X className="w-4 h-4" />
                                </Button>
                            </div>
                        </div>
                    </CardHeader>
                    <CardContent className="space-y-4 pt-4">
                        <div className="space-y-2">
                            <Label htmlFor="name">Full Name *</Label>
                            <Input
                                id="name"
                                placeholder="Dr. Jane Smith"
                                value={registerName}
                                onChange={(e) => setRegisterName(e.target.value)}
                            />
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="email">Email (optional)</Label>
                            <Input
                                id="email"
                                type="email"
                                placeholder="jane.smith@university.edu"
                                value={registerEmail}
                                onChange={(e) => setRegisterEmail(e.target.value)}
                            />
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="department">Department (optional)</Label>
                            <Input
                                id="department"
                                placeholder="Computer Science"
                                value={registerDepartment}
                                onChange={(e) => setRegisterDepartment(e.target.value)}
                            />
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="classes">Classes *</Label>
                            <Input
                                id="classes"
                                placeholder="SJT301, CDMM102, TT501"
                                value={registerClasses}
                                onChange={(e) => setRegisterClasses(e.target.value)}
                            />
                            <p className="text-xs text-muted-foreground">
                                Enter class locations separated by commas
                            </p>
                        </div>

                        {registerError && (
                            <div className="text-sm text-red-500 font-medium">{registerError}</div>
                        )}

                        <Button
                            onClick={handleRegister}
                            className="w-full"
                            disabled={registering}
                        >
                            {registering && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
                            Register
                        </Button>
                    </CardContent>
                </Card>
            </div>
        );
    }

    // Teacher Selection View
    if (role === 'teacher') {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-indigo-50 via-white to-purple-50 p-4">
                <Card className="w-full max-w-md shadow-xl border-t-4 border-indigo-500 animate-in fade-in zoom-in-95 duration-300">
                    <CardHeader className="text-center pb-2">
                        <CardTitle className="text-2xl font-bold text-slate-800">Teacher Access</CardTitle>
                        <CardDescription>Select your profile or register</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-6 pt-4">
                        <div className="space-y-2">
                            <label className="text-sm font-medium text-slate-700">Select Teacher</label>
                            <Select value={selectedTeacherId} onValueChange={setSelectedTeacherId}>
                                <SelectTrigger className="w-full">
                                    <SelectValue placeholder="Choose your name" />
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

                        {selectedTeacherId && (
                            <div className="grid grid-cols-2 gap-4 animate-in fade-in slide-in-from-bottom-2 duration-300">
                                <Button
                                    variant="outline"
                                    className="h-24 flex flex-col gap-2 hover:border-indigo-500 hover:bg-indigo-50 transition-all"
                                    onClick={() => handleTeacherAction('big5')}
                                >
                                    <FileText className="w-6 h-6 text-indigo-600" />
                                    <span>Big 5 Test</span>
                                </Button>
                                <Button
                                    variant="outline"
                                    className="h-24 flex flex-col gap-2 hover:border-indigo-500 hover:bg-indigo-50 transition-all"
                                    onClick={() => handleTeacherAction('dashboard')}
                                >
                                    <LayoutDashboard className="w-6 h-6 text-indigo-600" />
                                    <span>Dashboard</span>
                                </Button>
                            </div>
                        )}

                        <div className="border-t pt-4">
                            <Button
                                variant="outline"
                                className="w-full"
                                onClick={() => setShowRegister(true)}
                            >
                                <UserPlus className="w-4 h-4 mr-2" />
                                Register as New Teacher
                            </Button>
                        </div>

                        <Button
                            variant="ghost"
                            className="w-full text-muted-foreground hover:text-slate-800"
                            onClick={() => { setRole(null); setSelectedTeacherId(""); }}
                        >
                            Back to Role Selection
                        </Button>
                    </CardContent>
                </Card>
            </div>
        );
    }

    // Main Welcome View
    return (
        <div className="min-h-screen flex flex-col items-center justify-center bg-gradient-to-br from-indigo-50 via-white to-purple-50 p-4">
            <div className="text-center mb-12 space-y-2 animate-in fade-in slide-in-from-top-4 duration-700">
                <h1 className="text-5xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-indigo-600 to-purple-600 pb-2">
                    Sims Teacher
                </h1>
                <p className="text-slate-500 text-lg font-medium">Next Generation Educational Simulations</p>
            </div>

            <div className="grid md:grid-cols-2 gap-8 max-w-4xl w-full px-4">
                {/* Student Card */}
                <Card
                    className="group relative overflow-hidden cursor-pointer hover:shadow-2xl transition-all duration-300 border-t-4 border-emerald-400 hover:-translate-y-1"
                    onClick={handleStudentClick}
                >
                    <div className="absolute inset-0 bg-gradient-to-br from-emerald-50 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                    <CardHeader className="text-center pt-8 pb-4 relative">
                        <div className="mx-auto bg-emerald-100 w-20 h-20 rounded-full flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300">
                            <GraduationCap className="h-10 w-10 text-emerald-600" />
                        </div>
                        <CardTitle className="text-3xl text-slate-800 mb-2">I am a Student</CardTitle>
                        <CardDescription className="text-base">Take assessments and participate in simulations</CardDescription>
                    </CardHeader>
                    <CardContent className="pb-10 text-center relative">
                        <div className="flex items-center justify-center text-emerald-600 font-bold text-lg opacity-0 group-hover:opacity-100 transition-all transform translate-y-4 group-hover:translate-y-0 duration-300">
                            Get Started <ChevronRight className="ml-1 w-5 h-5" />
                        </div>
                    </CardContent>
                </Card>

                {/* Teacher Card */}
                <Card
                    className="group relative overflow-hidden cursor-pointer hover:shadow-2xl transition-all duration-300 border-t-4 border-indigo-500 hover:-translate-y-1"
                    onClick={handleTeacherClick}
                >
                    <div className="absolute inset-0 bg-gradient-to-br from-indigo-50 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                    <CardHeader className="text-center pt-8 pb-4 relative">
                        <div className="mx-auto bg-indigo-100 w-20 h-20 rounded-full flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300">
                            <School className="h-10 w-10 text-indigo-600" />
                        </div>
                        <CardTitle className="text-3xl text-slate-800 mb-2">I am a Teacher</CardTitle>
                        <CardDescription className="text-base">Manage simulations, view analytics and reports</CardDescription>
                    </CardHeader>
                    <CardContent className="pb-10 text-center relative">
                        <div className="flex items-center justify-center text-indigo-600 font-bold text-lg opacity-0 group-hover:opacity-100 transition-all transform translate-y-4 group-hover:translate-y-0 duration-300">
                            Teacher Login <ChevronRight className="ml-1 w-5 h-5" />
                        </div>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
