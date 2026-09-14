import type { FinSightResponse, ResearchDetail, ResearchListItem } from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

export async function askFinSight(question: string): Promise<FinSightResponse> {
  const response = await fetch(`${API_URL}/api/v1/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });

  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    const message = payload?.error?.message ?? payload?.detail ?? `Request failed with status ${response.status}`;
    throw new Error(message);
  }
  return response.json() as Promise<FinSightResponse>;
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
