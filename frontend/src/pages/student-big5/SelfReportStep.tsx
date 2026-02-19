import { useState } from 'react';
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { UserDetails, Big5Result } from '../StudentBig5Page';
import { Loader2, ChevronDown, ChevronUp, Info } from "lucide-react";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";

interface SelfReportStepProps {
    userDetails: UserDetails;
    onComplete: (result: Big5Result) => void;
}

type DomainKey = 'O' | 'C' | 'E' | 'A' | 'N';

interface DomainInfo {
    key: DomainKey;
    title: string;
    description: string;
    facets: { num: number; title: string }[];
}

const DOMAIN_INFO: DomainInfo[] = [
    {
        key: 'O',
        title: 'Openness to Experience',
        description: 'Imaginative, creative, open to new ideas and experiences',
        facets: [
            { num: 1, title: 'Imagination' },
            { num: 2, title: 'Artistic Interests' },
            { num: 3, title: 'Emotionality' },
            { num: 4, title: 'Adventurousness' },
            { num: 5, title: 'Intellect' },
            { num: 6, title: 'Liberalism' },
        ]
    },
    {
        key: 'C',
        title: 'Conscientiousness',
        description: 'Organized, dependable, self-disciplined',
        facets: [
            { num: 1, title: 'Self-Efficacy' },
            { num: 2, title: 'Orderliness' },
            { num: 3, title: 'Dutifulness' },
            { num: 4, title: 'Achievement-Striving' },
            { num: 5, title: 'Self-Discipline' },
            { num: 6, title: 'Cautiousness' },
        ]
    },
    {
        key: 'E',
        title: 'Extraversion',
        description: 'Sociable, outgoing, energetic',
        facets: [
            { num: 1, title: 'Friendliness' },
            { num: 2, title: 'Gregariousness' },
            { num: 3, title: 'Assertiveness' },
            { num: 4, title: 'Activity Level' },
            { num: 5, title: 'Excitement-Seeking' },
            { num: 6, title: 'Cheerfulness' },
        ]
    },
    {
        key: 'A',
        title: 'Agreeableness',
        description: 'Cooperative, trusting, helpful',
        facets: [
            { num: 1, title: 'Trust' },
            { num: 2, title: 'Morality' },
            { num: 3, title: 'Altruism' },
            { num: 4, title: 'Cooperation' },
            { num: 5, title: 'Modesty' },
            { num: 6, title: 'Sympathy' },
        ]
    },
    {
        key: 'N',
        title: 'Neuroticism',
        description: 'Tendency to experience negative emotions',
        facets: [
            { num: 1, title: 'Anxiety' },
            { num: 2, title: 'Anger' },
            { num: 3, title: 'Depression' },
            { num: 4, title: 'Self-Consciousness' },
            { num: 5, title: 'Immoderation' },
            { num: 6, title: 'Vulnerability' },
        ]
    },
];

