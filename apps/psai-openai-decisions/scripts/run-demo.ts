/**
 * Happy-path orchestrator: start the mock Decisions API, wait until it is
 * healthy, run the PowerShell triage demo against it, then shut it down.
 * In real mode (PSAI_MODE=real + OPENAI_API_KEY) the mock is skipped.
 */
import { resolve } from "node:path";

const appRoot = resolve(import.meta.dir, "..");
const port = process.env.PSAI_MOCK_PORT ?? "4100";
const realMode = process.env.PSAI_MODE === "real" && !!process.env.OPENAI_API_KEY;

let mock: Bun.Subprocess | null = null;

if (!realMode) {
  mock = Bun.spawn(["bun", "run", resolve(appRoot, "mock/server.ts")], {
    env: { ...process.env, PSAI_MOCK_PORT: port },
    stdout: "inherit",
    stderr: "inherit",
  });

  const healthUrl = `http://127.0.0.1:${port}/health`;
  let healthy = false;
  for (let attempt = 0; attempt < 50; attempt += 1) {
    try {
      const response = await fetch(healthUrl);
      if (response.ok) {
        healthy = true;
        break;
      }
    } catch {
      // server not up yet
    }
    await Bun.sleep(100);
  }
  if (!healthy) {
    mock.kill();
    console.error(`Mock Decisions API never became healthy at ${healthUrl}`);
    process.exit(1);
  }
}

const demo = Bun.spawn(["pwsh", "-NoLogo", "-File", resolve(appRoot, "demo/TicketTriage.ps1")], {
  env: { ...process.env, PSAI_MOCK_PORT: port },
  stdout: "inherit",
  stderr: "inherit",
});

const exitCode = await demo.exited;
mock?.kill();
process.exit(exitCode);
