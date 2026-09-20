import type { Reading } from "@/lib/types";

export const TARGET_DEVICE_ID = "fridge-sensor-01";
export const POLL_INTERVAL_MS = 5_000;
export const STALE_AFTER_MS = 2 * 60 * 1_000;

// Room-temperature hackathon setting. The production food-safety limit is 40°F.
export const DEMO_TEMP_MAX_F = 80;
export const TEMP_ATTENTION_START_F = DEMO_TEMP_MAX_F - 3;
export const DOOR_OPEN_TOO_LONG_MS = 2 * 60 * 1_000;

export function getReadingAgeMs(reading: Reading, nowMs: number): number {
  return Math.max(0, nowMs - new Date(reading.timestamp).getTime());
}

export function findDoorOpenedAt(readings: Reading[]): string | null {
  const newestFirst = [...readings].sort(
    (a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime(),
  );

  if (!newestFirst[0]?.door_open) return null;

  let openedAt = newestFirst[0].timestamp;
  for (const reading of newestFirst) {
    if (!reading.door_open) break;
    openedAt = reading.timestamp;
  }

  return openedAt;
}

export function getOverallStatus(
  reading: Reading,
  nowMs: number,
  doorOpenedAt: string | null,
) {
  if (getReadingAgeMs(reading, nowMs) > STALE_AFTER_MS) {
    return {
      kind: "unknown" as const,
      label: "Status unknown",
      summary: "FridgeGuard may be offline",
    };
  }

  const doorOpenMs =
    reading.door_open && doorOpenedAt
      ? Math.max(0, nowMs - new Date(doorOpenedAt).getTime())
      : 0;

  if (reading.temperature_f > DEMO_TEMP_MAX_F) {
    return {
      kind: "danger" as const,
      label: "Needs attention",
      summary: "The temperature is above the demo limit",
    };
  }

  if (doorOpenMs >= DOOR_OPEN_TOO_LONG_MS) {
    return {
      kind: "danger" as const,
      label: "Needs attention",
      summary: "The door has been open too long",
    };
  }

  if (reading.door_open) {
    return {
      kind: "attention" as const,
      label: "Attention soon",
      summary: "The door is currently open",
    };
  }

  if (reading.temperature_f > TEMP_ATTENTION_START_F) {
    return {
      kind: "attention" as const,
      label: "Attention soon",
      summary: "The temperature is nearing the demo limit",
    };
  }

  return {
    kind: "good" as const,
    label: "All good",
    summary: "No check is needed right now",
  };
}

export function formatDuration(milliseconds: number): string {
  const totalSeconds = Math.max(0, Math.floor(milliseconds / 1_000));
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${minutes}m ${seconds.toString().padStart(2, "0")}s`;
}

export function formatRelativeTime(timestamp: string, nowMs: number): string {
  const seconds = Math.max(
    0,
    Math.floor((nowMs - new Date(timestamp).getTime()) / 1_000),
  );

  if (seconds < 5) return "just now";
  if (seconds < 60) return `${seconds} seconds ago`;

  const minutes = Math.floor(seconds / 60);
  if (minutes === 1) return "1 minute ago";
  if (minutes < 60) return `${minutes} minutes ago`;

  const hours = Math.floor(minutes / 60);
  if (hours === 1) return "1 hour ago";
  if (hours < 24) return `${hours} hours ago`;

  const days = Math.floor(hours / 24);
  return days === 1 ? "1 day ago" : `${days} days ago`;
}

export function formatReadingTime(timestamp: string): string {
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
    second: "2-digit",
  }).format(new Date(timestamp));
}
