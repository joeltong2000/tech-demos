/**
 * AIS (Application Interface Services) is JD Edwards EnterpriseOne's REST
 * gateway. Orchestrations published on an AIS server are invokable via
 * `POST /jderest/v2/orchestrator/<name>` and discoverable via the discovery
 * endpoint. These types model the subset of that surface the MCP server
 * needs: a catalog of orchestrations (name + typed inputs) and an invoker.
 */

export type OrchestrationInputType = "string" | "number";

export interface OrchestrationInput {
  name: string;
  type: OrchestrationInputType;
  required: boolean;
  description: string;
}

export interface OrchestrationDescriptor {
  /** Orchestration name as published on the AIS server, e.g. "ORCH_CustomerSearch". */
  name: string;
  description: string;
  inputs: OrchestrationInput[];
}

/** An AIS orchestration invocation result: arbitrary JSON from the Orchestrator. */
export type OrchestrationResult = Record<string, unknown>;

/**
 * The connection the MCP server talks to. `MockAisConnection` implements it
 * in-memory; `RealAisConnection` implements it against a live AIS server.
 */
export interface AisConnection {
  /** Human-readable target, shown in UI badges and MCP server info. */
  readonly label: string;
  readonly mode: "mock" | "real";
  discoverOrchestrations(): Promise<OrchestrationDescriptor[]>;
  invokeOrchestration(
    name: string,
    inputs: Record<string, string | number>,
  ): Promise<OrchestrationResult>;
}
