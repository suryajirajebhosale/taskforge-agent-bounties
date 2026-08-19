export function SectionEyebrow({ label }: { label: string }) {
  return (
    <div className="flex items-center gap-4">
      <span className="font-display text-xs sm:text-sm font-semibold tracking-[0.35em] text-teal uppercase">
        {label}
      </span>
      <span className="tick-divider h-px flex-1" aria-hidden />
    </div>
  );
}
