/** Compact score bar for assessment dimensions. */

interface Props {
  label: string;
  score: number; // 0.0 – 1.0
  explanation?: string;
}

function scoreColor(score: number): string {
  if (score >= 0.8) return "bg-emerald-500";
  if (score >= 0.55) return "bg-amber-400";
  return "bg-red-400";
}

function scoreLabel(score: number): string {
  if (score >= 0.8) return "Strong";
  if (score >= 0.55) return "Moderate";
  if (score >= 0.3) return "Weak";
  return "Very Low";
}

export function ScoreBar({ label, score, explanation }: Props) {
  const pct = Math.round(score * 100);
  return (
    <div>
      <div className="flex items-center justify-between text-xs">
        <span className="font-medium text-ink">{label}</span>
        <span className="font-mono text-ink-soft">
          {pct}% &middot; {scoreLabel(score)}
        </span>
      </div>
      <div className="mt-1 h-1.5 w-full rounded-full bg-line">
        <div
          className={`h-full rounded-full transition-all duration-500 ${scoreColor(score)}`}
          style={{ width: `${pct}%` }}
          role="progressbar"
          aria-valuenow={pct}
          aria-valuemin={0}
          aria-valuemax={100}
        />
      </div>
      {explanation && <p className="mt-1 text-xs leading-snug text-ink-soft">{explanation}</p>}
    </div>
  );
}
