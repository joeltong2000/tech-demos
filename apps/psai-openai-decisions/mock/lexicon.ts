/**
 * Concept groups used by the mock scorer. Any token in a group counts as a
 * match for any other token in the same group, which is what lets a question
 * about "billing" match a ticket that says "charged twice".
 */
export const CONCEPT_GROUPS: Record<string, string[]> = {
  billing: [
    "billing", "bill", "billed", "charge", "charged", "charges", "invoice",
    "invoiced", "refund", "refunded", "payment", "paid", "pay", "price",
    "pricing", "subscription", "renewal", "overcharged", "duplicate", "receipt",
  ],
  technical: [
    "technical", "crash", "crashed", "crashes", "error", "errors", "bug",
    "bugs", "fail", "fails", "failed", "failure", "exception", "timeout",
    "broken", "break", "integration", "export", "sync", "api", "webhook",
    "defect", "regression",
  ],
  account: [
    "account", "login", "log", "password", "locked", "lockout", "sign",
    "signin", "signing", "access", "2fa", "mfa", "authenticator", "reset",
    "credentials", "username",
  ],
  urgency: [
    "urgent", "urgently", "immediately", "asap", "critical", "outage", "down",
    "production", "blocked", "blocking", "blocker", "deadline", "emergency",
    "launch", "today", "escalate", "severe", "unusable",
  ],
  calm: [
    "whenever", "minor", "curious", "wondering", "question", "someday",
    "eventually", "rush", "cosmetic", "suggestion", "idea",
  ],
  damage: [
    "damaged", "damage", "cracked", "shattered", "dent", "dented",
    "defective", "scratched",
  ],
};

const STOPWORDS = new Set([
  "the", "a", "an", "is", "are", "was", "were", "be", "been", "being", "do",
  "does", "did", "this", "that", "these", "those", "it", "its", "of", "to",
  "in", "on", "for", "from", "with", "and", "or", "not", "no", "yes", "has",
  "have", "had", "will", "would", "should", "can", "could", "our", "your",
  "their", "my", "we", "you", "they", "i", "me", "us", "at", "by", "as",
  "right", "now", "please", "customer", "request", "input", "item", "report",
  "reports", "about", "how", "what", "which", "who", "does", "true", "false",
]);

/** Lowercase, split, drop stopwords, and lightly stem (trailing s/ed/ing). */
export function tokenize(text: string): string[] {
  return text
    .toLowerCase()
    .split(/[^a-z0-9]+/)
    .filter((t) => t.length > 1 && !STOPWORDS.has(t));
}

const tokenToConcepts = new Map<string, string[]>();
for (const [concept, words] of Object.entries(CONCEPT_GROUPS)) {
  for (const word of words) {
    const list = tokenToConcepts.get(word) ?? [];
    list.push(concept);
    tokenToConcepts.set(word, list);
  }
}

/**
 * Number of distinct input tokens that match the question, either literally
 * or through a shared concept group. This is the single signal every mock
 * answer is derived from: more matching evidence in the input means a higher
 * probability or score, and the best-matching choice wins.
 */
export function matchCount(questionText: string, inputText: string): number {
  const questionTokens = new Set(tokenize(questionText));
  const questionConcepts = new Set<string>();
  for (const token of questionTokens) {
    for (const concept of tokenToConcepts.get(token) ?? []) {
      questionConcepts.add(concept);
    }
  }

  let hits = 0;
  for (const token of new Set(tokenize(inputText))) {
    const direct = questionTokens.has(token);
    const viaConcept = (tokenToConcepts.get(token) ?? []).some((concept) =>
      questionConcepts.has(concept),
    );
    if (direct || viaConcept) hits += 1;
  }
  return hits;
}

/** Deterministic jitter in [-0.03, 0.03] so probabilities look organic. */
export function jitter(seed: string): number {
  let hash = 2166136261;
  for (let i = 0; i < seed.length; i += 1) {
    hash ^= seed.charCodeAt(i);
    hash = Math.imul(hash, 16777619);
  }
  return ((hash >>> 0) % 61) / 1000 - 0.03;
}
