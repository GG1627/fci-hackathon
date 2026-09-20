import type { OverallStatus, Reading, StatusResponse } from "@/lib/types";

export const POLL_INTERVAL_MS = 5_000;
export const IMAGE_POLL_INTERVAL_MS = 30_000;

export type DisplayStatus = {
  kind: OverallStatus;
  label: string;
  summary: string;
};

export function getDisplayStatus(
  apiStatus: StatusResponse | null,
  reading: Reading,
): DisplayStatus {
  if (!apiStatus || apiStatus.health_level === "unknown") {
    return {
      kind: "unknown",
      label: "Status unknown",
      summary: apiStatus?.message ?? "The Pi health check is unavailable",
    };
  }

  if (apiStatus.health_level === "critical") {
    return {
      kind: "danger",
      label: "Needs attention",
      summary: apiStatus.message,
    };
  }

  if (apiStatus.health_level === "warning" || reading.door_open) {
    return {
      kind: "attention",
      label:
        apiStatus.health_level === "warning" ? "Check the fridge" : "Door open",
      summary:
        apiStatus.health_level === "warning"
          ? apiStatus.message
          : "The door is currently open",
    };
  }

  return {
    kind: "good",
    label: "All good",
    summary: apiStatus.message,
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
