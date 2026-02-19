// VotingCard component - expandable card showing student understanding votes after each chunk.
// Displays a summary line (avg score) when collapsed; full per-student breakdown when open.
import React, { useState } from "react";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { Badge } from "@/components/ui/badge";
import { ChevronDown, ChevronRight, BarChart2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { VoteEntry } from "./ChatMessage";

interface VotingCardProps {
  chunkId: string;
  votes: VoteEntry[];
  timestamp: string;
}

function understandingColor(score: number): string {
  if (score <= 1) return "bg-red-500";
  if (score === 2) return "bg-orange-400";
  if (score === 3) return "bg-yellow-400";
  if (score === 4) return "bg-lime-500";
  return "bg-green-500";
}

function understandingLabel(score: number): string {
  const labels: Record<number, string> = {
    1: "Lost",
    2: "Struggling",
    3: "Okay",
    4: "Good",
    5: "Excellent",
  };
  return labels[score] ?? String(score);
}

export function VotingCard({ chunkId, votes, timestamp }: VotingCardProps) {
  const [open, setOpen] = useState(false);

  const avg =
    votes.length > 0
      ? (
          votes.reduce((sum, v) => sum + v.understanding, 0) / votes.length
        ).toFixed(1)
      : "—";

  const avgNum =
    votes.length > 0
      ? votes.reduce((sum, v) => sum + v.understanding, 0) / votes.length
      : 0;

  return (
    <div className="flex w-full mb-4 justify-center">
      <Collapsible
        open={open}
        onOpenChange={setOpen}
        className="max-w-[90%] w-full border border-neutral-200 rounded-lg bg-neutral-50 shadow-sm"
      >
        <CollapsibleTrigger className="flex w-full items-center justify-between px-4 py-2 text-sm hover:bg-neutral-100 rounded-lg transition-colors">
          <div className="flex items-center gap-2">
            <BarChart2 className="h-4 w-4 text-neutral-500" />
            <Badge variant="secondary" className="text-[10px] h-4">
              Student Votes
            </Badge>
            <span className="text-xs text-neutral-500">Chunk: {chunkId}</span>
            <span
              className={cn(
                "text-xs font-semibold px-2 py-0.5 rounded-full text-white",
                understandingColor(avgNum),
              )}
            >
              Avg {avg}/5
            </span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-neutral-400">{timestamp}</span>
            {open ? (
              <ChevronDown className="h-4 w-4 opacity-50" />
            ) : (
              <ChevronRight className="h-4 w-4 opacity-50" />
            )}
          </div>
        </CollapsibleTrigger>

        <CollapsibleContent className="px-4 pb-3 pt-1">
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 mt-1">
            {votes.map((v) => (
              <div
                key={v.student_id}
                className="flex items-center justify-between border border-neutral-200 rounded-md px-3 py-1.5 bg-white text-xs"
              >
                <span className="truncate text-neutral-700 font-medium">
                  {v.name}
                </span>
                <span
                  className={cn(
                    "ml-2 text-[10px] font-bold px-1.5 py-0.5 rounded text-white shrink-0",
                    understandingColor(v.understanding),
                  )}
                >
                  {v.understanding}/5 · {understandingLabel(v.understanding)}
                </span>
              </div>
            ))}
          </div>
        </CollapsibleContent>
      </Collapsible>
    </div>
  );
}
