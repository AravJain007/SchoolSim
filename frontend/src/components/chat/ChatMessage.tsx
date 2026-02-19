// ChatMessage component - renders a single simulation chat message.
// Supports markdown rendering for Teacher/Student content.
// Principal messages are collapsible by default to reduce noise.
import React, { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { ChevronDown, ChevronRight } from "lucide-react";

export type MessageSender = "Teacher" | "Student" | "Principal" | "System";

export interface VoteEntry {
  name: string;
  student_id: string;
  understanding: number;
}

export interface Message {
  id: string;
  sender: MessageSender;
  name: string;
  content: string;
  timestamp: string;
  type?: "voting";
  run_index?: number;
  votes?: VoteEntry[];
  chunk_id?: string;
}

interface ChatMessageProps {
  message: Message;
}

export function ChatMessage({ message }: ChatMessageProps) {
  const isTeacher = message.sender === "Teacher";
  const isPrincipal = message.sender === "Principal";
  const [principalOpen, setPrincipalOpen] = useState(false);

  if (isPrincipal) {
    return (
      <div className="flex w-full mb-4 justify-center">
        <Collapsible
          open={principalOpen}
          onOpenChange={setPrincipalOpen}
          className="max-w-[90%] w-full border border-gray-200 rounded-lg bg-gray-50 shadow-sm"
        >
          <CollapsibleTrigger className="flex w-full items-center justify-between px-4 py-2 text-sm text-gray-600 hover:bg-gray-100 rounded-lg transition-colors">
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="text-[10px] h-4">
                Principal's Note
              </Badge>
              <span className="text-xs text-gray-500">{message.timestamp}</span>
            </div>
            {principalOpen ? (
              <ChevronDown className="h-4 w-4 opacity-50" />
            ) : (
              <ChevronRight className="h-4 w-4 opacity-50" />
            )}
          </CollapsibleTrigger>
          <CollapsibleContent className="px-4 pb-3 pt-1">
            <div className="prose prose-sm max-w-none text-gray-700 italic">
              <ReactMarkdown
                remarkPlugins={[remarkGfm, remarkMath]}
                rehypePlugins={[rehypeKatex]}
              >
                {message.content}
              </ReactMarkdown>
            </div>
          </CollapsibleContent>
        </Collapsible>
      </div>
    );
  }

  return (
    <div
      className={cn(
        "flex w-full mb-4",
        isTeacher ? "justify-start" : "justify-end",
      )}
    >
      <div
        className={cn(
          "max-w-[80%] rounded-lg p-3 text-sm shadow-sm",
          isTeacher && "bg-blue-100 text-blue-900 rounded-tl-none",
          !isTeacher && "bg-green-100 text-green-900 rounded-tr-none",
        )}
      >
        <div className="flex items-center gap-2 mb-1">
          <span className="font-semibold text-xs opacity-70">
            {message.name}
          </span>
        </div>
        <div className="prose prose-sm max-w-none [&_p]:my-1 [&_ul]:my-1 [&_ol]:my-1">
          <ReactMarkdown
            remarkPlugins={[remarkGfm, remarkMath]}
            rehypePlugins={[rehypeKatex]}
          >
            {message.content}
          </ReactMarkdown>
        </div>
        <div className="text-[10px] opacity-50 text-right mt-1">
          {message.timestamp}
        </div>
      </div>
    </div>
  );
}
