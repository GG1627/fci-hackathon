"use client";

/* eslint-disable @next/next/no-img-element */

import { useCallback, useEffect, useState } from "react";
import {
  AlertCircle,
  Camera,
  Check,
  ChevronDown,
  Clock3,
  DoorClosed,
  DoorOpen,
  ExternalLink,
  ImageOff,
  Info,
  MapPin,
  Radio,
  RefreshCw,
  Server,
  Thermometer,
  TriangleAlert,
  WifiOff,
  type LucideIcon,
} from "lucide-react";
import {
  formatDuration,
  formatReadingTime,
  formatRelativeTime,
  getDisplayStatus,
  IMAGE_POLL_INTERVAL_MS,
  POLL_INTERVAL_MS,
} from "@/lib/status";
import type {
  ImageItem,
  ImagesResponse,
  OverallStatus,
  Reading,
  StatusResponse,
} from "@/lib/types";

const statusStyles: Record<
  OverallStatus,
  {
    panel: string;
    badge: string;
    iconBox: string;
    dot: string;
    icon: LucideIcon;
  }
> = {
  good: {
    panel: "bg-emerald-50",
    badge: "bg-emerald-700 text-white",
    iconBox: "bg-emerald-700 text-white",
    dot: "bg-emerald-300",
    icon: Check,
  },
  attention: {
    panel: "bg-amber-50",
    badge: "bg-amber-400 text-amber-950",
    iconBox: "bg-amber-400 text-amber-950",
    dot: "bg-amber-900",
    icon: Info,
  },
  danger: {
    panel: "bg-red-50",
    badge: "bg-red-700 text-white",
    iconBox: "bg-red-700 text-white",
    dot: "bg-red-200",
    icon: TriangleAlert,
  },
  unknown: {
    panel: "bg-slate-100",
    badge: "bg-slate-700 text-white",
    iconBox: "bg-slate-700 text-white",
    dot: "bg-slate-300",
    icon: WifiOff,
  },
};

type DashboardState = {
  readings: Reading[];
  status: StatusResponse | null;
  readingsError: string | null;
  statusError: string | null;
  loading: boolean;
  lastFetchAt: number | null;
};

type ImageState = {
  data: ImagesResponse | null;
  error: string | null;
  loading: boolean;
};

type ConnectionState = "connecting" | "online" | "offline";

const initialState: DashboardState = {
  readings: [],
  status: null,
  readingsError: null,
  statusError: null,
  loading: true,
  lastFetchAt: null,
};

const initialImageState: ImageState = {
  data: null,
  error: null,
  loading: true,
};

function getApiBaseUrl(): string {
  const configuredUrl = process.env.NEXT_PUBLIC_FRIDGEGUARD_API_URL?.replace(
    /\/+$/,
    "",
  );
  return (
    configuredUrl || `${window.location.protocol}//${window.location.hostname}:8000`
  );
}

async function fetchApi<T>(path: string): Promise<T> {
  const apiBaseUrl = getApiBaseUrl();

  let response: Response;
  try {
    response = await fetch(`${apiBaseUrl}${path}`, {
      cache: "no-store",
    });
  } catch {
    throw new Error(
      `Unable to reach the Pi API at ${apiBaseUrl}. Confirm pi/api.py is running.`,
    );
  }

  const payload = (await response.json()) as T | { detail?: string };

  if (!response.ok) {
    const detail =
      payload && typeof payload === "object" && "detail" in payload
        ? payload.detail
        : null;
    throw new Error(detail ?? `The Pi API returned HTTP ${response.status}.`);
  }

  return payload as T;
}

async function fetchReadings(): Promise<Reading[]> {
  const payload = await fetchApi<Reading[]>("/api/readings?limit=50");

  if (!Array.isArray(payload)) {
    throw new Error("The Pi API returned an unexpected response.");
  }

  const preferredReadings = payload.filter(
    (reading) => reading.device_id === "fridge-sensor-01",
  );
  return preferredReadings.length > 0 ? preferredReadings : payload;
}

function fetchStatus(): Promise<StatusResponse> {
  return fetchApi<StatusResponse>("/api/status");
}

