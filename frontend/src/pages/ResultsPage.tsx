import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  CardDescription,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Download,
  FileText,
  AlertTriangle,
  CheckCircle,
  ChevronDown,
  Maximize2,
  RefreshCw,
} from "lucide-react";
import { apiClient, endpoints } from "@/api/client";
import {
  Collapsible,
  CollapsibleTrigger,
  CollapsibleContent,
} from "@/components/ui/collapsible";

interface SimulationResult {
  id: string;
  totalRuns: number;
  avgUnderstanding: number;
  gapChunks: { id: string; topic: string; failureRate: number }[];
  commonDoubts: { topic: string; doubts: string[] }[];
  principalNotes: string[];
}

interface ApiResultResponse {
  simulation_id: string;
  total_runs: number;
  per_chunk_avg_understanding: Record<string, number>;
  gap_chunks: string[];
  gap_chunk_details: {
    chunk_id: string;
    failure_rate: number;
    avg_understanding: number;
  }[];
  common_doubts: Record<string, string[]>;
  principal_notes: string[];
  principal_retrying?: boolean;
}

function transformApiResult(api: ApiResultResponse): SimulationResult {
  const avgValues = Object.values(api.per_chunk_avg_understanding);
  const avgUnderstanding =
    avgValues.length > 0
      ? avgValues.reduce((a, b) => a + b, 0) / avgValues.length
      : 0;

  // Build a lookup from gap_chunk_details for failure rates
  const detailsMap = new Map(api.gap_chunk_details.map((d) => [d.chunk_id, d]));

  const gapChunks = api.gap_chunks.map((chunkId) => {
    const detail = detailsMap.get(chunkId);
    const failureRate = detail
      ? detail.failure_rate
      : Math.max(0, (3 - (api.per_chunk_avg_understanding[chunkId] ?? 3)) / 3);
    const label = chunkId
      .replace(/_/g, " ")
      .replace(/\b\w/g, (c) => c.toUpperCase());
    return { id: chunkId, topic: label, failureRate };
  });

  const commonDoubts = Object.entries(api.common_doubts).map(
    ([chunkId, doubts]) => ({
      topic: chunkId
        .replace(/_/g, " ")
        .replace(/\b\w/g, (c) => c.toUpperCase()),
      doubts,
    }),
  );

  return {
    id: api.simulation_id,
    totalRuns: api.total_runs,
    avgUnderstanding,
    gapChunks,
    commonDoubts,
    principalNotes: api.principal_notes,
  };
}

function triggerDownload(url: string, filename: string) {
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
}

function isPrincipalFailed(notes: string[]): boolean {
  if (notes.length === 0) return true;
  return notes.some(
    (n) =>
      n.startsWith("Exception") ||
      n.startsWith("Error:") ||
      n.startsWith("Retry failed:") ||
      n.includes("Unable to analyze"),
  );
}

