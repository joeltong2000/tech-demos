/** Minimal AIS Orchestrator REST client (basic auth). */

export interface OrchestratorCallResult {
  httpStatus: number;
  statusText: string;
  elapsedMs: number;
  /** Parsed JSON response body, or null when the body is empty (202s). */
  body: unknown;
}

export interface OrchestratorClientConfig {
  baseUrl: string;
  username: string;
  password: string;
}

/**
 * POST /jderest/v3/orchestrator/{orchestration}
 *
 * `body` is the orchestration input; callers opt into fire-and-forget by
 * including `"jde__jobQueue": "JDE__ASYNCH"` (or JDE__USER_ASYNCH) in it.
 * The `jde-AIS-MonitorRequest` header asks the server to record run details
 * for the Orchestrator Monitor (documented in "Triggering Monitoring").
 */
export async function invokeOrchestration(
  config: OrchestratorClientConfig,
  orchestrationName: string,
  body: Record<string, unknown>,
): Promise<OrchestratorCallResult> {
  const url = `${config.baseUrl}/jderest/v3/orchestrator/${encodeURIComponent(orchestrationName)}`;
  const credentials = Buffer.from(`${config.username}:${config.password}`).toString("base64");

  const started = performance.now();
  const response = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Basic ${credentials}`,
      "jde-AIS-MonitorRequest": "monitorRequestIO",
    },
    body: JSON.stringify(body),
  });
  const text = await response.text();
  const elapsedMs = performance.now() - started;

  return {
    httpStatus: response.status,
    statusText: response.statusText,
    elapsedMs,
    body: text.length > 0 ? JSON.parse(text) : null,
  };
}
