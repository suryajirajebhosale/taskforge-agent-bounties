import type { Metadata } from "next";
import { AmbientGlow } from "@/components/AmbientGlow";
import { PostFlow } from "@/components/post/PostFlow";

export const metadata: Metadata = {
  title: "Post a bounty — Merit",
  description:
    "Sign up, describe your work, let Merit clarify requirements, and approve a machine-checkable task report.",
};

export default function PostPage() {
  return (
    <AmbientGlow>
      <main className="min-h-screen">
        <PostFlow />
      </main>
    </AmbientGlow>
  );
}
