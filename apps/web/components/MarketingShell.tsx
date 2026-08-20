import { AmbientGlow } from "@/components/AmbientGlow";
import { Nav } from "@/components/Nav";
import { Footer } from "@/components/Footer";

export function MarketingShell({ children }: { children: React.ReactNode }) {
  return (
    <AmbientGlow>
      <div className="flex min-h-screen flex-col">
        <Nav />
        <main className="flex-1 pt-24">{children}</main>
        <Footer />
      </div>
    </AmbientGlow>
  );
}
