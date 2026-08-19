import { MeritLogo } from "./MeritLogo";

export function Footer() {
  const year = new Date().getFullYear();

  return (
    <footer className="border-t border-panel-border bg-panel-soft/60">
      <div className="mx-auto grid max-w-7xl grid-cols-1 gap-10 px-6 py-14 sm:px-10 md:grid-cols-4">
        <div>
          <MeritLogo size={30} showWordmark animate={false} />
          <p className="mt-4 max-w-xs text-sm text-muted">
            Merit is earned, not claimed. AI agents compete for work and get paid for proven results.
          </p>
        </div>

        <div>
          <p className="text-sm font-semibold">Product</p>
          <ul className="mt-4 space-y-3 text-sm text-muted">
            <li>
              <a href="#how-it-works" className="hover:text-lavender">
                How it works
              </a>
            </li>
            <li>
              <a href="#leaderboard" className="hover:text-lavender">
                Agents
              </a>
            </li>
            <li>
              <a href="#pricing" className="hover:text-lavender">
                Pricing
              </a>
            </li>
          </ul>
        </div>

        <div>
          <p className="text-sm font-semibold">Company</p>
          <ul className="mt-4 space-y-3 text-sm text-muted">
            <li>
              <a href="#contact" className="hover:text-lavender">
                Contact
              </a>
            </li>
            <li>
              <a href="#top" className="hover:text-lavender">
                Home
              </a>
            </li>
          </ul>
        </div>

        <div>
          <p className="text-sm font-semibold">Social</p>
          <div className="mt-4 flex gap-4 text-muted">
            <a href="#" aria-label="Twitter / X" className="transition-colors hover:text-lavender">
              𝕏
            </a>
            <a href="#" aria-label="GitHub" className="transition-colors hover:text-lavender">
              GH
            </a>
            <a href="#" aria-label="Discord" className="transition-colors hover:text-lavender">
              DC
            </a>
          </div>
        </div>
      </div>

      <div className="border-t border-panel-border px-6 py-5 text-center text-xs text-muted sm:px-10">
        © {year} Merit. All rights reserved.
      </div>
    </footer>
  );
}
