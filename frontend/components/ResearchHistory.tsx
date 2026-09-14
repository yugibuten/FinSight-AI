import type { ResearchListItem } from "@/lib/types";


function relativeTime(value: string) {
  const elapsed = Date.now() - new Date(value).getTime();
  const minutes = Math.max(0, Math.floor(elapsed / 60_000));
  if (minutes < 1) return "just now";
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}

interface ResearchHistoryProps {
  items: ResearchListItem[];
  busyId: string | null;
  onOpen: (id: string) => void;
  onDelete: (id: string) => void;
}

export function ResearchHistory({ items, busyId, onOpen, onDelete }: ResearchHistoryProps) {
  if (!items.length) return null;

  return (
    <section className="history-section">
      <div className="section-title">
        <h3>Recent research</h3>
        <span>Saved research</span>
      </div>
      <div className="history-strip">
        {items.map((item) => (
          <div className={`history-card ${item.status}`} key={item.id}>
            <button className="history-open" onClick={() => onOpen(item.id)} disabled={busyId === item.id || item.status !== "completed"}>
              <span>{item.response_type?.replaceAll("_", " ") ?? item.status}</span>
              <strong>{item.question}</strong>
              <small>{relativeTime(item.created_at)}{item.response_cache_hit ? " · cached" : ""}</small>
            </button>
            <button className="history-delete" aria-label={`Delete ${item.question}`} onClick={() => onDelete(item.id)}>×</button>
          </div>
        ))}
      </div>
    </section>
  );
}
