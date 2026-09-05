import { ChatSource } from "../api/client";

interface Props {
  content: string;
  sources?: ChatSource[];
  role?: "user" | "assistant";
}

/** One rendered answer — a message bubble plus its linked sources, if any.
 * Shared by ChatPanel (one per conversation turn) and ScreenerPage (one
 * per completed run), since both stream text + sources from the same
 * backend SSE shape (see api/client.ts's consumeSSE). */
export function StreamedAnswer({ content, sources = [], role = "assistant" }: Props) {
  return (
    <div className={`chat-message chat-message-${role}`}>
      <div className="chat-bubble">{content || "…"}</div>
      {sources.length > 0 && (
        <ul className="chat-sources">
          {sources.map((s) => (
            <li key={s.url}>
              <a href={s.url} target="_blank" rel="noreferrer">
                {s.title}
              </a>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
