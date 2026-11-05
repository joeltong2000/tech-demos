/**
 * The five valid per-call queue/scope overrides, per Oracle's
 * "Overriding the AIS Job Queue and Scope for Individual Orchestrator Calls"
 * (docs.oracle.com .../eotos/overriding-the-ais-job-queue-and-scope-for-individual-orchestrator-calls.html).
 * Note the DOUBLE underscore after JDE — that is how the doc spells the
 * override values, even though the queues themselves are named JDE_ASYNC etc.
 */
export const JOB_QUEUE_OVERRIDES = [
  "JDE__SINGLE",
  "JDE__USER_SINGLE",
  "JDE__USER_ASYNCH",
  "JDE__ASYNCH",
  "JDE__DEFAULT",
] as const;

export type JobQueueOverride = (typeof JOB_QUEUE_OVERRIDES)[number];

/** The reserved body parameter name used to pass the override. */
export const JOB_QUEUE_PARAM = "jde__jobQueue";

export function isJobQueueOverride(value: unknown): value is JobQueueOverride {
  return (
    typeof value === "string" &&
    (JOB_QUEUE_OVERRIDES as readonly string[]).includes(value)
  );
}

/**
 * Whether a queue override makes the call fire-and-forget (202 Accepted)
 * or synchronous (200 with the orchestration output).
 */
export function isFireAndForget(queue: JobQueueOverride): boolean {
  switch (queue) {
    case "JDE__ASYNCH":
    case "JDE__USER_ASYNCH":
      return true;
    case "JDE__SINGLE":
    case "JDE__USER_SINGLE":
    case "JDE__DEFAULT":
      return false;
    default: {
      const exhaustive: never = queue;
      throw new Error(`Unhandled job queue override: ${exhaustive}`);
    }
  }
}

/** One entry in the mock Orchestrator Monitor's "Run Details" store. */
export interface MonitorRun {
  runId: string;
  name: string;
  /** Statuses mirror the Orchestrator Monitor Run Details tab. */
  status: "Queued" | "Running" | "Successful" | "Failed";
  queue: JobQueueOverride;
  requestReceived: string;
  durationMs: number | null;
  input: Record<string, unknown>;
  output: Record<string, unknown> | null;
}