function fetchImages(): Promise<ImagesResponse> {
  return fetchApi<ImagesResponse>("/api/images");
}

export function FridgeDashboard() {
  const [state, setState] = useState<DashboardState>(initialState);
  const [imageState, setImageState] = useState<ImageState>(initialImageState);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedImageName, setSelectedImageName] = useState<string | null>(null);
  const [nowMs, setNowMs] = useState(() => Date.now());

  const loadSensorData = useCallback(async () => {
    const [readingsResult, statusResult] = await Promise.allSettled([
      fetchReadings(),
      fetchStatus(),
    ]);

    setState((current) => ({
      readings:
        readingsResult.status === "fulfilled"
          ? readingsResult.value
          : current.readings,
      status:
        statusResult.status === "fulfilled" ? statusResult.value : null,
      readingsError:
        readingsResult.status === "rejected"
          ? readingsResult.reason instanceof Error
            ? readingsResult.reason.message
            : "Unable to reach the Pi API."
          : null,
      statusError:
        statusResult.status === "rejected"
          ? "The Pi health evaluation is temporarily unavailable."
          : null,
      loading: false,
      lastFetchAt:
        readingsResult.status === "fulfilled" ? Date.now() : current.lastFetchAt,
    }));
  }, []);

  const loadImages = useCallback(async () => {
    try {
      const data = await fetchImages();
      setImageState({ data, error: null, loading: false });
    } catch (error) {
      setImageState((current) => ({
        ...current,
        error:
          error instanceof Error
            ? error.message
            : "Unable to load camera images.",
        loading: false,
      }));
    }
  }, []);

  const refreshAll = useCallback(async () => {
    setRefreshing(true);
    await Promise.allSettled([loadSensorData(), loadImages()]);
    setRefreshing(false);
  }, [loadImages, loadSensorData]);

  useEffect(() => {
    void loadSensorData();
    void loadImages();
    const pollingTimer = window.setInterval(
      () => void loadSensorData(),
      POLL_INTERVAL_MS,
    );
    const imagePollingTimer = window.setInterval(
      () => void loadImages(),
      IMAGE_POLL_INTERVAL_MS,
    );
    const clockTimer = window.setInterval(() => setNowMs(Date.now()), 1_000);

    return () => {
      window.clearInterval(pollingTimer);
      window.clearInterval(imagePollingTimer);
      window.clearInterval(clockTimer);
    };
  }, [loadImages, loadSensorData]);

  const reading = state.readings[0] ?? null;
  const doorOpenedAt = state.status?.door_open_since ?? null;
  const status = reading ? getDisplayStatus(state.status, reading) : null;
  const images = imageState.data
    ? [imageState.data.latest, ...imageState.data.history].filter(
        (image): image is ImageItem => image !== null,
      )
    : [];
  const selectedImage =
    images.find((image) => image.name === selectedImageName) ?? images[0] ?? null;
  const connectionState: ConnectionState = state.loading
    ? "connecting"
    : state.readingsError
      ? "offline"
      : "online";

  return (
    <main className="min-h-screen">
      <Header
        refreshing={refreshing}
        lastFetchAt={state.lastFetchAt}
        connectionState={connectionState}
        onRefresh={() => void refreshAll()}
      />

      <div className="mx-auto w-full max-w-6xl px-4 py-7 sm:px-7 sm:py-9 lg:px-8">
        {state.loading ? (
          <LoadingState />
        ) : state.readingsError && !reading ? (
          <ErrorState
            message={state.readingsError}
            onRetry={() => void refreshAll()}
          />
        ) : !reading ? (
          <EmptyState onRetry={() => void refreshAll()} />
        ) : (
          <DashboardContent
            reading={reading}
            doorOpenedAt={doorOpenedAt}
            nowMs={nowMs}
            status={status!}
            apiStatus={state.status}
            backgroundError={state.readingsError ?? state.statusError}
            images={images}
            selectedImage={selectedImage}
            imageError={imageState.error}
            imagesLoading={imageState.loading}
            onSelectImage={setSelectedImageName}
          />
        )}
      </div>
    </main>
  );
}

