/**
 * Offline mock of the OpenAI Decisions API (POST /v1/decisions).
 *
 * Speaks the same wire format the PSAIOpenAIDecisions module sends and
 * expects, so the unmodified module works against it. Answers are
 * deterministic keyword/concept-overlap heuristics — no model, no network.
 */
import { jitter, matchCount } from "./lexicon";

type WireChoice = { value: string; description?: string };
type WireLevel = { label: string; description?: string };

type WireQuestion =
  | { type: "predicate"; instructions: string; name?: string }
  | { type: "choice"; instructions: string; name?: string; choices: WireChoice[] }
  | { type: "score"; instructions: string; name?: string; levels: WireLevel[] };

type WireRequest = {
  model?: string;
  input: unknown;
  questions: WireQuestion[];
};

const PORT = Number(process.env.PSAI_MOCK_PORT ?? 4100);

/** The module may send plain text, a JSON-serialized record, or message arrays. */
function inputAsText(input: unknown): string {
  if (typeof input === "string") return input;
  if (Array.isArray(input)) return input.map((part) => inputAsText(part)).join("\n");
  if (input && typeof input === "object") {
    if ("text" in input && typeof input.text === "string") return input.text;
    if ("content" in input) return inputAsText(input.content);
    return JSON.stringify(input);
  }
  return String(input ?? "");
}

function clamp(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value));
}

function probabilityFromHits(hits: number, seed: string): number {
  const base = hits >= 3 ? 0.93 : hits === 2 ? 0.81 : hits === 1 ? 0.62 : 0.07;
  return Number(clamp(base + jitter(seed), 0.01, 0.99).toFixed(3));
}

function answerQuestion(question: WireQuestion, text: string, index: number) {
  const name = question.name ?? `q${index}`;
  switch (question.type) {
    case "predicate": {
      const hits = matchCount(question.instructions, text);
      return {
        name,
        type: "predicate" as const,
        probability: probabilityFromHits(hits, name + text),
      };
    }
    case "choice": {
      let best = question.choices[0];
      let bestHits = -1;
      for (const choice of question.choices) {
        const hits = matchCount(`${choice.value} ${choice.description ?? ""}`, text);
        if (hits > bestHits) {
          best = choice;
          bestHits = hits;
        }
      }
      return { name, type: "choice" as const, choice: best.value };
    }
    case "score": {
      const hits = matchCount(question.instructions, text);
      const score = Math.min(question.levels.length - 1, hits);
      return { name, type: "score" as const, score };
    }
    default: {
      const exhausted: never = question;
      throw new Error(`Unsupported question type: ${JSON.stringify(exhausted)}`);
    }
  }
}

let requestCount = 0;

const server = Bun.serve({
  port: PORT,
  async fetch(request) {
    const url = new URL(request.url);
    if (url.pathname === "/health") {
      return Response.json({ status: "ok", service: "mock-decisions" });
    }
    if (url.pathname !== "/v1/decisions" || request.method !== "POST") {
      return Response.json({ error: { message: "Not found" } }, { status: 404 });
    }
    if (!(request.headers.get("authorization") ?? "").startsWith("Bearer ")) {
      return Response.json(
        { error: { message: "Missing bearer token (any non-empty value works in mock mode)" } },
        { status: 401 },
      );
    }

    const body = (await request.json()) as WireRequest;
    const text = inputAsText(body.input);
    const answers = body.questions.map((question, index) =>
      answerQuestion(question, text, index),
    );

    requestCount += 1;
    const preview = text.replaceAll("\n", " ").slice(0, 56);
    const summary = answers
      .map((a) =>
        a.type === "predicate"
          ? `${a.name}=p${a.probability}`
          : a.type === "choice"
            ? `${a.name}=${a.choice}`
            : `${a.name}=${a.score}`,
      )
      .join(" ");
    console.log(`[mock] #${requestCount} "${preview}…" -> ${summary}`);

    const inputTokens = Math.max(8, Math.round(text.length / 4));
    return Response.json({
      id: `dec_mock_${requestCount.toString().padStart(4, "0")}`,
      object: "decision",
      model: body.model ?? "gpt-6-luna",
      answers,
      usage: {
        input_tokens: inputTokens,
        output_tokens: answers.length * 6,
        total_tokens: inputTokens + answers.length * 6,
      },
    });
  },
});

console.log(`[mock] Decisions API listening on http://127.0.0.1:${server.port}/v1/decisions`);
