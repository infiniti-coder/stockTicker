import { FormEvent, useEffect, useRef, useState } from "react";

import { api, ChatMessage, ChatSource } from "../api/client";
import { useChatHistory } from "../hooks/useChatHistory";

export function ChatPanel() {
  const { data: history, isLoading } = useChatHistory();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [seededFromHistory, setSeededFromHistory] = useState(false);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [streamingText, setStreamingText] = useState("");
  const listRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (history && !seededFromHistory) {
      setMessages(history);
      setSeededFromHistory(true);
    }
  }, [history, seededFromHistory]);

  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight });
  }, [messages, streamingText]);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const content = input.trim();
    if (!content || streaming) return;

    setInput("");
    setMessages((prev) => [...prev, { role: "user", content, sources: [], created_at: new Date().toISOString() }]);
    setStreaming(true);
    setStreamingText("");

    let finalText = "";
    try {
      await api.postChatMessage(
        content,
        (delta) => {
          finalText += delta;
          setStreamingText(finalText);
        },
        (sources: ChatSource[]) => {
          setMessages((prev) => [
            ...prev,
            { role: "assistant", content: finalText, sources, created_at: new Date().toISOString() },
          ]);
          setStreamingText("");
        },
      );
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "Couldn't reach the chat service. Check that ANTHROPIC_API_KEY is set on the backend.",
          sources: [],
          created_at: new Date().toISOString(),
        },
      ]);
      setStreamingText("");
    } finally {
      setStreaming(false);
    }
  }

  return (
    <div className="chat-panel">
      <h2 className="section-title">Ask Claude</h2>
      <div className="chat-messages" ref={listRef}>
        {isLoading ? (
          <p className="empty-state">Loading chat history…</p>
        ) : messages.length === 0 && !streaming ? (
          <p className="empty-state chat-empty-hint">
            Ask about a stock's price move, or how real stocks compare on data like momentum or sector — answers are
            grounded in this app's own market data and real web sources, never a buy/sell recommendation.
          </p>
        ) : (
          messages.map((m, i) => (
            <div key={i} className={`chat-message chat-message-${m.role}`}>
              <div className="chat-bubble">{m.content}</div>
              {m.sources.length > 0 && (
                <ul className="chat-sources">
                  {m.sources.map((s) => (
                    <li key={s.url}>
                      <a href={s.url} target="_blank" rel="noreferrer">
                        {s.title}
                      </a>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          ))
        )}
        {streaming && (
          <div className="chat-message chat-message-assistant">
            <div className="chat-bubble">{streamingText || "…"}</div>
          </div>
        )}
      </div>
      <form className="chat-input-row" onSubmit={handleSubmit}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Why is this stock down?"
          disabled={streaming}
        />
        <button type="submit" disabled={streaming || !input.trim()}>
          Send
        </button>
      </form>
    </div>
  );
}
