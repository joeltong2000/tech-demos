import type {
  AisConnection,
  OrchestrationDescriptor,
  OrchestrationResult,
} from "./types";

export interface RealAisConfig {
  baseUrl: string; // e.g. https://ais.example.com:9302
  username: string;
  password: string;
  environment: string; // e.g. JDV920
  role: string; // e.g. *ALL
}

/**
 * Client for a live JDE AIS server (tools release 9.2.4+ REST surface):
 *   POST /jderest/v2/tokenrequest                 -> session token
 *   GET  /jderest/v2/orchestrator/discover        -> published orchestrations
 *   POST /jderest/v2/orchestrator/<name>          -> invoke
 *
 * Only exercised when JDE_AIS_BASE_URL is configured; the offline demo uses
 * MockAisConnection instead. Discovery response shapes vary across tools
 * releases, so parsing here is defensive.
 */
export class RealAisConnection implements AisConnection {
  readonly label: string;
  readonly mode = "real" as const;

  private token: string | null = null;

  constructor(private readonly config: RealAisConfig) {
    this.label = `AIS ${config.baseUrl} (${config.environment})`;
  }

  private async ensureToken(): Promise<string> {
    if (this.token) return this.token;
    const res = await fetch(`${this.config.baseUrl}/jderest/v2/tokenrequest`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        username: this.config.username,
        password: this.config.password,
        deviceName: "oracle-mcp-jde-orchestrator",
        environment: this.config.environment,
        role: this.config.role,
      }),
    });
    if (!res.ok) throw new Error(`AIS tokenrequest failed: ${res.status} ${await res.text()}`);
    const body = (await res.json()) as { userInfo?: { token?: string } };
    const token = body.userInfo?.token;
    if (!token) throw new Error("AIS tokenrequest returned no token");
    this.token = token;
    return token;
  }

  async discoverOrchestrations(): Promise<OrchestrationDescriptor[]> {
    const token = await this.ensureToken();
    const res = await fetch(`${this.config.baseUrl}/jderest/v2/orchestrator/discover`, {
      headers: { "jde-AIS-Auth": token },
    });
    if (!res.ok) throw new Error(`AIS discovery failed: ${res.status} ${await res.text()}`);
    const body = (await res.json()) as {
      orchestrations?: Array<{
        name?: string;
        description?: string;
        inputs?: Array<{ name?: string; type?: string; required?: boolean; description?: string }>;
      }>;
    };
    return (body.orchestrations ?? [])
      .filter((o): o is typeof o & { name: string } => typeof o.name === "string")
      .map((o) => ({
        name: o.name,
        description: o.description ?? `JDE orchestration ${o.name}`,
        inputs: (o.inputs ?? [])
          .filter((i): i is typeof i & { name: string } => typeof i.name === "string")
          .map((i) => ({
            name: i.name,
            type: i.type === "number" ? ("number" as const) : ("string" as const),
            required: i.required ?? false,
            description: i.description ?? "",
          })),
      }));
  }

  async invokeOrchestration(
    name: string,
    inputs: Record<string, string | number>,
  ): Promise<OrchestrationResult> {
    const token = await this.ensureToken();
    const res = await fetch(
      `${this.config.baseUrl}/jderest/v2/orchestrator/${encodeURIComponent(name)}`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json", "jde-AIS-Auth": token },
        body: JSON.stringify(inputs),
      },
    );
    if (!res.ok) {
      throw new Error(`AIS orchestration '${name}' failed: ${res.status} ${await res.text()}`);
    }
    return (await res.json()) as OrchestrationResult;
  }
}
