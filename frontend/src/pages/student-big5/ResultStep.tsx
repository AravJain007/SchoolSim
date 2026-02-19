import { Big5Result } from '../StudentBig5Page';
import { Card, CardContent, CardTitle, CardDescription } from "@/components/ui/card";

interface ResultStepProps {
    result: Big5Result;
}

export default function ResultStep({ result }: ResultStepProps) {
    const result_summary = result.result_summary;
    const domains = ["O", "C", "E", "A", "N"]; // Standard OCEAN order or mapping if needed
    // The key in result_summary is the letter (N, E, O, A, C)

    return (
        <div className="space-y-6">
            <Card className="bg-green-50 border-green-200">
                <CardContent className="pt-6">
                    <div className="flex flex-col items-center justify-center text-center space-y-2">
                        <h2 className="text-2xl font-bold text-green-800">Assessment Complete!</h2>
                        <p className="text-green-700">
                            Your results have been saved successfully. ID: <span className="font-mono text-sm bg-green-100 px-2 py-1 rounded">{result.inserted_id}</span>
                        </p>
                    </div>
                </CardContent>
            </Card>

            <div className="grid gap-6">
                {domains.map((domainChar) => {
                    const domainData = result_summary[domainChar];
                    if (!domainData) return null;

                    return (
                        <Card key={domainChar} className="overflow-hidden">
                            <div className="bg-slate-50 p-6 border-b">
                                <div className="space-y-1">
                                    <CardTitle className="text-2xl">{domainData.title}</CardTitle>
                                    <CardDescription className="text-base">{domainData.shortDescription}</CardDescription>
                                </div>
                                <div className="mt-4 p-4 bg-white rounded-lg border text-sm text-slate-600">
                                    {domainData.resultText}
                                </div>
                            </div>

                            <CardContent className="p-6">
                                <h4 className="font-semibold mb-4">Detailed Facets</h4>
                                <div className="grid gap-4 sm:grid-cols-2">
                                    {Object.entries(domainData.facets).map(([key, facet]: [string, any]) => (
                                        <div key={key} className="space-y-1 p-3 rounded-lg border bg-slate-50/50">
                                            <div className="flex items-center justify-between">
                                                <span className="font-medium text-sm">{facet.title}</span>
                                                <span className="text-xs uppercase font-semibold text-slate-500">{facet.result}</span>
                                            </div>
                                            <p className="text-xs text-muted-foreground line-clamp-2" title={facet.description}>
                                                {facet.description}
                                            </p>
                                        </div>
                                    ))}
                                </div>
                            </CardContent>
                        </Card>
                    );
                })}
            </div>
        </div>
    );
}
