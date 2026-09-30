import { MockAisConnection } from "./mock";
import { RealAisConnection } from "./real";
import type { AisConnection } from "./types";

export type { AisConnection } from "./types";
export type {
  OrchestrationDescriptor,
  OrchestrationInput,
  OrchestrationResult,
} from "./types";

/**
 * Pick the AIS connection from the environment: a configured
 * JDE_AIS_BASE_URL selects the real AIS REST client, otherwise the
 * offline in-memory mock (the demo happy path).
 */
export function connectAis(env: Record<string, string | undefined> = process.env): AisConnection {
  const baseUrl = env.JDE_AIS_BASE_URL?.trim();
  if (!baseUrl) return new MockAisConnection();
  return new RealAisConnection({
    baseUrl: baseUrl.replace(/\/$/, ""),
    username: env.JDE_AIS_USERNAME ?? "",
    password: env.JDE_AIS_PASSWORD ?? "",
    environment: env.JDE_AIS_ENVIRONMENT ?? "JDV920",
    role: env.JDE_AIS_ROLE ?? "*ALL",
  });
}
