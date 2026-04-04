import React from "react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "react-query";
import axios from "axios";
import { Activity, ArrowLeft, ChevronRight } from "lucide-react";
import SignalBadge from "../components/SignalBadge";

const host =
  typeof window !== "undefined" ? window.location.hostname : "localhost";
const protocol =
  typeof window !== "undefined" ? window.location.protocol : "http:";
const API_BASE =
  import.meta.env.VITE_API_BASE_URL || `${protocol}//${host}:8000`;

export default function AllStocks() {
  const navigate = useNavigate();

  const { data: trendingData, isLoading } = useQuery(
    ["allStocks"],
    async () => {
      const res = await axios.get(
        `${API_BASE}/trending?include_signals=true&limit=500`,
      );
      return res.data;
    },
    { refetchOnWindowFocus: false, staleTime: 60000 },
  );

  return (
    <div className="min-h-screen relative overflow-hidden pb-32">
      <div className="absolute top-[-20%] left-[-10%] w-[60%] h-[60%] bg-[var(--color-chart)] opacity-[0.03] rounded-full blur-[120px] pointer-events-none mix-blend-screen animate-pulse-slow"></div>
      <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-[#FF3366] opacity-[0.02] rounded-full blur-[100px] pointer-events-none mix-blend-screen"></div>

      <div className="max-w-[1400px] mx-auto px-[var(--space-md)] lg:px-[var(--space-xl)] mt-12 relative z-20">
        <button
          onClick={() => navigate("/")}
          className="mb-8 flex items-center gap-2 text-sm font-bold uppercase tracking-widest text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] transition-colors"
        >
          <ArrowLeft size={16} /> Home
        </button>

        <div className="mb-12">
          <div className="inline-flex items-center justify-center gap-2 rounded-full border border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-1.5 text-xs font-bold uppercase tracking-widest text-[var(--color-text-primary)] shadow-[var(--shadow-subtle)] mb-6">
            <span className="relative flex h-2 w-2 shrink-0">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-[var(--color-chart)] opacity-75"></span>
              <span className="relative inline-flex h-2 w-2 rounded-full bg-[var(--color-chart)]"></span>
            </span>
            All Tracked Assets
          </div>
          <h2 className="text-4xl md:text-5xl font-extrabold leading-[1.1] tracking-tight font-[Sora] mb-4">
            Market Universe
          </h2>
          <p className="text-[var(--color-text-secondary)] max-w-2xl text-lg opacity-80 leading-relaxed font-medium">
            Explore all predictive signals across the entire database.
          </p>
        </div>

        {isLoading ? (
          <div className="mt-20 flex flex-col items-center justify-center space-y-6">
            <Activity
              className="animate-spin text-[var(--color-border)] opacity-30"
              size={48}
            />
            <p className="text-sm font-bold uppercase tracking-widest text-[var(--color-text-secondary)] animate-pulse">
              Aggregating signals...
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {trendingData?.stocks?.map((stock, index) => {
              const hasPrice =
                stock.price !== null && stock.price !== undefined;
              const isUp = hasPrice && stock.daily_change_pct >= 0;
              const sign = isUp ? "+" : "";
              const colorClass = isUp
                ? "text-[var(--color-gain)]"
                : hasPrice
                  ? "text-[var(--color-loss)]"
                  : "text-[var(--color-text-secondary)]";

              return (
                <div
                  key={stock.symbol}
                  onClick={() =>
                    navigate(`/stock/${encodeURIComponent(stock.symbol)}`)
                  }
                  className="card p-6 flex flex-col justify-between hover:border-[var(--color-chart)]/40 hover:-translate-y-2 transition-all cursor-pointer group opacity-0 animate-[fadeInY_0.5s_ease-out_forwards] relative z-10 hover:z-20"
                  style={{ animationDelay: `${index * 0.05}s` }}
                >
                  <div className="flex justify-between items-start mb-6">
                    <div>
                      <h3 className="text-2xl font-extrabold font-[Sora] tracking-tight">
                        {stock.symbol}
                      </h3>
                      <p className="text-xs font-bold uppercase tracking-widest text-[var(--color-text-secondary)] mt-1 truncate max-w-[150px]">
                        {stock.name}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-xl font-extrabold mono-font">
                        {hasPrice ? stock.price.toFixed(2) : "N/A"}
                      </p>
                      <p
                        className={`text-sm font-bold mono-font mt-1 ${colorClass}`}
                      >
                        {hasPrice && stock.daily_change_pct != null
                          ? `${sign}${stock.daily_change_pct.toFixed(2)}%`
                          : ""}
                      </p>
                    </div>
                  </div>

                  <div className="mt-auto">
                    <SignalBadge signal={stock.signal} />
                  </div>

                  <div className="mt-4 pt-4 border-t border-[var(--color-border)] flex justify-between items-center group-hover:text-[var(--color-chart)] transition-colors">
                    <span className="text-[0.7rem] uppercase tracking-widest font-bold opacity-70">
                      View Deep Analysis
                    </span>
                    <ChevronRight size={16} />
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
