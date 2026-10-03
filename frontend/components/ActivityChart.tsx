"use client";

import type { DailyActivity } from "@/lib/types";

const WIDTH = 600;
const HEIGHT = 160;
const LABEL_SPACE = 24;
const BAR_AREA_HEIGHT = HEIGHT - LABEL_SPACE;

function formatShortDate(iso: string): string {
  const [, month, day] = iso.split("-");
  const names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  return `${names[Number(month) - 1]} ${Number(day)}`;
}

// Color encodes that day's accuracy, not just volume -- a tall rust bar (lots of
// attempts, mostly wrong) is a different signal than a tall sage one, and that
// distinction is the whole point of showing this next to a raw attempt count.
function barColor(attempts: number, correct: number): string {
  if (attempts === 0) return "#DCE3D6"; // line
  const accuracy = correct / attempts;
  if (accuracy >= 0.7) return "#4C7A63"; // sage
  if (accuracy >= 0.4) return "#D9A441"; // accent
  return "#A5432E"; // rust
}

export function ActivityChart({ data }: { data: DailyActivity[] }) {
  const totalAttempts = data.reduce((sum, d) => sum + d.attempts, 0);
  const totalCorrect = data.reduce((sum, d) => sum + d.correct, 0);
  const maxAttempts = Math.max(1, ...data.map((d) => d.attempts));
  const n = Math.max(1, data.length);
  const slot = WIDTH / n;
  const barWidth = slot * 0.7;

  const accuracyLabel = totalAttempts > 0 ? `${Math.round((totalCorrect / totalAttempts) * 100)}% correct` : "no activity yet";
  const summary = `Practice activity over the last ${data.length} days: ${totalAttempts} question${
    totalAttempts === 1 ? "" : "s"
  } answered, ${accuracyLabel}.`;

  if (totalAttempts === 0) {
    return <p className="text-sm text-ink-muted">No practice activity in this window yet.</p>;
  }

  const firstLabel = data[0]?.date;
  const lastLabel = data[data.length - 1]?.date;
  const midIndex = Math.floor((data.length - 1) / 2);
  const midLabel = data[midIndex]?.date;

  return (
    <div>
      <svg
        role="img"
        aria-label={summary}
        viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
        className="h-auto w-full"
        preserveAspectRatio="none"
      >
        {data.map((d, i) => {
          const barHeight = (d.attempts / maxAttempts) * (BAR_AREA_HEIGHT - 4);
          const x = i * slot + (slot - barWidth) / 2;
          const y = BAR_AREA_HEIGHT - barHeight;
          return <rect key={d.date} x={x} y={y} width={barWidth} height={Math.max(barHeight, 1)} fill={barColor(d.attempts, d.correct)} />;
        })}
        <line x1={0} y1={BAR_AREA_HEIGHT} x2={WIDTH} y2={BAR_AREA_HEIGHT} stroke="#DCE3D6" strokeWidth={1} />
        {firstLabel && (
          <text x={0} y={HEIGHT - 6} fontSize={11} fill="#55655C">
            {formatShortDate(firstLabel)}
          </text>
        )}
        {midLabel && data.length > 6 && (
          <text x={WIDTH / 2} y={HEIGHT - 6} fontSize={11} fill="#55655C" textAnchor="middle">
            {formatShortDate(midLabel)}
          </text>
        )}
        {lastLabel && (
          <text x={WIDTH} y={HEIGHT - 6} fontSize={11} fill="#55655C" textAnchor="end">
            {formatShortDate(lastLabel)}
          </text>
        )}
      </svg>
      <p className="mt-2 text-sm text-ink-muted">
        {totalAttempts} question{totalAttempts === 1 ? "" : "s"} answered, {accuracyLabel}
      </p>
    </div>
  );
}
