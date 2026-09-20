export type Reading = {
  id: number;
  device_id: string;
  timestamp: string;
  temperature_f: number;
  door_open: boolean;
};

export type OverallStatus = "good" | "attention" | "danger" | "unknown";
