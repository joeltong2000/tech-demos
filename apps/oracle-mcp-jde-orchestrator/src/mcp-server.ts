import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z, type ZodRawShape, type ZodTypeAny } from "zod";
import { connectAis } from "./ais";
import type { AisConnection, OrchestrationDescriptor } from "./ais";

/**
 * The AIS-native MCP server: every orchestration published on the JDE AIS
 * server becomes one MCP tool, schema included. Nothing is hardcoded about
 * the tool surface — publish a new orchestration in Orchestrator Studio,
 * restart the server, and agents see a new tool.
 *
 * Run standalone for any MCP client (Claude Desktop, etc.): `bun run mcp`.
 * The web inspector (`bun run dev`) spawns this same file over stdio.
 */

function inputShape(descriptor: OrchestrationDescriptor): ZodRawShape {
  const shape: ZodRawShape = {};
  for (const input of descriptor.inputs) {
    let schema: ZodTypeAny =
      input.type === "number"
        ? z.coerce.number().describe(input.description)
        : z.string().describe(input.description);
    if (!input.required) schema = schema.optional();
    shape[input.name] = schema;
  }
  return shape;
}

interface ToolCallResult {
  [key: string]: unknown;
  isError: boolean;
  content: Array<{ type: "text"; text: string }>;
}

/**
 * registerTool's generics infer per-tool arg types from literal Zod shapes;
 * with shapes generated at runtime from AIS discovery that inference recurses
 * (TS2589), so we pin a monomorphic signature for the dynamic case.
 */
type RegisterDynamicTool = (
  name: string,
  config: { title: string; description: string; inputSchema: ZodRawShape },
  handler: (args: Record<string, string | number>) => Promise<ToolCallResult>,
) => void;

export async function buildServer(ais: AisConnection): Promise<McpServer> {
  const server = new McpServer({
    name: "oracle-mcp-jde-orchestrator",
    version: "0.1.0",
  });
  const registerTool = server.registerTool.bind(server) as RegisterDynamicTool;

  const orchestrations = await ais.discoverOrchestrations();
  for (const descriptor of orchestrations) {
    registerTool(
      descriptor.name,
      {
        title: descriptor.name,
        description: `${descriptor.description} [JDE Orchestrator via ${ais.label}]`,
        inputSchema: inputShape(descriptor),
      },
      async (args) => {
        try {
          const result = await ais.invokeOrchestration(descriptor.name, args);
          const failed = typeof result.exception === "string";
          return {
            isError: failed,
            content: [{ type: "text", text: JSON.stringify(result, null, 2) }],
          };
        } catch (err) {
          return {
            isError: true,
            content: [{ type: "text", text: String(err) }],
          };
        }
      },
    );
  }

  return server;
}

if (import.meta.main) {
  const ais = connectAis();
  const server = await buildServer(ais);
  await server.connect(new StdioServerTransport());
  console.error(`[mcp] oracle-mcp-jde-orchestrator ready on stdio — ${ais.label}`);
}
