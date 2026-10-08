# Oracle MCP for JDE Orchestrator (AIS-native)

A runnable demo of the idea behind Oracle's MCP server for JD Edwards EnterpriseOne Orchestrator
(source inspiration: [this LinkedIn post](https://www.linkedin.com/posts/barizon_jdedwards-innova9-jdedwards-activity-7507881685003161601-OhnO)):
orchestrations published on a JDE **AIS** (Application Interface Services) server are discovered
at startup and exposed **1:1 as MCP tools**, so any MCP client — Claude Desktop, an agent
framework, this repo's web inspector — can call live JDE business logic. "AIS-native" means
nothing about the tool surface is hardcoded: publish a new orchestration in Orchestrator Studio,
restart the server, and agents see a new tool with its input schema.

## Run it

Requires [Bun](https://bun.sh) (`curl -fsSL https://bun.sh/install | bash`).

```bash
cd apps/oracle-mcp-jde-orchestrator
bun install
bun run dev
```

Open http://localhost:9400. No `.env` is needed: without `JDE_AIS_BASE_URL` the MCP server talks
to a built-in **mock AIS layer** (in-memory E1 tables — F0101 address book, F41021 item
availability, F4211 sales orders — returning AIS-shaped payloads with JDE field names like
`szOrderNumber` and `mnQuantityAvailable`).

### Happy path to try

1. `ORCH_CustomerSearch` with `szSearchText` = `Capital` → two Address Book matches.
2. `ORCH_GetItemAvailability` with `szItemNumber` = `210`, `szBranchPlant` = `30` → availability 109.
3. `ORCH_CreateSalesOrder` with `mnSoldTo` = `4242`, `szBranchPlant` = `30`, `szItemNumber` = `210`,
   `mnQuantityOrdered` = `5` → returns `szOrderNumber: "8001"` and the order total.
4. `ORCH_GetOrderStatus` with `mnOrderNumber` = `8001` → the order you just created, with lines.

The right-hand panel shows the raw MCP JSON-RPC 2.0 traffic (`initialize`, `tools/list`,
`tools/call`) exchanged with the server for every step.

## Use it from a real MCP client

The same server runs standalone on stdio:

```bash
bun run mcp
```

Claude Desktop config entry:

```json
{
  "mcpServers": {
    "jde-orchestrator": {
      "command": "bun",
      "args": ["run", "/path/to/apps/oracle-mcp-jde-orchestrator/src/mcp-server.ts"]
    }
  }
}
```

## Against a real JDE AIS server

```bash
cp .env.example .env
# set JDE_AIS_BASE_URL, JDE_AIS_USERNAME, JDE_AIS_PASSWORD, JDE_AIS_ENVIRONMENT, JDE_AIS_ROLE
bun run dev
```

With `JDE_AIS_BASE_URL` set, the server authenticates via `POST /jderest/v2/tokenrequest`,
discovers orchestrations from the AIS discovery endpoint, and invokes them via
`POST /jderest/v2/orchestrator/<name>` (`src/ais/real.ts`). Never commit `.env`.

## How it works

- `src/ais/types.ts` — the `AisConnection` interface: discover orchestrations + invoke one.
- `src/ais/mock.ts` — offline AIS: four orchestrations over in-memory E1 tables, including
  availability checks, commitment updates, and AIS-style `OrchestrationException` payloads.
- `src/ais/real.ts` — the same interface against a live AIS REST surface.
- `src/mcp-server.ts` — the MCP server (official `@modelcontextprotocol/sdk`, stdio transport).
  Calls `discoverOrchestrations()` at startup and registers one MCP tool per orchestration, with
  a Zod input schema generated from the discovery metadata.
- `src/web/mcp-stdio-client.ts` — a deliberately minimal hand-rolled MCP client: the inspector
  exists to show the raw JSON-RPC wire traffic, so every message is captured verbatim.
- `src/web/server.ts` + `src/web/index.html` — Bun web server that spawns the MCP server as a
  child process, bridges `tools/list` / `tools/call`, and renders tools, an invoke form, results,
  and the traffic log.

## API

```bash
curl -s localhost:9400/api/state | head -50
curl -s -X POST localhost:9400/api/call -H 'Content-Type: application/json' \
  -d '{"tool":"ORCH_GetItemAvailability","args":{"szItemNumber":"210","szBranchPlant":"30"}}'
```
