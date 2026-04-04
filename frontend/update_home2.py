import os

home_content = """import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Search, TrendingUp, TrendingDown, Sparkles, Activity, FileText } from "lucide-react";
import { useQuery } from "react-query";
import axios from "axios";

const host = typeof window !== "undefined" ? window.location.hostname : "localhost";
const protocol = typeof window !== "undefined" ? window.location.protocol : "http:";
const API_BASE = import.meta.env.VITE_API_BASE_URL || `${protocol}//${host}:8000`;

export default function Home() {
  const navigate = useNavigate();
  const [query, setQuery] = useState("");
  const [signalFilter, setSignalFilter] = useState("ALL");

  const fetchTrending = async () => {
    const params = { include_signals: true, limit: 15 };
    if (signalFilter !== "ALL") {
      params.signal = signalFilter;
    }
    const { data } = await axios.get(`${API_BASE}/trending`, { params });
    return data.stocks || [];
  };

  const { data: trending = [], isLoading: trendLoading } = useQuery(
    ["trending", signalFilter], 
    fetchTrending,
    { keepPreviousData: true }
  );

  const fetchMarket = async () => {
    const { data } = await axios.get(`${API_BASE}/market-overview`);
    return data.indices || {};
  };

  const { data: marketData = {} } = useQuery(["market"], fetchMarket);

  const handleSearch = (e) => {
    e.preventDefault();
    if (query.trim()) {
      navigate(`/stock/${query.toUpperCase()}`);
    }
  };

  return (
    <div className="pb-16 relative w-full h-full" style={{ zIndex: 0 }}>
      <div className="page-background">
        <div className="mesh-gradient"></div>
        <div className="noise-overlay"></div>
      </div>

      <div className="max-w-[1400px] mx-auto px-[var(--space-md)] lg:px-[var(--space-xl)] grid lg:grid-cols-[1.1fr_0.9fr] gap-16 lg:gap-8 min-h-[min(80vh,800px)] items-center">
        <div className="mt-12 lg:mt-0">
          <div className="w-12 h-[3px] bg-[var(--color-chart)] mb-8 animate-[fadeInY_0.8s_ease-out_forwards]"></div>
          
          <h1 className="text-[clamp(3.5rem,6vw,6.5rem)] leading-[1.02] font-extrabold mb-6 animate-[fadeInY_0.8s_ease-out_0.1s_forwards] opacity-0" style={{ fontFamily: "Sora, sans-serif", letterSpacing: "-0.02em" }}>
             <span className="block text-[clamp(1.25rem,2.5vw,2rem)] font-normal mb-2 text-[var(--color-text-secondary)]">Precision signals.</span>
             Zero <br/> Noise.
          </h1>
          
          <p className="text-[1.125rem] leading-[1.6] text-[var(--color-text-secondary)] mb-10 max-w-[500px] animate-[fadeInY_0.8s_ease-out_0.2s_forwards] opacity-0">
            Harness deep learning models to forecast market movements. Clean typography, exact data, and actionable intelligence — designed for the modern investor.
          </p>

          <form onSubmit={handleSearch} className="relative max-w-[440px] animate-[fadeInY_0.8s_ease-out_0.3s_forwards] opacity-0 z-40">
            <input
              type="text"
              className="w-full bg-[var(--color-surface)] border border-[var(--color-border)] rounded-full py-5 pr-6 pl-14 text-base shadow-[var(--shadow-subtle)] transition-all duration-300 outline-none focus:border-[var(--color-chart)] focus:shadow-[var(--shadow-hover)] hover:shadow-[var(--shadow-hover)]"
              placeholder="Enter ticker (e.g. AAPL, TSLA)"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              spellCheck="false"
              autoComplete="off"
            />
            <Search size={20} className="absolute left-5 top-1/2 -translate-y-1/2 text-[var(--color-text-secondary)]" />
            
            {query.length > 0 && (
              <div className="absolute top-[calc(100%+12px)] left-0 right-0 bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl shadow-[var(--shadow-card)] p-2 z-50">
                <div 
                  className="flex items-center justify-between p-3 rounded-lg cursor-pointer hover:bg-[var(--color-bg)] hover:text-[var(--color-chart)] transition-colors"
                  onClick={() => navigate(`/stock/${query.toUpperCase()}`)}
                >
                  <div className="flex gap-3">
                    <span className="mono-font font-semibold">{query.toUpperCase()}</span>
                    <span className="text-sm text-[var(--color-text-secondary)]">Analyze asset &rarr;</span>
                  </div>
                </div>
              </div>
            )}
          </form>
        </div>

        <div className="relative h-[600px] flex justify-center items-start pt-[var(--space-2xl)] animate-[fadeInY_0.8s_ease-out_0.2s_forwards] opacity-0 lg:flex hidden">
          <div className="absolute z-10 w-[340px] bg-[var(--color-surface)] border border-[var(--color-border)] p-[var(--space-xl)] shadow-[var(--shadow-card)] rotate-[-2deg] -translate-x-8 rounded-[var(--radius-lg)] animate-[floatA_7s_ease-in-out_infinite] hover:rotate-0 hover:-translate-y-2 hover:translate-x-[-30px] hover:scale-[1.03] hover:shadow-[var(--shadow-hover)] hover:z-20 transition-all duration-500 cursor-default">
            <div className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-[0.75rem] font-extrabold uppercase tracking-[0.06em] bg-[var(--color-ai-bg)] text-[var(--color-ai-text)] mb-4 mono-font shadow-sm">
              <Sparkles size={14} fill="currentColor" strokeWidth={1.5} /> Signal: Bullish
            </div>
            
            <div className="flex justify-between items-start mb-4">
              <div>
                <div className="text-[1.75rem] font-extrabold font-[Sora]">NVDA</div>
                <div className="text-sm text-[var(--color-text-secondary)] mt-1">NVIDIA Corporation</div>
              </div>
              <Activity size={28} color="var(--color-chart)" strokeWidth={2} />
            </div>
            
            <div className="mono-font text-[2.5rem] font-medium tracking-tight mb-2">177.39</div>
            
            <div className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full font-semibold text-[0.875rem] mono-font bg-[var(--color-gain-bg)] text-[var(--color-gain)]">
              <TrendingUp size={18} strokeWidth={2.5} /> +1.64 (+0.93%)
            </div>
          </div>

          <div className="absolute z-[5] w-[340px] bg-[var(--color-surface)] border border-[var(--color-border)] p-[var(--space-xl)] shadow-[var(--shadow-card)] rotate-[4deg] translate-x-20 translate-y-36 rounded-[var(--radius-md)_var(--radius-lg)_var(--radius-md)_var(--radius-sm)] opacity-95 animate-[floatB_9s_ease-in-out_infinite_1s] hover:rotate-[2deg] hover:translate-x-20 hover:translate-y-[130px] hover:scale-[1.03] hover:opacity-100 hover:shadow-[var(--shadow-hover)] hover:z-20 transition-all duration-500 cursor-default">
             <div className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-[0.75rem] font-extrabold uppercase tracking-[0.06em] mb-4 mono-font" style={{ background: "var(--color-loss-bg)", color: "var(--color-loss)" }}>
              <Sparkles size={14} fill="currentColor" strokeWidth={1.5} /> Signal: Bearish
            </div>
            <div className="flex justify-between items-start mb-4">
              <div>
                <div className="text-[1.75rem] font-extrabold font-[Sora]">TSLA</div>
                <div className="text-sm text-[var(--color-text-secondary)] mt-1">Tesla, Inc.</div>
              </div>
            </div>
            <div className="mono-font text-[2.5rem] font-medium tracking-tight mb-2">174.20</div>
            <div className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full font-semibold text-[0.875rem] mono-font" style={{ background: "var(--color-loss-bg)", color: "var(--color-loss)" }}>
              <TrendingDown size={18} strokeWidth={2.5} /> -1.8% predicted
            </div>
          </div>
        </div>
      </div>

      {Object.keys(marketData).length > 0 && (
        <div className="max-w-[1400px] mx-auto px-[var(--space-md)] lg:px-[var(--space-xl)] mb-12 relative z-20">
          <div className="flex flex-wrap gap-4 overflow-x-auto pb-4 hide-scrollbar">
            {Object.entries(marketData).map(([key, info]) => {
              const isUp = info.change >= 0;
              return (
                <div key={key} className="card py-3 px-5 flex items-center gap-4 min-w-[200px] flex-shrink-0">
                  <div>
                    <div className="text-[0.7rem] uppercase tracking-widest font-bold text-[var(--color-text-secondary)] mb-1">{key}</div>
                    <div className="text-lg font-extrabold mono-font">{info.price}</div>
                  </div>
                  <div className={`ml-auto text-sm font-bold mono-font ${isUp ? 'text-[var(--color-gain)]' : 'text-[var(--color-loss)]'}`}>
                    {isUp ? '+' : ''}{info.change_pct}%
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      <div className="max-w-[1400px] mx-auto px-[var(--space-md)] lg:px-[var(--space-xl)] mt-12 relative z-20">
        <div className="flex flex-col sm:flex-row sm:items-end justify-between mb-8 gap-4">
            <h2 className="section-title !mb-0">Trending Predictions</h2>
            
            {/* Filters */}
            <div className="flex bg-[var(--color-surface)] border border-[var(--color-border)] rounded-full p-1.5 shadow-[var(--shadow-subtle)]">
                {["ALL", "BUY", "HOLD", "SELL"].map((f) => (
                    <button
                        key={f}
                        onClick={() => setSignalFilter(f)}
                        className={`px-5 py-2 text-xs font-bold uppercase tracking-wider rounded-full transition-all ${signalFilter === f ? 'bg-[var(--color-bg)] text-[var(--color-chart)] shadow-sm' : 'text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)]'}`}
                    >
                        {f}
                    </button>
                ))}
            </div>
        </div>

        {trendLoading ? (
            <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="h-[140px] rounded-[var(--radius-lg)] bg-[var(--color-border)]/40 animate-pulse" />
              ))}
            </div>
          ) : trending.length === 0 ? (
            <div className="card-strong py-12 text-center flex flex-col items-center">
              <FileText className="text-[var(--color-text-secondary)] opacity-50 mb-4" size={40} />
              <p className="text-[var(--color-text-secondary)] font-medium">No assets match the current filter.</p>
            </div>
          ) : (
            <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
              {trending.map((item) => {
                const signal = item.signal?.signal || "WAIT";
                const isBullish = signal === "BUY";
                const isBearish = signal === "SELL";
                const isHold = signal === "HOLD";
                
                let sigClass = "bg-[var(--color-border)] text-[var(--color-text-primary)]";
                if (isBullish) sigClass = "bg-[var(--color-gain-bg)] text-[var(--color-gain)]";
                if (isBearish) sigClass = "bg-[var(--color-loss-bg)] text-[var(--color-loss)]";
                if (isHold) sigClass = "bg-amber-500/10 text-amber-500";

                const isUp = item.daily_change_pct >= 0;

                return (
                  <div 
                    key={item.symbol} 
                    onClick={() => navigate(`/stock/${item.symbol}`)}
                    className="card cursor-pointer group hover:border-[var(--color-chart)]/40 transition-colors"
                  >
                    <div className="flex justify-between items-start mb-4">
                        <div>
                            <h3 className="text-xl font-extrabold font-[Sora] group-hover:text-[var(--color-chart)] transition-colors">{item.symbol}</h3>
                            <p className="text-xs font-semibold text-[var(--color-text-secondary)] mt-1 line-clamp-1 uppercase tracking-widest">{item.name}</p>
                        </div>
                        <div className={`inline-flex items-center px-2 py-0.5 rounded-[var(--radius-sm)] text-[0.7rem] font-bold mono-font ${sigClass}`}>
                            {signal}
                        </div>
                    </div>
                    <div className="flex items-end justify-between mt-6">
                        <div className="mono-font text-2xl font-bold tracking-tight">
                            {item.current_price} <span className="text-[0.8rem] text-[var(--color-text-secondary)] ml-0.5">{item.currency}</span>
                        </div>
                        <div className={`mono-font text-sm font-semibold tracking-tight ${isUp ? 'text-[var(--color-gain)]' : 'text-[var(--color-loss)]'}`}>
                            {isUp ? '+' : ''}{item.daily_change_pct}%
                        </div>
                    </div>
                  </div>
                );
              })}
            </div>
        )}
      </div>
      <style>{`
        @keyframes fadeInY {
          from { opacity: 0; transform: translateY(40px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @keyframes floatA {
          0%, 100% { transform: rotate(-2deg) translate(-30px, 0); }
          50% { transform: rotate(-2deg) translate(-30px, -15px); }
        }
        @keyframes floatB {
          0%, 100% { transform: rotate(4deg) translate(80px, 140px); }
          50% { transform: rotate(4deg) translate(80px, 125px); }
        }
      `}</style>
    </div>
  );
}
"""

with open("/Users/kumaraswamy/Desktop/Fiance/stocksense-ai/frontend/src/pages/Home.jsx", "w") as f:
    f.write(home_content)

print("Updated Home.jsx")
