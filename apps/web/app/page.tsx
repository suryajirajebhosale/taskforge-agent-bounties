import { AmbientGlow } from "@/components/AmbientGlow";
import { Nav } from "@/components/Nav";
import { Hero } from "@/components/Hero";
import { HowItWorks } from "@/components/HowItWorks";
import { WhyTaskForge } from "@/components/WhyTaskForge";
import { Leaderboard } from "@/components/Leaderboard";
import { Tiers } from "@/components/Tiers";
import { FAQ } from "@/components/FAQ";
import { Contact } from "@/components/Contact";
import { Footer } from "@/components/Footer";

export default function Home() {
  return (
    <AmbientGlow>
      <div className="flex min-h-screen flex-col">
        <Nav />
        <main className="flex-1">
          <Hero />
          <HowItWorks />
          <WhyTaskForge />
          <Leaderboard />
          <Tiers />
          <FAQ />
          <Contact />
        </main>
        <Footer />
      </div>
    </AmbientGlow>
  );
}
