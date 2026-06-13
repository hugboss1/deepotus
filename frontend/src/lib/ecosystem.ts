/**
 * lib/ecosystem.ts — API helpers for the Ecosystem / Payment flows.
 *
 * Centralised so components stay declarative. All requests go through
 * the canonical ``REACT_APP_BACKEND_URL`` + ``/api`` prefix.
 */

import axios, { AxiosInstance } from "axios";

const BACKEND_URL: string = process.env.REACT_APP_BACKEND_URL || "";
export const API_BASE: string = `${BACKEND_URL}/api`;

export const api: AxiosInstance = axios.create({
  baseURL: API_BASE,
  timeout: 20_000,
  headers: { "Content-Type": "application/json" },
});

// ---------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------
export interface BoardgameCounter {
  sold: number;
  next_number: number;
  founder_limit: number;
  is_founder: boolean;
  current_price_eur: number;
  current_tier:
    | "early_bird_1"
    | "early_bird_2"
    | "standard_founder"
    | "standard";
}

export interface CreateSessionPayload {
  product_id: "boardgame" | "videogen";
  origin_url: string;
  locale: "fr" | "en";
  customer?: {
    name?: string;
    email?: string;
  };
}

export interface CreateSessionResponse {
  url: string;
  session_id: string;
  amount_eur: number;
  currency: string;
  metadata: Record<string, string>;
}

export interface OrderSummary {
  type: "boardgame" | "videogen";
  founder_number?: number | null;
  founder_tier?: string | null;
  license_key?: string | null;
  amount_eur: number;
  currency: string;
  customer: {
    email?: string | null;
    name?: string | null;
    locale?: string;
  };
}

export interface CheckoutStatusOut {
  session_id: string;
  status: string;
  payment_status: string;
  amount_eur: number;
  currency: string;
  metadata: Record<string, string>;
  order?: OrderSummary | null;
}

export interface GenesisPayload {
  email: string;
  source:
    | "genesis_roman"
    | "genesis_mobile"
    | "genesis_secret"
    | "genesis_generic";
  locale: "fr" | "en";
}

export interface B2BPayload {
  name: string;
  email: string;
  company?: string;
  message: string;
  locale: "fr" | "en";
}

// ---------------------------------------------------------------------
// Endpoints
// ---------------------------------------------------------------------
export async function fetchBoardgameCounter(): Promise<BoardgameCounter> {
  const res = await api.get<BoardgameCounter>("/ecosystem/board-game/counter");
  return res.data;
}

export async function subscribeGenesis(payload: GenesisPayload): Promise<void> {
  await api.post("/ecosystem/genesis", payload);
}

export async function submitB2BInquiry(
  payload: B2BPayload
): Promise<{ inquiry_id: string }> {
  const res = await api.post<{ ok: boolean; inquiry_id: string }>(
    "/ecosystem/b2b-inquiry",
    payload
  );
  return { inquiry_id: res.data.inquiry_id };
}

export async function createCheckoutSession(
  payload: CreateSessionPayload
): Promise<CreateSessionResponse> {
  const res = await api.post<CreateSessionResponse>(
    "/payments/checkout/session",
    payload
  );
  return res.data;
}

export async function getCheckoutStatus(
  sessionId: string
): Promise<CheckoutStatusOut> {
  const res = await api.get<CheckoutStatusOut>(
    `/payments/checkout/status/${encodeURIComponent(sessionId)}`
  );
  return res.data;
}
