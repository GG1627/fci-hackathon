export type Reading = {
  id: number;
  device_id: string;
  timestamp: string;
  temperature_f: number;
  door_open: boolean;
};

export type OverallStatus = "good" | "attention" | "danger" | "unknown";

export type ApiStatus = "ok" | "stale" | "no_data";
export type HealthLevel = "good" | "warning" | "critical" | "unknown";

export type StatusResponse = {
  status: ApiStatus;
  age_seconds: number | null;
  reading: Reading | null;
  door_open_since: string | null;
  health_level: HealthLevel;
  conditions: string[];
  message: string;
};

export type ImageItem = {
  name: string;
  timestamp: string;
  url: string;
};

export type ImagesResponse = {
  latest: ImageItem | null;
  history: ImageItem[];
};