export default function ResultsPage() {
  const { id } = useParams<{ id: string }>();
  const [data, setData] = useState<SimulationResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [principalExpanded, setPrincipalExpanded] = useState(false);
  const [heatmapLoading, setHeatmapLoading] = useState(false);
  const [heatmapError, setHeatmapError] = useState<string | null>(null);
  const [retryLoading, setRetryLoading] = useState(false);
  const [principalRetrying, setPrincipalRetrying] = useState(false);

  const handleDownloadHeatmap = async () => {
    if (!id) return;
    setHeatmapLoading(true);
    setHeatmapError(null);
    try {
      const response = await apiClient.get(endpoints.downloadHeatmap(id), {
        responseType: "arraybuffer",
      });
      const contentType =
        response.headers["content-type"] || "application/octet-stream";
      const contentDisposition = response.headers["content-disposition"] ?? "";
      const match = contentDisposition.match(/filename="?([^";\s]+)"?/);
      let filename = match ? match[1].trim() : null;
      if (!filename) {
        const extByType: Record<string, string> = {
          "application/pdf": ".pdf",
          "application/vnd.openxmlformats-officedocument.presentationml.presentation":
            ".pptx",
          "application/vnd.ms-powerpoint": ".ppt",
          "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            ".docx",
          "application/msword": ".doc",
        };
        const ext = extByType[contentType.split(";")[0].trim()] || ".pdf";
        filename = `heatmap_${id}${ext}`;
      }
      const blob = new Blob([response.data], { type: contentType });
      const blobUrl = URL.createObjectURL(blob);
      triggerDownload(blobUrl, filename);
      URL.revokeObjectURL(blobUrl);
    } catch (err: any) {
      const msg =
        err?.response?.data?.detail ??
        err?.message ??
        "Failed to download heatmap.";
      setHeatmapError(msg);
    } finally {
      setHeatmapLoading(false);
    }
  };

  const handleDownloadReport = async (format: "pdf" | "json") => {
    if (!id) return;
    try {
      const response = await apiClient.get(
        endpoints.downloadReport(id, format),
        {
          responseType: "arraybuffer",
        },
      );
      const filename = `report_${id}.${format}`;
      const contentType =
        response.headers["content-type"] ||
        (format === "pdf" ? "application/pdf" : "application/json");
      const blob = new Blob([response.data], { type: contentType });
      const blobUrl = URL.createObjectURL(blob);
      triggerDownload(blobUrl, filename);
      URL.revokeObjectURL(blobUrl);
    } catch (err: any) {
      console.error("Failed to download report:", err);
    }
  };

  const fetchResults = React.useCallback(() => {
    if (!id) return;
    return apiClient
      .get<ApiResultResponse>(endpoints.getResults(id))
      .then((res) => {
        setData(transformApiResult(res.data));
        setPrincipalRetrying(res.data.principal_retrying ?? false);
        return res.data;
      })
      .catch((err) => {
        const msg =
          err?.response?.data?.detail ||
          err?.message ||
          "Failed to load results.";
        setError(msg);
      });
  }, [id]);

  useEffect(() => {
    fetchResults();
  }, [fetchResults]);

  // Poll when principal retry is in progress
  useEffect(() => {
    if (!id || !principalRetrying) return;
    const interval = setInterval(() => fetchResults(), 2500);
    return () => clearInterval(interval);
  }, [id, principalRetrying, fetchResults]);

  const handleRetryPrincipal = async () => {
    if (!id) return;
    setRetryLoading(true);
    try {
      await apiClient.post(endpoints.retryPrincipal(id));
      setPrincipalRetrying(true);
      fetchResults();
    } catch (err: any) {
      const msg =
        err?.response?.data?.detail ??
        err?.message ??
        "Failed to start principal retry.";
      setError(msg);
    } finally {
      setRetryLoading(false);
    }
  };

  if (error)
    return (
      <div className="container mx-auto max-w-6xl pt-16 text-center">
        <p className="text-red-500 font-medium">{error}</p>
      </div>
    );

  if (!data)
    return (
      <div className="container mx-auto max-w-6xl pt-16 text-center text-neutral-500">
        Loading results...
      </div>
    );

  return (
    <div className="space-y-6 container mx-auto max-w-6xl">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">
            Simulation Results
          </h1>
          <p className="text-neutral-500">Report for Simulation {data.id}</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => handleDownloadReport("pdf")}>
            <FileText className="mr-2 h-4 w-4" /> Download Report (PDF)
          </Button>
          <Button onClick={() => handleDownloadReport("json")}>
            <Download className="mr-2 h-4 w-4" /> Export Data (JSON)
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Key Metrics */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-neutral-500">
              Avg. Understanding
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-4xl font-bold">
              {data.avgUnderstanding.toFixed(1)}/5.0
            </div>
            <p className="text-xs text-neutral-500 mt-1">
              Across {data.totalRuns} runs
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-neutral-500">
              Identified Gaps
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-4xl font-bold text-amber-600">
              {data.gapChunks.length}
            </div>
            <p className="text-xs text-neutral-500 mt-1">
              Chunks with &gt;40% failure rate
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-neutral-500">
              Principal Notes
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-4xl font-bold">
              {data.principalNotes.length}
            </div>
            <p className="text-xs text-neutral-500 mt-1">
              Pedagogical observations recorded
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Detailed Gaps */}
        <Card className="col-span-1">
          <CardHeader>
            <CardTitle>Critical Gaps Detected</CardTitle>
            <CardDescription>
              Topics where students consistently struggled.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {data.gapChunks.map((gap) => (
                <div
                  key={gap.id}
                  className="flex items-start gap-4 p-4 border border-amber-100 bg-amber-50/50 rounded-lg"
                >
                  <AlertTriangle className="h-5 w-5 text-amber-600 mt-0.5" />
                  <div>
                    <h4 className="font-semibold text-neutral-900">
                      {gap.topic}
                    </h4>
                    <p className="text-sm text-neutral-600">
                      Failure Rate: {(gap.failureRate * 100).toFixed(0)}%
                    </p>
                  </div>
                </div>
              ))}
              {data.gapChunks.length === 0 && (
                <div className="flex items-center gap-2 text-green-600 p-4 border border-green-100 bg-green-50/50 rounded-lg">
                  <CheckCircle className="h-5 w-5" />
                  <span>No critical gaps detected. Good job!</span>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Principal Notes */}
        <Card className="col-span-1">
          <CardHeader className="flex flex-row items-start justify-between gap-2">
            <div>
              <CardTitle>Principal's Observations</CardTitle>
              <CardDescription>
                Pedagogical notes from the KLI analysis.
              </CardDescription>
            </div>
            <Button
              variant="ghost"
              size="icon"
              className="shrink-0 text-neutral-500 hover:text-neutral-800"
              onClick={() => setPrincipalExpanded(true)}
              title="Expand observations"
            >
              <Maximize2 className="h-4 w-4" />
            </Button>
          </CardHeader>
          <CardContent>
            {principalRetrying && (
              <div className="mb-4 flex items-center gap-3 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                <RefreshCw className="h-4 w-4 text-blue-600 animate-spin" />
                <span className="text-sm text-blue-700">
                  Regenerating principal observations...
                </span>
              </div>
            )}
            {!principalRetrying && isPrincipalFailed(data.principalNotes) && (
              <div className="mb-4 flex flex-wrap items-center gap-3 p-3 bg-amber-50 border border-amber-200 rounded-lg">
                <AlertTriangle className="h-4 w-4 text-amber-600 shrink-0" />
                <span className="text-sm text-amber-700 flex-1">
                  Principal analysis failed or is incomplete.
                </span>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={handleRetryPrincipal}
                  disabled={retryLoading}
                  className="shrink-0"
                >
                  <RefreshCw
                    className={`mr-2 h-3 w-3 ${retryLoading ? "animate-spin" : ""}`}
                  />
                  {retryLoading ? "Retrying..." : "Retry Analysis"}
                </Button>
              </div>
            )}
            <ScrollArea className="h-[250px] w-full rounded-md border p-4">
              <div className="space-y-4">
                {data.principalNotes.map((note, i) => (
                  <div
                    key={i}
                    className="text-sm text-neutral-700 border-l-2 border-neutral-300 pl-3 prose prose-sm prose-neutral max-w-none"
                  >
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {note}
                    </ReactMarkdown>
                  </div>
                ))}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>

        {/* Principal Notes — expanded dialog */}
        <Dialog open={principalExpanded} onOpenChange={setPrincipalExpanded}>
          <DialogContent className="max-w-5xl w-full max-h-[85vh] flex flex-col">
            <DialogHeader>
              <DialogTitle>Principal's Observations</DialogTitle>
            </DialogHeader>
            <ScrollArea className="flex-1 pr-4 overflow-y-auto">
              <div className="space-y-6 py-2">
                {data.principalNotes.map((note, i) => (
                  <div
                    key={i}
                    className="text-sm text-neutral-700 border-l-2 border-neutral-300 pl-4 prose prose-neutral max-w-none"
                  >
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {note}
                    </ReactMarkdown>
                  </div>
                ))}
              </div>
            </ScrollArea>
          </DialogContent>
        </Dialog>
      </div>

      {/* Common Doubts */}
      <Card>
        <CardHeader>
          <CardTitle>Common Student Doubts</CardTitle>
          <CardDescription>
            Recurring questions across multiple simulation runs.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="divide-y divide-neutral-100">
            {data.commonDoubts.map((item, i) => (
              <Collapsible key={i}>
                <CollapsibleTrigger className="flex w-full items-center justify-between py-3 text-left group">
                  <div className="flex items-center gap-3">
                    <Badge variant="outline" className="text-xs shrink-0">
                      {item.doubts.length}
                    </Badge>
                    <span className="font-medium text-sm text-neutral-800">
                      {item.topic}
                    </span>
                  </div>
                  <ChevronDown className="h-4 w-4 text-neutral-400 shrink-0 transition-transform duration-200 group-data-[state=open]:rotate-180" />
                </CollapsibleTrigger>
                <CollapsibleContent className="pb-3">
                  <ul className="space-y-2 pl-1">
                    {item.doubts.map((doubt, j) => (
                      <li
                        key={j}
                        className="text-sm text-neutral-600 border-l-2 border-neutral-200 pl-3 py-0.5"
                      >
                        {doubt}
                      </li>
                    ))}
                  </ul>
                </CollapsibleContent>
              </Collapsible>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Heatmap Download */}
      <Card>
        <CardHeader>
          <CardTitle>Material Heatmap</CardTitle>
          <CardDescription>
            Download the annotated PDF/PPT with color-coded understanding
            overlays and gap annotations per slide.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-start gap-3">
            <div className="w-full rounded-lg border-2 border-dashed border-neutral-200 bg-neutral-50 p-8 flex flex-col items-center gap-4">
              <div className="flex items-center gap-3 text-neutral-500">
                <FileText className="h-10 w-10 text-neutral-300" />
                <div>
                  <p className="font-medium text-neutral-700">
                    Annotated Material
                  </p>
                  <p className="text-sm text-neutral-400">
                    Slides/pages colour-coded by student understanding
                    (green&nbsp;→&nbsp;amber&nbsp;→&nbsp;red) with gap notes in
                    footers.
                  </p>
                </div>
              </div>
              <Button
                onClick={handleDownloadHeatmap}
                disabled={heatmapLoading}
                className="mt-2"
              >
                <Download className="mr-2 h-4 w-4" />
                {heatmapLoading ? "Generating…" : "Download Heatmap"}
              </Button>
              {heatmapError && (
                <p className="text-sm text-red-500">{heatmapError}</p>
              )}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
