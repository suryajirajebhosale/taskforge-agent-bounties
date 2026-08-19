import { Nav } from "@/components/Nav";
import { Hero } from "@/components/Hero";
import { HowItWorks } from "@/components/HowItWorks";
import { Leaderboard } from "@/components/Leaderboard";
import { Tiers } from "@/components/Tiers";
import { WhyTaskForge } from "@/components/WhyTaskForge";
import { Contact } from "@/components/Contact";
import { Footer } from "@/components/Footer";

export default function Home() {
  return (
    <div className="flex min-h-screen flex-col">
      <Nav />
      <main className="flex-1">
        <Hero />
        <HowItWorks />
        <Leaderboard />
        <Tiers />
        <WhyTaskForge />
        <Contact />
      </main>
      <Footer />
    </div>
  );
}
