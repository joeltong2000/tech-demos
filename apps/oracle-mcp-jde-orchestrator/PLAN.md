# Plan: Oracle MCP for JDE Orchestrator (AIS-native)

Written per `skills/project-planning/SKILL.md`. Inspired by Oracle's announcement of an
MCP server for JD Edwards EnterpriseOne Orchestrator
([LinkedIn post](https://www.linkedin.com/posts/barizon_jdedwards-innova9-jdedwards-activity-7507881685003161601-OhnO)).

## 1. Goal

Show the core idea of Oracle's **AIS-native MCP server for JDE Orchestrator**: orchestrations
published on a JDE E1 AIS server are *discovered at startup* and exposed 1:1 as MCP tools, so any
MCP client (Claude Desktop, an agent framework, …) can call live JDE business logic. The happy
path: a reviewer opens a web "MCP inspector" UI, sees four JDE orchestrations surfaced as MCP
tools (customer search, item availability, sales order create, order status), invokes one, and
watches the raw MCP JSON-RPC traffic plus the AIS-style orchestration response.

## 2. Constraints

- **Bun + TypeScript** (monorepo standard). MCP server built on the official
  `@modelcontextprotocol/sdk`; the web bridge speaks minimal hand-rolled JSON-RPC over the MCP
  server's stdio so the UI can display every raw request/response byte.
- No real JDE instance is available, so an in-process **mock AIS layer** implements the same
  interface as the real AIS REST client: orchestration discovery + invocation against in-memory
  E1 tables (F0101 address book, F41021 item availability, F4211 sales orders), returning
  AIS-shaped responses with JDE field names (`szOrderNumber`, `mnQuantityAvailable`, …).
- Real credentials go in `.env.example` only (`JDE_AIS_BASE_URL`, `JDE_AIS_USERNAME`,
  `JDE_AIS_PASSWORD`, `JDE_AIS_ENVIRONMENT`, `JDE_AIS_ROLE`); with them set, the same MCP server
  targets a real AIS server via `/jderest/v2/tokenrequest` + `/jderest/v2/orchestrator/<name>`.
- Out of scope: writing back to a real JDE instance, orchestration *authoring*, AIS token
  refresh/expiry handling, authentication on the demo web UI.

## 3. Steps

1. Scaffold `apps/oracle-mcp-jde-orchestrator/` with Bun; add `@modelcontextprotocol/sdk`.
2. Define the AIS connection interface + mock implementation (in-memory E1 tables, four
   orchestrations with discovery metadata and realistic AIS response shapes).
3. Add the real-AIS REST client selected when `JDE_AIS_BASE_URL` is set.
4. Build the MCP stdio server: discover orchestrations at startup, register one MCP tool per
   orchestration with an input schema generated from the discovery metadata.
5. Build the web bridge/UI: Bun server spawns the MCP server as a child process, performs the
   MCP handshake, proxies `tools/list` / `tools/call`, and logs raw JSON-RPC traffic; a
   single-page UI renders the tool surface, an invoke form, results, and the traffic log.
6. Verify the happy path offline (`bun run dev`, invoke each tool, confirm mock E1 data flows
   through MCP end to end).
7. Capture validation artifacts (screenshot + short video of the running UI) and attach to the PR.

## 4. Success criteria

- `cd apps/oracle-mcp-jde-orchestrator && bun install && bun run dev` starts the UI on
  http://localhost:9400 with no `.env` present (offline mock mode, shown by a header badge).
- The tool list shows four MCP tools discovered from the (mock) AIS orchestration catalog.
- Invoking `ORCH_CreateSalesOrder` returns a new `szOrderNumber` and the traffic log shows the
  `tools/call` JSON-RPC request and response; `ORCH_GetOrderStatus` then finds that order.
- `bun run mcp` runs the bare stdio MCP server, usable from any MCP client (documented in README).
- PR includes at least one screenshot and one video of the running app.
