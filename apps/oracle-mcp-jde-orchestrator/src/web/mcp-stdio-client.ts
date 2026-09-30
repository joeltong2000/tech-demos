/**
 * Minimal MCP client over a child process's stdio, hand-rolled on purpose:
 * the inspector UI's whole point is showing the raw JSON-RPC 2.0 traffic an
 * MCP client exchanges with the JDE Orchestrator MCP server, so every
 * message is captured verbatim into a traffic log. (The server side uses
 * the official @modelcontextprotocol/sdk.)
 */

import type { Subprocess } from "bun";

export interface TrafficEntry {
  direction: "client->server" | "server->client";
  at: string;
  message: unknown;
}

interface JsonRpcResponse {
  jsonrpc: "2.0";
  id?: number;
  result?: unknown;
  error?: { code: number; message: string; data?: unknown };
}

const MAX_TRAFFIC_ENTRIES = 200;

export class McpStdioClient {
  readonly traffic: TrafficEntry[] = [];
  serverInfo: unknown = null;

  private child: Subprocess<"pipe", "pipe", "inherit"> | null = null;
  private nextId = 1;
  private pending = new Map<
    number,
    { resolve: (value: unknown) => void; reject: (err: Error) => void }
  >();

  constructor(private readonly cmd: string[]) {}

  async start(): Promise<void> {
    this.child = Bun.spawn(this.cmd, {
      stdin: "pipe",
      stdout: "pipe",
      stderr: "inherit",
    });
    void this.readLoop();

    const initResult = (await this.request("initialize", {
      protocolVersion: "2025-03-26",
      capabilities: {},
      clientInfo: { name: "jde-mcp-web-inspector", version: "0.1.0" },
    })) as { serverInfo?: unknown };
    this.serverInfo = initResult.serverInfo ?? initResult;
    this.notify("notifications/initialized", {});
  }

  async listTools(): Promise<unknown> {
    return this.request("tools/list", {});
  }

  async callTool(name: string, args: Record<string, unknown>): Promise<unknown> {
    return this.request("tools/call", { name, arguments: args });
  }

  private record(direction: TrafficEntry["direction"], message: unknown): void {
    this.traffic.push({ direction, at: new Date().toISOString(), message });
    if (this.traffic.length > MAX_TRAFFIC_ENTRIES) {
      this.traffic.splice(0, this.traffic.length - MAX_TRAFFIC_ENTRIES);
    }
  }

  private send(message: Record<string, unknown>): void {
    if (!this.child) throw new Error("MCP server process not started");
    this.record("client->server", message);
    this.child.stdin.write(`${JSON.stringify(message)}\n`);
    this.child.stdin.flush();
  }

  private notify(method: string, params: Record<string, unknown>): void {
    this.send({ jsonrpc: "2.0", method, params });
  }

  private request(method: string, params: Record<string, unknown>): Promise<unknown> {
    const id = this.nextId++;
    const promise = new Promise<unknown>((resolve, reject) => {
      this.pending.set(id, { resolve, reject });
      setTimeout(() => {
        if (this.pending.delete(id)) reject(new Error(`MCP request '${method}' timed out`));
      }, 15_000);
    });
    this.send({ jsonrpc: "2.0", id, method, params });
    return promise;
  }

  private async readLoop(): Promise<void> {
    if (!this.child) return;
    const decoder = new TextDecoder();
    let buffer = "";
    for await (const chunk of this.child.stdout) {
      buffer += decoder.decode(chunk, { stream: true });
      let newline: number;
      while ((newline = buffer.indexOf("\n")) >= 0) {
        const line = buffer.slice(0, newline).trim();
        buffer = buffer.slice(newline + 1);
        if (line) this.handleLine(line);
      }
    }
  }

  private handleLine(line: string): void {
    let message: JsonRpcResponse;
    try {
      message = JSON.parse(line) as JsonRpcResponse;
    } catch {
      return; // not JSON-RPC; ignore
    }
    this.record("server->client", message);
    if (message.id === undefined) return;
    const waiter = this.pending.get(message.id);
    if (!waiter) return;
    this.pending.delete(message.id);
    if (message.error) {
      waiter.reject(new Error(`MCP error ${message.error.code}: ${message.error.message}`));
    } else {
      waiter.resolve(message.result);
    }
  }
}
