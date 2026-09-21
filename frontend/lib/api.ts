import type { CanvasDetail, ConversationDetail, ConversationListItem, FinSightResponse, MarketTickerSnapshot, ResearchDetail, ResearchListItem } from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

export async function askFinSight(
  question: string,
  conversationId?: string | null,
  canvasRevision?: number | null,
): Promise<FinSightResponse> {
  const response = await fetch(`${API_URL}/api/v1/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      question,
      conversation_id: conversationId || undefined,
      canvas_revision: canvasRevision || undefined,
    }),
  });

  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    const message = payload?.error?.message ?? payload?.detail ?? `Request failed with status ${response.status}`;
    throw new Error(message);
  }
  return response.json() as Promise<FinSightResponse>;
}

export type FinSightStreamEvent =
  | "status"
  | "tool_started"
  | "tool_completed"
  | "response_start"
  | "component"
  | "complete";

export async function streamFinSight(
  question: string,
  conversationId: string | null,
  canvasRevision: number | null | undefined,
  onEvent: (event: FinSightStreamEvent, data: Record<string, unknown>) => void,
  signal?: AbortSignal,
): Promise<void> {
  const response = await fetch(`${API_URL}/api/v1/query/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
    body: JSON.stringify({
      question,
      conversation_id: conversationId || undefined,
      canvas_revision: canvasRevision || undefined,
    }),
    signal,
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    throw new Error(payload?.error?.message ?? `Request failed with status ${response.status}`);
  }
  if (!response.body) throw new Error("Streaming is not supported by this browser.");

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  function dispatch(frame: string) {
    let event = "message";
    const dataLines: string[] = [];
    for (const line of frame.replaceAll("\r", "").split("\n")) {
      if (line.startsWith("event:")) event = line.slice(6).trim();
      if (line.startsWith("data:")) dataLines.push(line.slice(5).trim());
    }
    if (!dataLines.length) return;
    const data = JSON.parse(dataLines.join("\n")) as Record<string, unknown>;
    if (event === "error") throw new Error(String(data.message ?? "The query failed."));
    onEvent(event as FinSightStreamEvent, data);
  }

  while (true) {
    const { done, value } = await reader.read();
    buffer += decoder.decode(value, { stream: !done });
    let boundary = buffer.indexOf("\n\n");
    while (boundary >= 0) {
      dispatch(buffer.slice(0, boundary));
      buffer = buffer.slice(boundary + 2);
      boundary = buffer.indexOf("\n\n");
    }
    if (done) break;
  }
  if (buffer.trim()) dispatch(buffer);
}

async function apiRequest<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, options);
  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    throw new Error(payload?.error?.message ?? `Request failed with status ${response.status}`);
  }
  return response.status === 204 ? (undefined as T) : (response.json() as Promise<T>);
}

export function getResearchHistory(limit = 8): Promise<ResearchListItem[]> {
  return apiRequest(`/api/v1/research?limit=${limit}`);
}

export function getSavedResearch(researchId: string): Promise<ResearchDetail> {
  return apiRequest(`/api/v1/research/${encodeURIComponent(researchId)}`);
}

export function deleteSavedResearch(researchId: string): Promise<void> {
  return apiRequest(`/api/v1/research/${encodeURIComponent(researchId)}`, {
    method: "DELETE",
  });
}

export function createConversation(title = "New research"): Promise<ConversationListItem> {
  return apiRequest("/api/v1/conversations", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title }),
  });
}

export function getConversations(limit = 20): Promise<ConversationListItem[]> {
  return apiRequest(`/api/v1/conversations?limit=${limit}`);
}

export function getConversation(conversationId: string): Promise<ConversationDetail> {
  return apiRequest(`/api/v1/conversations/${encodeURIComponent(conversationId)}`);
}

export function getCanvas(conversationId: string): Promise<CanvasDetail> {
  return apiRequest(`/api/v1/conversations/${encodeURIComponent(conversationId)}/canvas`);
}

export function getMarketTicker(): Promise<MarketTickerSnapshot> {
  return apiRequest("/api/v1/market/ticker");
}

export function deleteConversation(conversationId: string): Promise<void> {
  return apiRequest(`/api/v1/conversations/${encodeURIComponent(conversationId)}`, { method: "DELETE" });
}
