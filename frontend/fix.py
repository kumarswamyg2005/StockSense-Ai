import re

with open('/Users/kumaraswamy/Desktop/Fiance/stocksense-ai/frontend/src/pages/AllStocks.jsx', 'r') as f:
    text = f.read()

pattern = r'<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">.*?</ChevronRight size=\{16\} />\n                  </div>\n                </div>\n              \);\n            \}\)}\n          </div>'
import textwrap

new_str = """<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {trendingData?.stocks?.map((stock, index) => {
              const hasPrice = stock.price !== null && stock.price !== undefined;
              const isUp = hasPrice && stock.daily_change_pct >= 0;
              const sign = isUp ? "+" : "";
              const colorClass = isUp
                  ? "text-[var(--color-gain)]"
                  : hasPrice ? "text-[var(--color-loss)]" : "text-[var(--color-text-secondary)]";

              return (
                <div
                  key={stock.symbol}
                  onClick={() => navigate(`/stock/${stock.symbol}`)}
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
                        {hasPrice ? `${sign}${stock.daily_change_pct.toFixed(2)}%` : ""}
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
          </div>"""

new_text = re.sub(pattern, new_str, text, flags=re.DOTALL)
with open('/Users/kumaraswamy/Desktop/Fiance/stocksense-ai/frontend/src/pages/AllStocks.jsx', 'w') as f:
    f.write(new_text)
