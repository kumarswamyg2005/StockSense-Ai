import ErrorBoundary from "./components/ErrorBoundary";
import { Link, Route, Routes } from "react-router-dom";
import { Activity, Moon, Sun } from "lucide-react";
import { useEffect, useState } from "react";
import Home from "./pages/Home";
import StockDetail from "./pages/StockDetail";
import AllStocks from "./pages/AllStocks";

export default function App() {
  const [darkMode, setDarkMode] = useState(() => {
    const stored = localStorage.getItem("stocksense-theme");
    return stored ? stored === "dark" : true;
  });

  useEffect(() => {
    const root = document.documentElement;
    root.classList.add("theme-transition");
    root.classList.toggle("dark", darkMode);
    localStorage.setItem("stocksense-theme", darkMode ? "dark" : "light");

    const timer = window.setTimeout(() => {
      root.classList.remove("theme-transition");
    }, 320);

    return () => window.clearTimeout(timer);
  }, [darkMode]);

  return (
    <div className="min-h-screen bg-[var(--color-bg)] text-[var(--color-text-primary)] transition-colors relative">
      <div className="pointer-events-none fixed inset-0 -z-10 bg-[radial-gradient(circle_at_20%_0%,rgba(0,200,81,0.05),transparent_40%),radial-gradient(circle_at_80%_20%,rgba(144,144,152,0.03),transparent_35%)] dark:bg-[radial-gradient(circle_at_20%_0%,rgba(0,200,81,0.08),transparent_40%),radial-gradient(circle_at_80%_20%,rgba(20,20,24,0.3),transparent_45%)]" />

      <header className="sticky top-0 z-40 border-b border-[var(--color-border)] bg-[var(--color-bg)]/80 backdrop-blur-xl">
        <div className="mx-auto flex w-full max-w-[1400px] items-center justify-between px-4 py-4 md:px-8">
          <Link to="/" className="group flex items-center gap-3">
            <div className="relative flex h-10 w-10 shrink-0 items-center justify-center overflow-hidden rounded-xl bg-gradient-to-br from-[var(--color-chart)] to-[#009d3e] shadow-[0_0_15px_rgba(0,200,81,0.2)] transition-transform group-hover:scale-105">
              <div className="absolute inset-0 bg-black/10 mix-blend-darken"></div>
              <Activity
                size={20}
                className="relative z-10 text-white stroke-[2.5]"
              />
            </div>
            <div>
              <p className="text-xl font-extrabold leading-none text-[var(--color-text-primary)] font-[Sora] tracking-tight">
                StockSense
              </p>
              <p className="text-[0.65rem] font-bold text-[var(--color-chart)] uppercase tracking-[0.2em] mt-1 opacity-90">
                Studio Edition
              </p>
            </div>
          </Link>

          <button
            onClick={() => setDarkMode((prev) => !prev)}
            className="rounded-full border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-sm shadow-[var(--shadow-subtle)] transition-all hover:shadow-[var(--shadow-hover)] hover:-translate-y-0.5 text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)]"
            aria-label="Toggle theme"
          >
            {darkMode ? <Sun size={16} /> : <Moon size={16} />}
          </button>
        </div>
      </header>

      <main className="w-full">
        <ErrorBoundary>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/all-stocks" element={<AllStocks />} />
            <Route path="/stock/:symbol" element={<StockDetail />} />
          </Routes>
        </ErrorBoundary>
      </main>
    </div>
  );
}
