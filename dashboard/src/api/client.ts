import { useQuery } from '@tanstack/react-query'

const API_BASE = import.meta.env.VITE_API_URL || ''

async function fetchJson<T>(url: string): Promise<T> {
  const res = await fetch(API_BASE + url)
  if (!res.ok) throw new Error(`API error ${res.status}: ${url}`)
  return res.json()
}

// ── Types ────────────────────────────────────────────────────────────────────

export interface ReputationData {
  kpis: {
    volume_total: number
    sentiment_negatif_pct: number
    gravity_score: number
    influenceurs_detracteurs: number
  }
  volume_by_day: { date: string; volume: number }[]
  platform_breakdown: { platform: string; count: number; pct: number }[]
  top_items: {
    entity: string
    summary: string | null
    priority: number | null
    sentiment: string
    source: string
    followers?: number | null
    url?: string | null
    evidence?: string[]
  }[]
  alert: { active: boolean; gravity_score: number; message: string }
}

export interface BenchmarkData {
  kpis: {
    share_of_voice_decathlon: number
    share_of_voice_intersport: number
    sentiment_decathlon_positive_pct: number
    sentiment_intersport_positive_pct: number
    total_mentions: number
  }
  radar: { topic: string; decathlon: number; intersport: number }[]
  sov_by_month: { month: string; decathlon: number; intersport: number }[]
  brand_scores: {
    decathlon: { total_mentions: number; positive_pct: number; negative_pct: number; neutral_pct: number }
    intersport: { total_mentions: number; positive_pct: number; negative_pct: number; neutral_pct: number }
  }
}

export interface CxData {
  kpis: {
    avg_rating: number
    nps_proxy: number
    total_reviews: number
    sav_negative_pct: number
  }
  rating_by_month: { month: string; decathlon: number | null; intersport: number | null }[]
  rating_distribution: { stars: number; count: number; pct: number }[]
  irritants: { label: string; count: number; pct: number; bar_pct: number }[]
  enchantements: { label: string; count: number; pct: number; bar_pct: number }[]
  sources: { name: string; count: number; url?: string | null }[]
}

export interface Recommendation {
  id: number
  priority: string
  pilier: string
  titre: string
  description: string
  impact: string
  effort: string
  kpi_cible: string
}

export interface SummaryData {
  entities: {
    name: string
    partition: string
    brand: string
    volume: number
    themes: string[]
    risks: string[]
    opportunities: string[]
    takeaway: string
  }[]
  top_risks: { flag: string; count: number }[]
  top_opportunities: { flag: string; count: number }[]
}

export interface HealthData {
  status: string
  last_run: string | null
  label: string | null
}

// ── Hooks ────────────────────────────────────────────────────────────────────

export function useReputation() {
  return useQuery<ReputationData>({
    queryKey: ['reputation'],
    queryFn: () => fetchJson('/api/reputation'),
  })
}

export function useBenchmark() {
  return useQuery<BenchmarkData>({
    queryKey: ['benchmark'],
    queryFn: () => fetchJson('/api/benchmark'),
  })
}

export function useCx() {
  return useQuery<CxData>({
    queryKey: ['cx'],
    queryFn: () => fetchJson('/api/cx'),
  })
}

export function useRecos() {
  return useQuery<{ recommendations: Recommendation[] }>({
    queryKey: ['recommendations'],
    queryFn: () => fetchJson('/api/recommendations'),
  })
}

export function useSummary() {
  return useQuery<SummaryData>({
    queryKey: ['summary'],
    queryFn: () => fetchJson('/api/summary'),
  })
}

export function useHealth() {
  return useQuery<HealthData>({
    queryKey: ['health'],
    queryFn: () => fetchJson('/api/health'),
    refetchInterval: 60_000,
  })
}