function Header({
  refreshing,
  lastFetchAt,
  connectionState,
  onRefresh,
}: {
  refreshing: boolean;
  lastFetchAt: number | null;
  connectionState: ConnectionState;
  onRefresh: () => void;
}) {
  const connection = {
    connecting: { label: "Connecting", dot: "bg-sky-500" },
    online: { label: "Auto-refresh on", dot: "bg-emerald-500" },
    offline: { label: "API unavailable", dot: "bg-red-500" },
  }[connectionState];

  return (
    <header className="border-b border-line bg-surface">
      <div className="mx-auto flex min-h-18 w-full max-w-6xl items-center justify-between gap-4 px-4 sm:px-7 lg:px-8">
        <div className="flex min-w-0 items-center gap-4">
          <div
            className="shrink-0 text-xl font-extrabold tracking-[-0.025em] text-brand sm:text-2xl"
            aria-label="Community Chill"
          >
            <span className="font-semibold text-sky-400">[</span> Community Chill{" "}
            <span className="font-semibold text-sky-400">]</span>
          </div>
          <div className="hidden h-8 w-px bg-line sm:block" />
          <div className="hidden min-w-0 sm:block">
            <p className="truncate text-sm font-semibold text-ink">
              Gainesville Community Fridge
            </p>
            <p className="mt-0.5 flex items-center gap-1 text-xs text-muted">
              <MapPin className="h-3.5 w-3.5" aria-hidden="true" /> Gainesville,
              Florida
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 sm:gap-3">
          <span
            className="hidden items-center gap-2 text-xs font-semibold text-muted sm:inline-flex"
            aria-live="polite"
            title={
              lastFetchAt
                ? `Last checked ${formatReadingTime(new Date(lastFetchAt).toISOString())}`
                : "Connecting"
            }
          >
            <span className="relative flex h-2 w-2">
              {connectionState === "online" && (
                <span
                  className={`live-pulse absolute inline-flex h-full w-full rounded-full ${connection.dot}`}
                />
              )}
              <span
                className={`relative inline-flex h-2 w-2 rounded-full ${connection.dot}`}
              />
            </span>
            {connection.label}
          </span>
          <button
            type="button"
            onClick={onRefresh}
            disabled={refreshing}
            className="inline-flex min-h-11 items-center justify-center gap-2 rounded-full bg-brand-deep px-4 py-2 text-sm font-bold text-white transition-colors hover:bg-ink focus-visible:outline-none focus-visible:ring-3 focus-visible:ring-focus disabled:cursor-wait disabled:opacity-65"
            title="Refresh sensor data"
          >
            <RefreshCw
              className={`h-4 w-4 ${refreshing ? "animate-spin" : ""}`}
              aria-hidden="true"
            />
            <span>Refresh</span>
          </button>
        </div>
      </div>
    </header>
  );
}

