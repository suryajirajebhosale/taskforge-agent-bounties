import { NextResponse } from "next/server";
import { clarifyBounty } from "@/lib/bounty-ai";
import type { ChatMessage } from "@/lib/bounty-types";

export async function POST(req: Request) {
  try {
    const body = await req.json();
    const brief = String(body.brief ?? "").trim();
    const history = (body.history ?? []) as ChatMessage[];

    if (!brief) {
      return NextResponse.json({ error: "Brief is required" }, { status: 400 });
    }

    const result = await clarifyBounty(brief, history);
    return NextResponse.json(result);
  } catch {
    return NextResponse.json({ error: "Clarify failed" }, { status: 500 });
  }
}
