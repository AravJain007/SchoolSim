import { useState } from "react";
import { useLocation } from "react-router-dom";
import StudentBig5Layout from "./student-big5/StudentBig5Layout";
import IntroStep from "./student-big5/IntroStep";
import SelfReportStep from "./student-big5/SelfReportStep";
import ResultStep from "./student-big5/ResultStep";

export type UserDetails = {
  name: string;
  collegeId: string;
  teacherName: string;
  classLocation: string;
  resume?: File;
  // Teacher-specific fields
  isTeacher?: boolean;
  teacherId?: string;
};

export type Big5Result = {
  result_summary: any;
  inserted_id: string;
};

interface LocationState {
  isTeacher?: boolean;
  teacherId?: string;
  teacherName?: string;
}

export default function StudentBig5Page() {
  const location = useLocation();
  const state = location.state as LocationState | null;

  const isTeacher = state?.isTeacher ?? false;
  const teacherId = state?.teacherId;
  const teacherName = state?.teacherName;

  // Teachers who logged in via Teacher Access already have name/ID - skip intro, go straight to scores
  const initialTeacherDetails: UserDetails | null =
    isTeacher && teacherId && teacherName
      ? {
          name: teacherName,
          collegeId: "",
          teacherName,
          classLocation: "",
          isTeacher: true,
          teacherId,
        }
      : null;

  const [step, setStep] = useState<"intro" | "scores" | "results">(
    initialTeacherDetails ? "scores" : "intro",
  );
  const [userDetails, setUserDetails] = useState<UserDetails | null>(
    initialTeacherDetails,
  );
  const [finalResult, setFinalResult] = useState<Big5Result | null>(null);

  const handleStartTest = (details: UserDetails) => {
    setUserDetails(details);
    setStep("scores");
  };

  const handleTestComplete = (result: Big5Result) => {
    setFinalResult(result);
    setStep("results");
  };

  const pageTitle = isTeacher
    ? "Teacher Big 5 Personality Report"
    : "Big 5 Personality Report";
  const pageDescription = isTeacher
    ? "Report your Big 5 personality test scores."
    : "Report your Big 5 personality test scores.";

  return (
    <div className="min-h-screen bg-gray-50/50 p-4 md:p-8">
      <div className="max-w-4xl mx-auto space-y-6">
        <div className="space-y-2">
          <h1 className="text-3xl font-bold tracking-tight">{pageTitle}</h1>
          <p className="text-muted-foreground">{pageDescription}</p>
        </div>

        <StudentBig5Layout>
          {step === "intro" && (
            <IntroStep
              onStart={handleStartTest}
              isTeacher={isTeacher}
              teacherId={teacherId}
              teacherName={teacherName}
            />
          )}
          {step === "scores" && userDetails && (
            <SelfReportStep
              userDetails={userDetails}
              onComplete={handleTestComplete}
            />
          )}
          {step === "results" && finalResult && (
            <ResultStep result={finalResult} />
          )}
        </StudentBig5Layout>
      </div>
    </div>
  );
}
