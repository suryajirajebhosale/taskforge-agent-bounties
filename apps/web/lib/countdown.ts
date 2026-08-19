/** Next Sunday 00:00 local time — matches the backend's default Sunday-anchored
 * weekly leaderboard period (see services/reputation_service/period.py). */
export function nextSundayMidnight(from: Date = new Date()): Date {
  const result = new Date(from);
  const daysUntilSunday = (7 - result.getDay()) % 7 || 7;
  result.setDate(result.getDate() + daysUntilSunday);
  result.setHours(0, 0, 0, 0);
  return result;
}

export function formatCountdown(msRemaining: number): string {
  if (msRemaining <= 0) return "00d 00h 00m 00s";
  const totalSeconds = Math.floor(msRemaining / 1000);
  const days = Math.floor(totalSeconds / 86400);
  const hours = Math.floor((totalSeconds % 86400) / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;
  return `${String(days).padStart(2, "0")}d ${String(hours).padStart(2, "0")}h ${String(minutes).padStart(2, "0")}m ${String(seconds).padStart(2, "0")}s`;
}
