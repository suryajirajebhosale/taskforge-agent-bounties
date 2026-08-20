import type { Metadata } from "next";
import { AmbientGlow } from "@/components/AmbientGlow";
import { PostChoice } from "@/components/post/PostChoice";

export const metadata: Metadata = {
  title: "Get started — Merit",
  description: "Run a job against a locked specialization contract, or list the agent you already built.",
};

export default function PostPage() {
  return (
    <AmbientGlow>
      <main className="min-h-screen">
        <PostChoice />
      </main>
    </AmbientGlow>
  );
}
