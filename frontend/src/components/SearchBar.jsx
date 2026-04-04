import { Search } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import axios from "axios";

const host =
  typeof window !== "undefined" ? window.location.hostname : "localhost";
const protocol =
  typeof window !== "undefined" ? window.location.protocol : "http:";
const API_BASE =
  import.meta.env.VITE_API_BASE_URL || `${protocol}//${host}:8000`;

export default function SearchBar({ onSelectSymbol, className = "" }) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [open, setOpen] = useState(false);
  const wrapperRef = useRef(null);

  useEffect(() => {
    const timer = setTimeout(async () => {
      if (!query.trim()) {
        setResults([]);
        return;
      }
      try {
        const { data } = await axios.get(`${API_BASE}/search`, {
          params: { q: query },
        });
        setResults(data.results || []);
        setOpen(true);
      } catch {
        setResults([]);
        setOpen(true);
      }
    }, 250);

    return () => clearTimeout(timer);
  }, [query]);

  useEffect(() => {
    function onClickOutside(e) {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", onClickOutside);
    return () => document.removeEventListener("mousedown", onClickOutside);
  }, []);

  return (
    <div ref={wrapperRef} className={`relative w-full ${className}`}>
      <div className="flex items-center gap-4 rounded-[var(--radius-md)] border border-[var(--color-border)] bg-[var(--color-surface)]/80 px-5 py-4 shadow-[var(--shadow-subtle)] backdrop-blur-xl focus-within:border-[var(--color-chart)] focus-within:shadow-[var(--shadow-ambient)] transition-all">
        <Search className="text-[var(--color-chart)]" size={20} />
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => query && setOpen(true)}
          placeholder="Search global & local equities (e.g. TCS.NS, NVDA)"
          className="w-full bg-transparent text-[1.125rem] font-medium font-[Sora] outline-none placeholder:text-[var(--color-text-secondary)] placeholder:font-normal text-[var(--color-text-primary)]"
        />
      </div>

      <p className="mt-3 pl-2 text-left text-xs uppercase tracking-widest font-bold text-[var(--color-text-secondary)] opacity-70">
        Press{" "}
        <span className="mono-font bg-[var(--color-surface)] border border-[var(--color-border)] px-1.5 py-0.5 rounded leading-none text-xs">
          /
        </span>{" "}
        to jump to search
      </p>

      {open && query.trim() && (
        <div className="absolute z-50 mt-3 max-h-72 w-full overflow-y-auto rounded-[var(--radius-lg)] border border-[var(--color-border)] bg-[var(--color-surface)] shadow-[var(--shadow-card)] backdrop-blur-2xl p-2 hide-scrollbar">
          {results.length > 0 ? (
            results.map((item) => (
              <button
                key={item.symbol}
                onClick={() => {
                  setQuery(`${item.name} (${item.symbol})`);
                  setOpen(false);
                  onSelectSymbol?.(item.symbol);
                }}
                className="flex w-full items-center justify-between rounded-[var(--radius-sm)] px-4 py-3 text-left hover:bg-[var(--color-bg)] transition-colors group mb-1 last:mb-0 border border-transparent hover:border-[var(--color-border)]"
              >
                <div>
                  <p className="font-semibold text-[var(--color-text-primary)] font-[Sora] group-hover:text-[var(--color-chart)] transition-colors">
                    {item.name}
                  </p>
                  <p className="text-xs text-[var(--color-text-secondary)] font-bold mono-font tracking-wide mt-0.5">
                    {item.symbol}
                  </p>
                </div>
                <span className="text-[0.65rem] font-bold uppercase tracking-widest text-[var(--color-text-secondary)] bg-[var(--color-border)] px-2 py-1 rounded">
                  {item.exchange}
                </span>
              </button>
            ))
          ) : (
            <div className="px-6 py-8 text-center text-sm font-semibold text-[var(--color-text-secondary)] flex flex-col items-center gap-2">
              <Search className="opacity-20" size={32} />
              <p>No equities found.</p>
              <p className="text-xs font-normal">
                Try exact tickers like{" "}
                <span className="mono-font text-[var(--color-text-primary)]">
                  MSFT
                </span>{" "}
                or{" "}
                <span className="mono-font text-[var(--color-text-primary)]">
                  RELIANCE.NS
                </span>
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
