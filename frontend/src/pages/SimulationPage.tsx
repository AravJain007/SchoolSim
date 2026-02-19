// SimulationPage - live classroom simulation view with real-time SSE streaming.
// Features: markdown chat, collapsible principal notes, student vote cards,
// and a run selector dropdown to browse each simulation run independently.
import React, { useState, useEffect, useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { ChatList } from "@/components/chat/ChatList";
import { Message } from "@/components/chat/ChatMessage";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { endpoints, apiClient } from "@/api/client";
import { CheckCircle2, PlayCircle, StopCircle } from "lucide-react";

export default function SimulationPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [messages, setMessages] = useState<Message[]>([]);
  const [status, setStatus] = useState<
    "running" | "completed" | "stopped" | "error"
  >("running");
  const [progress, setProgress] = useState(0);
  const [currentChunk, setCurrentChunk] = useState("Initializing...");

  // Multi-run tracking
  const [totalRuns, setTotalRuns] = useState(1);
  const [currentRun, setCurrentRun] = useState(0); // 0-indexed, latest active run
  // selectedRun mirrors currentRun unless the user manually picks one
  const [selectedRun, setSelectedRun] = useState<number>(0);
  const userPickedRun = useRef(false);

  const eventSourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    if (!id) return;

    const eventSource = new EventSource(endpoints.streamSimulation(id));
    eventSourceRef.current = eventSource;

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        if (data.type === "message" && data.payload) {
          setMessages((prev) => [...prev, data.payload]);
        } else if (data.type === "progress" && data.payload) {
          const {
            percentage,
            currentChunk: chunk,
            totalRuns: tr,
            currentRun: cr,
          } = data.payload;
          setProgress(percentage ?? 0);
          setCurrentChunk(chunk ?? "");
          if (tr != null) setTotalRuns(tr);
          if (cr != null) {
            setCurrentRun(cr);
            // Auto-follow latest run unless user manually selected one
            if (!userPickedRun.current) {
              setSelectedRun(cr);
            }
          }
        } else if (data.type === "status" && data.payload) {
          const newStatus = data.payload.status;
          setStatus(newStatus === "failed" ? "error" : newStatus);
          if (newStatus === "completed" || newStatus === "failed") {
            eventSource.close();
            eventSourceRef.current = null;
          }
        } else if (data.type === "error") {
          console.error("SSE error from server", data.payload);
          eventSource.close();
        }
        // Legacy flat format fallback
        else if (data.status && !data.type) {
          setStatus(data.status);
          setCurrentChunk(data.progress ?? "");
          if (data.status === "completed" || data.status === "failed") {
            eventSource.close();
            eventSourceRef.current = null;
          }
        }
      } catch (err) {
        console.error("Error parsing SSE data", err);
      }
    };

    eventSource.onerror = () => {
      console.warn("SSE connection issue - EventSource may reconnect");
    };

    return () => {
      eventSource.close();
      eventSourceRef.current = null;
    };
  }, [id]);

  const handleStop = async () => {
    if (id) {
      try {
        await apiClient.post(endpoints.stopSimulation(id));
        setStatus("stopped");
      } catch (err) {
        console.error("Failed to stop", err);
      }
    }
  };

  const handleRunSelect = (value: string) => {
    const idx = parseInt(value, 10);
    userPickedRun.current = true;
    setSelectedRun(idx);
  };

  // Filter messages to show only the selected run.
  // Messages without run_index (legacy/single-run) are shown for run 0.
  const visibleMessages = messages.filter((m) => {
    const ri = m.run_index ?? 0;
    return ri === selectedRun;
  });

  // Determine which run indices have started (have at least one message)
  const startedRuns = new Set(messages.map((m) => m.run_index ?? 0));

  return (
    <div className="h-[calc(100vh-100px)] grid grid-cols-1 md:grid-cols-4 gap-6">
      {/* Left Sidebar */}
      <div className="md:col-span-1 space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>Simulation Status</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Status badge */}
            <div className="flex items-center gap-2">
              {status === "running" && (
                <Badge variant="default" className="bg-blue-500 animate-pulse">
                  Running
                </Badge>
              )}
              {status === "completed" && (
                <Badge variant="default" className="bg-green-500">
                  Completed
                </Badge>
              )}
              {status === "stopped" && (
                <Badge variant="destructive">Stopped</Badge>
              )}
              {status === "error" && <Badge variant="destructive">Error</Badge>}
            </div>

            {/* Current activity */}
            <div className="space-y-1">
              <span className="text-xs text-neutral-500 uppercase font-bold">
                Current Activity
              </span>
              <p className="text-sm font-medium">{currentChunk}</p>
            </div>

            {/* Progress bar */}
            <div className="space-y-1">
              <div className="flex justify-between text-xs">
                <span>Progress</span>
                <span>{progress}%</span>
              </div>
              <Progress value={progress} />
            </div>

            {/* Run selector - only shown when multiple runs */}
            {totalRuns > 1 && (
              <div className="space-y-1">
                <span className="text-xs text-neutral-500 uppercase font-bold">
                  View Run
                </span>
                <Select
                  value={String(selectedRun)}
                  onValueChange={handleRunSelect}
                >
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="Select run..." />
                  </SelectTrigger>
                  <SelectContent>
                    {Array.from({ length: totalRuns }, (_, i) => {
                      const hasStarted = startedRuns.has(i);
                      const isActive = i === currentRun && status === "running";
                      return (
                        <SelectItem
                          key={i}
                          value={String(i)}
                          disabled={!hasStarted}
                          className={!hasStarted ? "opacity-40" : ""}
                        >
                          Run {i + 1}
                          {isActive ? " (live)" : ""}
                          {!hasStarted ? " (pending)" : ""}
                        </SelectItem>
                      );
                    })}
                  </SelectContent>
                </Select>
              </div>
            )}

            {/* Actions */}
            {status === "running" && (
              <Button
                variant="destructive"
                className="w-full"
                onClick={handleStop}
              >
                <StopCircle className="mr-2 h-4 w-4" /> Stop Simulation
              </Button>
            )}
            {status === "completed" && (
              <Button
                className="w-full"
                onClick={() => navigate(`/results/${id}`)}
              >
                <CheckCircle2 className="mr-2 h-4 w-4" /> View Results
              </Button>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Main Chat Area */}
      <div className="md:col-span-3 flex flex-col h-full bg-white rounded-xl border border-neutral-200 shadow-sm overflow-hidden">
        <div className="p-4 border-b border-neutral-100 bg-neutral-50/50 flex justify-between items-center">
          <h2 className="font-semibold text-neutral-700">
            Live Classroom Interaction
          </h2>
          <div className="flex items-center gap-3 text-xs text-neutral-400">
            {totalRuns > 1 && (
              <span className="font-medium text-neutral-600">
                Run {selectedRun + 1} / {totalRuns}
              </span>
            )}
            <span>ID: {id}</span>
          </div>
        </div>
        <div className="flex-1 p-4 overflow-hidden bg-neutral-50/30">
          {visibleMessages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-neutral-400">
              <PlayCircle className="h-12 w-12 mb-2 opacity-20" />
              <p>
                {status === "running" &&
                totalRuns > 1 &&
                !startedRuns.has(selectedRun)
                  ? `Run ${selectedRun + 1} hasn't started yet.`
                  : "Waiting for simulation to start..."}
              </p>
            </div>
          ) : (
            <ChatList messages={visibleMessages} />
          )}
        </div>
      </div>
    </div>
  );
}
