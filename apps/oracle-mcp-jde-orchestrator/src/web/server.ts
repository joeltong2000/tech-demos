import { join } from "node:path";
import { connectAis } from "../ais";
import { McpStdioClient } from "./mcp-stdio-client";

const PORT = Number(process.env.PORT ?? 9400);
const MCP_SERVER_ENTRY = join(import.meta.dir, "..", "mcp-server.ts");
const INDEX_HTML = join(import.meta.dir, "index.html");

// Only used for the header badge; the MCP server child process makes its
// own connection from the same environment.
const aisLabel = connectAis().label;
const aisMode = connectAis().mode;

const client = new McpStdioClient(["bun", "run", MCP_SERVER_ENTRY]);
await client.start();

const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body, null, 2), {
    status,
    headers: { "Content-Type": "application/json" },
  });

Bun.serve({
  port: PORT,
  routes: {
    "/": () => new Response(Bun.file(INDEX_HTML)),

    "/api/state": async () => {
      const tools = await client.listTools();
      return json({
        ais: { mode: aisMode, label: aisLabel },
        serverInfo: client.serverInfo,
        tools,
        traffic: client.traffic,
      });
    },

    "/api/call": {
      POST: async (req) => {
        const body = (await req.json()) as {
          tool?: string;
          args?: Record<string, unknown>;
        };
        if (!body.tool) return json({ error: "'tool' is required" }, 400);
        try {
          const result = await client.callTool(body.tool, body.args ?? {});
          return json({ result, traffic: client.traffic });
        } catch (err) {
          return json({ error: String(err), traffic: client.traffic }, 502);
        }
      },
    },
  },
});

console.log(`oracle-mcp-jde-orchestrator inspector → http://localhost:${PORT} (${aisLabel})`);
