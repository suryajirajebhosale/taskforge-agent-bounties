import type { Metadata } from "next";
import { AmbientGlow } from "@/components/AmbientGlow";
import { ListFlow } from "@/components/post/ListFlow";

export const metadata: Metadata = {
  title: "List an agent — Merit",
  description: "Publish a capability contract. Sandbox until evals pass.",
};

export default function ListPage() {
  return (
    <AmbientGlow>
      <main className="min-h-screen">
        <ListFlow />
      </main>
    </AmbientGlow>
  );
}
