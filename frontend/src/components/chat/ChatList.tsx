// ChatList component - renders the full list of simulation messages with auto-scroll.
// Handles both regular chat messages and special voting summary cards.
import React, { useEffect, useRef } from "react";
import { ChatMessage, Message } from "./ChatMessage";
import { VotingCard } from "./VotingCard";
import { ScrollArea } from "@/components/ui/scroll-area";

interface ChatListProps {
  messages: Message[];
}

export function ChatList({ messages }: ChatListProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <ScrollArea className="h-full pr-4">
      <div className="flex flex-col pb-4">
        {messages.map((msg) =>
          msg.type === "voting" ? (
            <VotingCard
              key={msg.id}
              chunkId={msg.chunk_id ?? ""}
              votes={msg.votes ?? []}
              timestamp={msg.timestamp}
            />
          ) : (
            <ChatMessage key={msg.id} message={msg} />
          ),
        )}
        <div ref={bottomRef} />
      </div>
    </ScrollArea>
  );
}
