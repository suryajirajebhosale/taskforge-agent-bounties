import type { ChatMessage, ClarifyResponse, TaskReport } from "@/lib/bounty-types";

function hasOpenAI() {
  return Boolean(process.env.OPENAI_API_KEY);
}

async function openaiJson<T>(system: string, user: string): Promise<T | null> {
  if (!hasOpenAI()) return null;
  const res = await fetch("https://api.openai.com/v1/chat/completions", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${process.env.OPENAI_API_KEY}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      model: process.env.OPENAI_MODEL ?? "gpt-4o-mini",
      temperature: 0.4,
      response_format: { type: "json_object" },
      messages: [
        { role: "system", content: system },
        { role: "user", content: user },
      ],
    }),
  });
  if (!res.ok) return null;
  const data = await res.json();
  const text = data.choices?.[0]?.message?.content;
  if (!text) return null;
  return JSON.parse(text) as T;
}

export async function clarifyBounty(
  brief: string,
  history: ChatMessage[],
): Promise<ClarifyResponse> {
  const transcript = history.map((m) => `${m.role}: ${m.content}`).join("\n");

  const ai = await openaiJson<ClarifyResponse>(
    `You are Merit's bounty scoping assistant. Ask short clarifying questions so a bounty can be verified automatically later.
Return JSON: { "reply": string, "readyForReport": boolean }.
Rules:
- Ask at most 2 questions per turn.
- Focus on deliverable format, quantity, quality bar, deadline, and budget if missing.
- Set readyForReport=true only when you have enough to draft a structured task report.
- Keep reply concise and professional.`,
    `Original brief:\n${brief}\n\nConversation so far:\n${transcript || "(none yet — ask first clarifying questions)"}`,
  );

  if (ai?.reply) return ai;

  // Deterministic demo fallback when no API key / API failure
  const turns = history.filter((m) => m.role === "user").length;
  if (turns === 0) {
    return {
      reply:
        "Got it. Two quick clarifiers before I draft the task report:\n\n1) What exact deliverable should agents submit (sheet, doc, repo link, ZIP)?\n2) How will we know it’s done — a hard count/format, or a quality bar too?",
      readyForReport: false,
    };
  }
  if (turns === 1) {
    return {
      reply:
        "Thanks. Last ones:\n\n1) What’s your target budget and deadline?\n2) Any must-have constraints (geography, tools, brand tone, exclusions)?",
      readyForReport: false,
    };
  }
  return {
    reply:
      "Perfect — I have enough to draft a Merit task report. Review it next, edit if needed, then approve to fund escrow.",
    readyForReport: true,
  };
}

export async function generateTaskReport(
  brief: string,
  history: ChatMessage[],
): Promise<TaskReport> {
  const transcript = history.map((m) => `${m.role}: ${m.content}`).join("\n");

  const ai = await openaiJson<TaskReport>(
    `You are Merit's rubric drafter. Create a structured bounty task report for an AI-agent marketplace.
Return JSON with keys:
title, summary, category, suggestedReward, deadline, deliverables (string[]),
objectiveCriteria ({field, rule}[]), subjectiveCriteria ({description, weight}[] with weights summing to 1),
acceptanceNotes.
Categories: Lead gen | Research | Build | Hiring | Content | Sales | Other.
suggestedReward like "$75". deadline like "3 days".`,
    `Brief:\n${brief}\n\nClarification transcript:\n${transcript}`,
  );

  if (ai?.title) {
    return ai;
  }

  const lower = brief.toLowerCase();
  const category = lower.includes("lead")
    ? "Lead gen"
    : lower.includes("research") || lower.includes("competitor")
      ? "Research"
      : lower.includes("hire") || lower.includes("recruit")
        ? "Hiring"
        : lower.includes("build") || lower.includes("code") || lower.includes("extension")
          ? "Build"
          : lower.includes("content") || lower.includes("copy") || lower.includes("script")
            ? "Content"
            : "Other";

  return {
    title: brief.trim().slice(0, 72) || "Untitled bounty",
    summary:
      history.find((m) => m.role === "user")?.content
        ? `${brief.trim()} Scoped from your answers so agents and the oracle share one definition of done.`
        : brief.trim(),
    category,
    suggestedReward: category === "Build" ? "$120" : category === "Research" ? "$75" : "$55",
    deadline: "3 days",
    deliverables: [
      "Primary deliverable in the agreed format",
      "Short method note (sources / approach)",
      "Ready for oracle verification",
    ],
    objectiveCriteria: [
      { field: "deliverable_present", rule: "== true" },
      { field: "format_valid", rule: "== true" },
      { field: "meets_quantity_or_scope", rule: "== true" },
    ],
    subjectiveCriteria: [
      { description: "Quality matches requester intent", weight: 0.5 },
      { description: "Clear, usable, and well organized", weight: 0.3 },
      { description: "No filler or obvious fabrication", weight: 0.2 },
    ],
    acceptanceNotes:
      "Escrow releases only after Merit’s oracle passes objective checks and subjective criteria above the confidence threshold.",
  };
}
