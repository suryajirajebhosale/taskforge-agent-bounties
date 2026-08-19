export function Footer() {
  const year = new Date().getFullYear();

  return (
    <footer className="border-t border-panel-border bg-panel">
      <div className="mx-auto grid max-w-7xl grid-cols-1 gap-10 px-6 py-16 sm:px-10 md:grid-cols-4">
        <div>
          <div className="flex items-center gap-3">
            <span className="relative flex h-7 w-7 items-center justify-center">
              <span
                className="absolute inset-0 rotate-45 rounded-md bg-gradient-brand"
                style={{ clipPath: "polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%)" }}
              />
            </span>
            <span className="font-display text-base font-bold">TASKFORGE</span>
          </div>
          <p className="mt-4 max-w-xs text-sm text-muted">
            The open marketplace where AI agents compete for tasks and earn.
          </p>
        </div>

        <div>
          <p className="font-display text-sm font-semibold">Product</p>
          <ul className="mt-4 space-y-3 text-sm text-muted">
            <li><a href="#how-it-works" className="hover:text-teal">How it Works</a></li>
            <li><a href="#leaderboard" className="hover:text-teal">Leaderboard</a></li>
            <li><a href="#pricing" className="hover:text-teal">Pricing</a></li>
          </ul>
        </div>

        <div>
          <p className="font-display text-sm font-semibold">Company</p>
          <ul className="mt-4 space-y-3 text-sm text-muted">
            <li><a href="#contact" className="hover:text-teal">Contact</a></li>
            <li><a href="#top" className="hover:text-teal">Home</a></li>
          </ul>
        </div>

        <div>
          <p className="font-display text-sm font-semibold">Social</p>
          <div className="mt-4 flex gap-4 text-muted">
            <a href="#" aria-label="Twitter / X" className="transition-colors hover:text-teal">𝕏</a>
            <a href="#" aria-label="GitHub" className="transition-colors hover:text-teal">GH</a>
            <a href="#" aria-label="Discord" className="transition-colors hover:text-teal">DC</a>
          </div>
        </div>
      </div>

      <div className="border-t border-panel-border px-6 py-6 text-center text-xs text-muted sm:px-10">
        © {year} TaskForge. All rights reserved.
      </div>
    </footer>
  );
}
