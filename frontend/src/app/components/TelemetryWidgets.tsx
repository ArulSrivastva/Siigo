import React from "react";

export const DualArrowsIcon: React.FC<{ size?: "sm" | "md" | "lg"; className?: string }> = ({
  size = "md",
  className = "",
}) => {
  const pixelSize = { sm: 20, md: 32, lg: 44 }[size];
  return (
    <div className={`relative flex items-center justify-center shrink-0 ${className}`} style={{ width: pixelSize, height: pixelSize }}>
      <svg viewBox="0 0 100 100" fill="none" className="w-full h-full text-current">
        <g className="animate-arrow-top">
          <path d="M20 40 V26 C20 20 25 15 31 15 H80" stroke="currentColor" strokeWidth="8" strokeLinecap="square" />
          <path d="M65 2 L82 15 L65 28" stroke="currentColor" strokeWidth="8" strokeLinecap="square" />
        </g>
        <g className="animate-arrow-bottom">
          <path d="M80 60 V74 C80 80 75 85 69 85 H20" stroke="currentColor" strokeWidth="8" strokeLinecap="square" />
          <path d="M35 72 L18 85 L35 98" stroke="currentColor" strokeWidth="8" strokeLinecap="square" />
        </g>
      </svg>
    </div>
  );
};

export const RectEqualizerLoader: React.FC<{ label?: string }> = ({ label }) => (
  <div className="inline-flex items-center gap-2">
    <div className="flex items-center gap-1 h-4">
      <span className="w-1 h-3.5 bg-sky-400 rounded-none animate-rect-pulse" style={{ animationDelay: "0s" }} />
      <span className="w-1 h-3.5 bg-sky-400 rounded-none animate-rect-pulse" style={{ animationDelay: "0.15s" }} />
      <span className="w-1 h-3.5 bg-sky-400 rounded-none animate-rect-pulse" style={{ animationDelay: "0.3s" }} />
      <span className="w-1 h-3.5 bg-sky-400 rounded-none animate-rect-pulse" style={{ animationDelay: "0.45s" }} />
    </div>
    {label && <span className="font-mono text-xs font-semibold uppercase tracking-wider text-slate-400">{label}</span>}
  </div>
);

export type StatusStage = "IDLE" | "ACTIVE" | "PROCESSING" | "COMPLETED" | "FAILED";

export const StatusBadge: React.FC<{ stage: StatusStage; label?: string }> = ({ stage, label }) => {
  const configs: Record<StatusStage, { badge: string; pip: string; defaultLabel: string; pulse?: boolean }> = {
    IDLE: {
      badge: "bg-slate-900/60 text-slate-300 border-slate-700",
      pip: "bg-slate-400",
      defaultLabel: "Idle / Standby",
    },
    PROCESSING: {
      badge: "bg-sky-950/50 text-sky-300 border-sky-800",
      pip: "bg-sky-400",
      defaultLabel: "Processing",
      pulse: true,
    },
    ACTIVE: {
      badge: "bg-amber-950/50 text-amber-300 border-amber-800",
      pip: "bg-amber-400",
      defaultLabel: "Live / Under Test",
      pulse: true,
    },
    COMPLETED: {
      badge: "bg-emerald-950/60 text-emerald-200 border-emerald-700",
      pip: "bg-emerald-400",
      defaultLabel: "Verified / Passed",
    },
    FAILED: {
      badge: "bg-rose-950/50 text-rose-300 border-rose-800",
      pip: "bg-rose-400",
      defaultLabel: "Rejected / Alert",
    },
  };
  const config = configs[stage] || configs.IDLE;
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded text-xs font-mono font-semibold border ${config.badge}`}>
      <span className={`w-1.5 h-1.5 rounded-none ${config.pip} ${config.pulse ? "animate-pulse" : ""}`} />
      <span>{label || config.defaultLabel}</span>
    </span>
  );
};