export default function SelfReportStep({ userDetails, onComplete }: SelfReportStepProps) {
    const [domainScores, setDomainScores] = useState<Record<DomainKey, string>>({
        O: '', C: '', E: '', A: '', N: ''
    });
    const [facetScores, setFacetScores] = useState<Record<string, string>>({});
    const [expandedDomains, setExpandedDomains] = useState<Record<DomainKey, boolean>>({
        O: true, C: true, E: true, A: true, N: true  // Start expanded since facets are required
    });
    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState('');

    const handleDomainChange = (key: DomainKey, value: string) => {
        // Allow empty or numbers 0-120
        if (value === '' || (/^\d+$/.test(value) && parseInt(value) >= 0 && parseInt(value) <= 120)) {
            setDomainScores(prev => ({ ...prev, [key]: value }));
            setError('');
        }
    };

    const handleFacetChange = (domain: DomainKey, facetNum: number, value: string) => {
        const facetKey = `${domain}_${facetNum}`;
        // Allow empty or numbers 0-20
        if (value === '' || (/^\d+$/.test(value) && parseInt(value) >= 0 && parseInt(value) <= 20)) {
            setFacetScores(prev => ({ ...prev, [facetKey]: value }));
        }
    };

    const toggleDomain = (key: DomainKey) => {
        setExpandedDomains(prev => ({ ...prev, [key]: !prev[key] }));
    };

    const validateScores = (): boolean => {
        for (const domain of DOMAIN_INFO) {
            const score = domainScores[domain.key];
            if (!score || score === '') {
                setError(`Please enter a score for ${domain.title}`);
                return false;
            }
            const numScore = parseInt(score);
            if (isNaN(numScore) || numScore < 0 || numScore > 120) {
                setError(`${domain.title} score must be between 0 and 120`);
                return false;
            }
        }
        // Validate all facet scores are provided (required)
        for (const domain of DOMAIN_INFO) {
            for (const facet of domain.facets) {
                const facetKey = `${domain.key}_${facet.num}`;
                const value = facetScores[facetKey];
                if (!value || value === '') {
                    setError(`Please enter a score for ${domain.title} - ${facet.title}`);
                    return false;
                }
                const numScore = parseInt(value);
                if (isNaN(numScore) || numScore < 0 || numScore > 20) {
                    setError(`${facet.title} score must be between 0 and 20`);
                    return false;
                }
            }
        }
        return true;
    };

    const handleSubmit = async () => {
        if (!validateScores()) return;

        setSubmitting(true);
        setError('');

        try {
            const isTeacher = userDetails.isTeacher;
            const endpoint = isTeacher
                ? 'http://localhost:8000/big5/teacher/self-report'
                : 'http://localhost:8000/big5/self-report';

            // Build domain scores object
            const domains: Record<DomainKey, { score: number; facets: Record<number, number> }> = {} as any;

            for (const domain of DOMAIN_INFO) {
                const score = parseInt(domainScores[domain.key]);
                const facets: Record<number, number> = {};

                // All facet scores are required
                for (const facet of domain.facets) {
                    const facetKey = `${domain.key}_${facet.num}`;
                    facets[facet.num] = parseInt(facetScores[facetKey]);
                }

                domains[domain.key] = {
                    score,
                    facets
                };
            }

            const submission = isTeacher
                ? {
                    session_id: crypto.randomUUID(),
                    teacher_id: userDetails.teacherId || '',
                    teacher_name: userDetails.teacherName || userDetails.name,
                    domain_scores: domains
                }
                : {
                    session_id: crypto.randomUUID(),
                    user_name: userDetails.name,
                    college_id: userDetails.collegeId,
                    teacher_name: userDetails.teacherName,
                    class_location: userDetails.classLocation,
                    domain_scores: domains
                };

            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(submission),
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || 'Submission failed');
            }

            const result = await response.json();
            onComplete(result);
        } catch (err) {
            console.error(err);
            setError(err instanceof Error ? err.message : 'Failed to submit. Please try again.');
        } finally {
            setSubmitting(false);
        }
    };

    // Check all domain scores AND all facet scores are filled
    const isComplete =
        Object.values(domainScores).every(score => score !== '') &&
        DOMAIN_INFO.every(domain =>
            domain.facets.every(facet => {
                const facetKey = `${domain.key}_${facet.num}`;
                return facetScores[facetKey] && facetScores[facetKey] !== '';
            })
        );

    return (
        <div className="space-y-6">
            {/* Instructions Card */}
            <Card className="bg-gradient-to-br from-indigo-50 to-purple-50 border-indigo-200">
                <CardHeader className="pb-3">
                    <CardTitle className="text-lg flex items-center gap-2">
                        <Info className="w-5 h-5 text-indigo-600" />
                        Self-Report Your Big 5 Scores
                    </CardTitle>
                    <CardDescription className="text-indigo-700">
                        Enter your Big 5 personality test results. You can take the official test at{' '}
                        <a
                            href="https://bigfive-test.com"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="underline font-medium hover:text-indigo-900"
                        >
                            bigfive-test.com
                        </a>
                        {' '}or similar platforms, then report your scores below.
                    </CardDescription>
                </CardHeader>
                <CardContent className="text-sm text-indigo-600">
                    <p><strong>Domain Score Range:</strong> 0 - 120 (sum of 6 facets × max 20 each)</p>
                    <p className="mt-1"><strong>Facet Score Range:</strong> 0 - 20 (all 6 required per domain)</p>
                </CardContent>
            </Card>

            {/* Domain Score Cards */}
            <div className="space-y-4">
                {DOMAIN_INFO.map((domain) => (
                    <Card key={domain.key} className="overflow-hidden">
                        <CardHeader className="pb-3">
                            <div className="flex items-center justify-between">
                                <div className="flex-1">
                                    <CardTitle className="text-lg flex items-center gap-2">
                                        <span className="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 text-white flex items-center justify-center text-sm font-bold">
                                            {domain.key}
                                        </span>
                                        {domain.title}
                                    </CardTitle>
                                    <CardDescription className="mt-1">{domain.description}</CardDescription>
                                </div>
                                <div className="flex items-center gap-3">
                                    <div className="flex items-center gap-2">
                                        <TooltipProvider>
                                            <Tooltip>
                                                <TooltipTrigger asChild>
                                                    <Label htmlFor={`domain-${domain.key}`} className="text-sm font-medium cursor-help">
                                                        Score
                                                    </Label>
                                                </TooltipTrigger>
                                                <TooltipContent>
                                                    <p>Enter your total score for {domain.title} (0-120)</p>
                                                </TooltipContent>
                                            </Tooltip>
                                        </TooltipProvider>
                                        <Input
                                            id={`domain-${domain.key}`}
                                            type="text"
                                            inputMode="numeric"
                                            placeholder="0-120"
                                            value={domainScores[domain.key]}
                                            onChange={(e) => handleDomainChange(domain.key, e.target.value)}
                                            className="w-20 text-center font-mono"
                                        />
                                    </div>
                                </div>
                            </div>
                        </CardHeader>

                        <Collapsible open={expandedDomains[domain.key]} onOpenChange={() => toggleDomain(domain.key)}>
                            <CollapsibleTrigger asChild>
                                <button className="w-full px-6 py-2 text-sm text-muted-foreground hover:bg-muted/50 flex items-center justify-center gap-1 transition-colors border-t">
                                    {expandedDomains[domain.key] ? (
                                        <>
                                            <ChevronUp className="w-4 h-4" />
                                            Hide Facet Scores
                                        </>
                                    ) : (
                                        <>
                                            <ChevronDown className="w-4 h-4" />
                                            Enter Facet Scores (Required)
                                        </>
                                    )}
                                </button>
                            </CollapsibleTrigger>
                            <CollapsibleContent>
                                <CardContent className="pt-4 bg-muted/30">
                                    <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                                        {domain.facets.map((facet) => (
                                            <div key={facet.num} className="space-y-1">
                                                <Label htmlFor={`facet-${domain.key}-${facet.num}`} className="text-xs text-muted-foreground">
                                                    {facet.num}. {facet.title}
                                                </Label>
                                                <Input
                                                    id={`facet-${domain.key}-${facet.num}`}
                                                    type="text"
                                                    inputMode="numeric"
                                                    placeholder="0-20"
                                                    value={facetScores[`${domain.key}_${facet.num}`] || ''}
                                                    onChange={(e) => handleFacetChange(domain.key, facet.num, e.target.value)}
                                                    className="h-8 text-center font-mono text-sm"
                                                />
                                            </div>
                                        ))}
                                    </div>
                                </CardContent>
                            </CollapsibleContent>
                        </Collapsible>
                    </Card>
                ))}
            </div>

            {/* Error Message */}
            {error && (
                <div className="p-3 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm font-medium">
                    {error}
                </div>
            )}

            {/* Submit Button */}
            <div className="flex justify-end pt-4">
                <Button
                    onClick={handleSubmit}
                    disabled={!isComplete || submitting}
                    size="lg"
                    className="min-w-32"
                >
                    {submitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                    Submit Scores
                </Button>
            </div>
        </div>
    );
}
