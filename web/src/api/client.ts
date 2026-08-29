import type { EventSummary, HazardEvent, RiskProfile } from '../types/hazard';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1';

export async function fetchEvents(): Promise<HazardEvent[]> {
  const response = await fetch(`${API_BASE_URL}/events`);
  if (!response.ok) {
    throw new Error('Failed to fetch events');
  }
  return response.json();
}

export async function fetchRiskProfiles(): Promise<RiskProfile[]> {
  const response = await fetch(`${API_BASE_URL}/risk-profile/clusters`);
  if (!response.ok) {
    throw new Error('Failed to fetch risk profiles');
  }
  return response.json();
}

export async function fetchRiskProfile(regionName: string): Promise<RiskProfile> {
  const response = await fetch(`${API_BASE_URL}/risk-profile/${encodeURIComponent(regionName)}`);
  if (!response.ok) {
    throw new Error('Failed to fetch risk profile');
  }
  return response.json();
}

export type EventSummaryParams = {
  west?: number;
  south?: number;
  east?: number;
  north?: number;
  region_name?: string;
};

export async function fetchEventSummary(params?: EventSummaryParams): Promise<EventSummary> {
  const query = new URLSearchParams();
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined) query.set(key, String(value));
    });
  }
  const response = await fetch(`${API_BASE_URL}/events/summary?${query.toString()}`);
  if (!response.ok) {
    throw new Error('Failed to fetch event summary');
  }
  return response.json();
}