function DashboardContent({
  reading,
  doorOpenedAt,
  nowMs,
  status,
  apiStatus,
  backgroundError,
  images,
  selectedImage,
  imageError,
  imagesLoading,
  onSelectImage,
}: {
  reading: Reading;
  doorOpenedAt: string | null;
  nowMs: number;
  status: ReturnType<typeof getDisplayStatus>;
  apiStatus: StatusResponse | null;
  backgroundError: string | null;
  images: ImageItem[];
  selectedImage: ImageItem | null;
  imageError: string | null;
  imagesLoading: boolean;
  onSelectImage: (name: string) => void;
}) {
  const styles = statusStyles[status.kind];
  const StatusIcon = styles.icon;
  const stale = apiStatus?.status !== "ok";
  const doorDurationMs = doorOpenedAt
    ? Math.max(0, nowMs - new Date(doorOpenedAt).getTime())
    : 0;
  const temperatureHigh = apiStatus?.conditions.includes("TEMP_HIGH") ?? false;

  return (
    <>
      <section className="mb-6">
        <h1 className="text-3xl font-bold tracking-[-0.025em] text-ink sm:text-4xl">
          Gainesville Community Fridge
        </h1>
        <p className="mt-2 max-w-2xl text-base leading-7 text-muted">
          Live temperature, door, connection status, and camera views for volunteers.
        </p>
      </section>

      <section
        className={`rounded-panel p-5 shadow-panel sm:p-6 ${styles.panel}`}
        aria-labelledby="overall-status"
        aria-live="polite"
      >
        <div className="flex flex-col justify-between gap-5 sm:flex-row sm:items-center">
          <div className="flex items-start gap-4 sm:items-center">
            <div
              className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-xl ${styles.iconBox}`}
            >
              <StatusIcon
                className="h-6 w-6"
                strokeWidth={2.25}
                aria-hidden="true"
              />
            </div>
            <div>
              <p className="text-xs font-bold tracking-[0.12em] text-slate-600 uppercase">
                Current status
              </p>
              <h2
                id="overall-status"
                className="mt-0.5 text-2xl font-bold tracking-[-0.02em] text-ink sm:text-3xl"
              >
                {status.label}
              </h2>
              <p className="mt-1 text-sm font-medium text-slate-700 sm:text-base">
                {status.summary}
              </p>
            </div>
          </div>
          <div
            className={`inline-flex w-fit items-center gap-2 self-start rounded-full px-3.5 py-2 text-xs font-bold tracking-[0.06em] uppercase sm:self-auto ${styles.badge}`}
          >
            <span className="relative flex h-2 w-2">
              {status.kind === "good" && (
                <span
                  className={`live-pulse absolute inline-flex h-full w-full rounded-full ${styles.dot}`}
                />
              )}
              <span
                className={`relative inline-flex h-2 w-2 rounded-full ${styles.dot}`}
              />
            </span>
            {status.kind === "good" ? "Operating normally" : status.label}
          </div>
        </div>
      </section>

      {backgroundError && (
        <div
          className="mt-4 flex items-start gap-3 rounded-xl bg-amber-50 px-4 py-3 text-sm font-medium text-amber-950 shadow-sm"
          role="status"
        >
          <AlertCircle
            className="mt-0.5 h-4 w-4 shrink-0"
            aria-hidden="true"
          />
          Live refresh failed. Showing the most recent reading already loaded.
        </div>
      )}

      <section
        className="mt-4 overflow-hidden rounded-panel bg-surface shadow-panel"
        aria-labelledby="sensor-readings"
      >
        <div className="flex flex-col gap-1 border-b border-line px-5 py-4 sm:flex-row sm:items-center sm:justify-between sm:px-6">
          <h2 id="sensor-readings" className="text-base font-bold text-ink">
            Latest sensor reading
          </h2>
          <p className="text-sm text-muted">
            Recorded {formatRelativeTime(reading.timestamp, nowMs)}
          </p>
        </div>

        <div className="grid sm:grid-cols-2 xl:grid-cols-4">
          <MetricCard
            eyebrow="Temperature"
            icon={Thermometer}
            iconClass={
              stale
                ? "text-slate-500"
                : temperatureHigh
                  ? "text-red-700"
                  : "text-brand"
            }
            value={`${reading.temperature_f.toFixed(1)} °F`}
            detail={
              stale ? "Last recorded reading" : temperatureHigh ? "Warning" : "Safe"
            }
            detailClass={
              stale
                ? "text-slate-600"
                : temperatureHigh
                  ? "text-red-700"
                  : "text-emerald-700"
            }
            footer={
              stale
                ? "Current safety status unknown"
                : "Safety limit configured on the Pi"
            }
          />

          <MetricCard
            eyebrow="Door"
            icon={reading.door_open ? DoorOpen : DoorClosed}
            iconClass={
              stale
                ? "text-slate-500"
                : reading.door_open
                  ? "text-amber-700"
                  : "text-emerald-700"
            }
            value={reading.door_open ? "OPEN" : "CLOSED"}
            detail={
              stale
                ? "Last recorded state"
                : reading.door_open && doorOpenedAt
                  ? `Open for ${formatDuration(doorDurationMs)}`
                  : "Door is secured"
            }
            detailClass={
              stale
                ? "text-slate-600"
                : reading.door_open
                  ? "text-amber-700"
                  : "text-emerald-700"
            }
            footer={
              stale
                ? "Current door status unknown"
                : reading.door_open
                  ? "Close the door when possible"
                  : "No action needed"
            }
          />

          <MetricCard
            eyebrow="Last update"
            icon={stale ? WifiOff : Clock3}
            iconClass={stale ? "text-slate-600" : "text-brand"}
            value={formatRelativeTime(reading.timestamp, nowMs)}
            detail={
              stale
                ? "Community Chill may be offline"
                : formatReadingTime(reading.timestamp)
            }
            detailClass={stale ? "text-slate-700" : "text-muted"}
            footer={
              stale ? "Current status is unknown" : "Updates every few seconds"
            }
          />

          <MetricCard
            eyebrow="Device"
            icon={Server}
            iconClass={stale ? "text-slate-500" : "text-brand"}
            value={reading.device_id}
            valueClass="break-words text-xl"
            detail={stale ? "Last known sensor" : "Sensor connected"}
            detailClass={stale ? "text-slate-600" : "text-emerald-700"}
            footer="Gainesville Community Fridge"
          />
        </div>

        <details className="group border-t border-line">
          <summary className="flex min-h-13 cursor-pointer list-none items-center justify-between gap-4 px-5 py-3 text-sm font-semibold text-ink outline-none transition-colors hover:bg-surface-muted focus-visible:ring-3 focus-visible:ring-inset focus-visible:ring-focus sm:px-6">
            <span className="flex items-center gap-2">
              <Radio className="h-4 w-4 text-brand" aria-hidden="true" />
              Reading details
            </span>
            <ChevronDown
              className="h-4 w-4 transition-transform group-open:rotate-180"
              aria-hidden="true"
            />
          </summary>
          <dl className="grid gap-x-8 gap-y-4 border-t border-line bg-surface-muted px-5 py-4 text-sm sm:grid-cols-2 sm:px-6">
            <DebugItem label="Reading ID" value={String(reading.id)} />
            <DebugItem label="Sensor timestamp" value={reading.timestamp} />
          </dl>
        </details>
      </section>

      <CameraGallery
        images={images}
        selectedImage={selectedImage}
        error={imageError}
        loading={imagesLoading}
        nowMs={nowMs}
        onSelect={onSelectImage}
      />

      <p className="mt-5 text-center text-xs leading-5 text-muted">
        Community Chill checks sensor data every {POLL_INTERVAL_MS / 1_000}{" "}
        seconds and camera images every {IMAGE_POLL_INTERVAL_MS / 1_000} seconds.
      </p>
    </>
  );
}

function CameraGallery({
  images,
  selectedImage,
  error,
  loading,
  nowMs,
  onSelect,
}: {
  images: ImageItem[];
  selectedImage: ImageItem | null;
  error: string | null;
  loading: boolean;
  nowMs: number;
  onSelect: (name: string) => void;
}) {
  const selectedIsLatest = selectedImage?.name === images[0]?.name;

  return (
    <section
      className="mt-4 overflow-hidden rounded-panel bg-surface shadow-panel"
      aria-labelledby="camera-view"
    >
      <div className="flex flex-col gap-1 border-b border-line px-5 py-4 sm:flex-row sm:items-center sm:justify-between sm:px-6">
        <h2 id="camera-view" className="flex items-center gap-2 text-base font-bold text-ink">
          <Camera className="h-4 w-4 text-brand" aria-hidden="true" />
          Fridge camera
        </h2>
        {images[0] && (
          <p className="text-sm text-muted">
            Latest capture {formatRelativeTime(images[0].timestamp, nowMs)}
          </p>
        )}
      </div>

      {error && (
        <div
          className="flex items-start gap-3 border-b border-amber-200 bg-amber-50 px-5 py-3 text-sm font-medium text-amber-950 sm:px-6"
          role="status"
        >
          <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
          {images.length > 0
            ? "Camera refresh failed. Showing the images already loaded."
            : error}
        </div>
      )}

      {loading && !selectedImage ? (
        <div className="p-5 sm:p-6">
          <div className="skeleton aspect-video w-full rounded-xl" />
        </div>
      ) : !selectedImage ? (
        <div className="flex flex-col items-center px-6 py-12 text-center">
          <span className="mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-sky-50 text-brand">
            <ImageOff className="h-6 w-6" aria-hidden="true" />
          </span>
          <h3 className="text-lg font-bold text-ink">Waiting for a camera image</h3>
          <p className="mt-2 max-w-lg text-sm leading-6 text-muted">
            Images will appear here after the Pi captures and uploads its first
            photo.
          </p>
        </div>
      ) : (
        <>
          <div className="grid lg:grid-cols-[minmax(0,2fr)_minmax(16rem,1fr)]">
            <div className="bg-slate-950">
              <img
                src={selectedImage.url}
                alt={`Community fridge captured ${formatReadingTime(selectedImage.timestamp)}`}
                className="aspect-video h-full w-full object-cover"
              />
            </div>
            <div className="flex flex-col justify-center border-line p-5 lg:border-l lg:p-6">
              <p className="text-xs font-bold tracking-[0.1em] text-muted uppercase">
                {selectedIsLatest ? "Latest image" : "Previous image"}
              </p>
              <h3 className="mt-2 text-xl font-bold text-ink">
                {formatReadingTime(selectedImage.timestamp)}
              </h3>
              <p className="mt-2 text-sm leading-6 text-muted">
                Captured {formatRelativeTime(selectedImage.timestamp, nowMs)} by
                the Raspberry Pi Camera Module 3.
              </p>
              <a
                href={selectedImage.url}
                target="_blank"
                rel="noreferrer"
                className="mt-5 inline-flex min-h-11 w-fit items-center gap-2 rounded-full bg-brand-deep px-4 py-2 text-sm font-bold text-white transition-colors hover:bg-ink focus-visible:outline-none focus-visible:ring-3 focus-visible:ring-focus"
              >
                Open full-size
                <ExternalLink className="h-4 w-4" aria-hidden="true" />
              </a>
            </div>
          </div>

          <div className="border-t border-line px-5 py-4 sm:px-6">
            <div className="flex items-center justify-between gap-4">
              <h3 className="text-sm font-bold text-ink">Recent captures</h3>
              <p className="text-xs text-muted">
                {images.length} image{images.length === 1 ? "" : "s"} available
              </p>
            </div>
            <div className="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6">
              {images.map((image, index) => {
                const selected = image.name === selectedImage.name;
                return (
                  <button
                    key={image.name}
                    type="button"
                    onClick={() => onSelect(image.name)}
                    aria-label={`View image captured ${formatReadingTime(image.timestamp)}`}
                    aria-pressed={selected}
                    className={`overflow-hidden rounded-xl border-2 bg-surface-muted text-left transition-colors focus-visible:outline-none focus-visible:ring-3 focus-visible:ring-focus ${
                      selected
                        ? "border-brand"
                        : "border-transparent hover:border-line"
                    }`}
                  >
                    <img
                      src={image.url}
                      alt=""
                      loading={index === 0 ? "eager" : "lazy"}
                      className="aspect-video w-full object-cover"
                    />
                    <span className="block truncate px-2 py-1.5 text-xs font-semibold text-ink">
                      {index === 0
                        ? "Latest"
                        : formatRelativeTime(image.timestamp, nowMs)}
                    </span>
                  </button>
                );
              })}
            </div>
          </div>
        </>
      )}
    </section>
  );
}

function MetricCard({
  eyebrow,
  icon: Icon,
  iconClass,
  value,
  valueClass = "text-3xl",
  detail,
  detailClass,
  footer,
}: {
  eyebrow: string;
  icon: LucideIcon;
  iconClass: string;
  value: string;
  valueClass?: string;
  detail: string;
  detailClass: string;
  footer: string;
}) {
  return (
    <article className="flex min-h-52 flex-col border-line p-5 max-sm:border-b sm:nth-[odd]:border-r sm:nth-[-n+2]:border-b xl:border-r xl:border-b-0 xl:last:border-r-0 sm:p-6">
      <div className="flex items-center justify-between gap-4">
        <p className="text-xs font-bold tracking-[0.1em] text-muted uppercase">
          {eyebrow}
        </p>
        <Icon
          className={`h-5 w-5 ${iconClass}`}
          strokeWidth={2}
          aria-hidden="true"
        />
      </div>
      <div className="py-5">
        <p
          className={`data-value ${valueClass} leading-tight font-bold tracking-[-0.02em] text-ink`}
        >
          {value}
        </p>
        <p className={`mt-2 text-sm font-semibold ${detailClass}`}>{detail}</p>
      </div>
      <p className="mt-auto border-t border-line pt-3 text-xs leading-5 text-muted">
        {footer}
      </p>
    </article>
  );
}

function DebugItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="min-w-0">
      <dt className="mb-1 text-xs font-semibold tracking-wide text-muted uppercase">
        {label}
      </dt>
      <dd className="data-value break-all font-mono text-xs text-ink">{value}</dd>
    </div>
  );
}

function LoadingState() {
  return (
    <div role="status" aria-busy="true" aria-label="Checking the fridge">
      <span className="sr-only">Checking the fridge…</span>
      <div className="mb-6 space-y-3">
        <div className="skeleton h-9 w-72 max-w-full rounded-lg" />
        <div className="skeleton h-5 w-96 max-w-full rounded-md" />
      </div>
      <div className="skeleton h-36 rounded-panel" />
      <div className="mt-4 overflow-hidden rounded-panel bg-surface shadow-panel">
        <div className="border-b border-line px-5 py-4 sm:px-6">
          <div className="skeleton h-5 w-40 rounded-md" />
        </div>
        <div className="grid sm:grid-cols-2 xl:grid-cols-4">
          {[0, 1, 2, 3].map((item) => (
            <div
              key={item}
              className="min-h-48 border-line p-5 max-sm:border-b sm:nth-[odd]:border-r sm:nth-[-n+2]:border-b xl:border-r xl:border-b-0 xl:last:border-r-0 sm:p-6"
            >
              <div className="skeleton h-4 w-24 rounded" />
              <div className="skeleton mt-8 h-9 w-32 rounded-md" />
              <div className="skeleton mt-3 h-4 w-24 rounded" />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function ErrorState({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <StateCard
      icon={AlertCircle}
      iconClass="bg-red-100 text-red-700"
      title="We couldn’t check the fridge"
      body={message}
      action="Try again"
      onAction={onRetry}
    />
  );
}

function EmptyState({ onRetry }: { onRetry: () => void }) {
  return (
    <StateCard
      icon={Radio}
      iconClass="bg-sky-100 text-brand"
      title="Waiting for the first reading"
      body="The Pi API returned no sensor readings yet. Once the device records a reading, this dashboard will update automatically."
      action="Check again"
      onAction={onRetry}
    />
  );
}

function StateCard({
  icon: Icon,
  iconClass,
  title,
  body,
  action,
  onAction,
}: {
  icon: LucideIcon;
  iconClass: string;
  title: string;
  body: string;
  action: string;
  onAction: () => void;
}) {
  return (
    <section className="mx-auto mt-8 max-w-2xl rounded-panel bg-surface px-6 py-10 text-center shadow-panel sm:mt-12 sm:px-10 sm:py-12">
      <span
        className={`mx-auto mb-5 flex h-12 w-12 items-center justify-center rounded-xl ${iconClass}`}
      >
        <Icon className="h-6 w-6" aria-hidden="true" />
      </span>
      <h1 className="text-2xl font-bold tracking-[-0.02em] text-ink sm:text-3xl">
        {title}
      </h1>
      <p className="mx-auto mt-3 max-w-xl text-base leading-7 text-muted">
        {body}
      </p>
      <button
        type="button"
        onClick={onAction}
        className="mt-6 inline-flex min-h-11 items-center gap-2 rounded-full bg-brand-deep px-5 py-2.5 text-sm font-bold text-white transition-colors hover:bg-ink focus-visible:outline-none focus-visible:ring-3 focus-visible:ring-focus"
      >
        <RefreshCw className="h-4 w-4" aria-hidden="true" /> {action}
      </button>
    </section>
  );
}
