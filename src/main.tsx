import React from "react";
import { createRoot } from "react-dom/client";
import { Bell, ChevronDown, Database, LineChart, RefreshCw, Search, Settings2, ShieldAlert, Signal, Waves } from "lucide-react";
import "./styles.css";

type Market = "KRW-BTC" | "KRW-ETH" | "KRW-XRP";
type Timeframe = "15m" | "4h";
type Persona = "accumulation" | "breakout" | "distribution_trap" | "panic_sell" | "retail_chop" | "sleep";

type Snapshot = {
  snapshot_at: string;
  price_close: number;
  price_change_pct: number;
  volatility_pct: number;
  total_volume_krw: number;
  volume_surge_ratio: number;
  whale_buy_krw: number;
  whale_sell_krw: number;
  retail_buy_krw: number;
  retail_sell_krw: number;
  whale_net_ratio: number;
  retail_net_ratio: number;
  trade_count: number;
  whale_count: number;
};

type PersonaSnapshot = {
  persona: Persona;
  confidence: number;
  reason_codes: string[];
};

const markets: Market[] = ["KRW-BTC", "KRW-ETH", "KRW-XRP"];
const timeframes: Timeframe[] = ["15m", "4h"];

const snapshots: Record<Market, Record<Timeframe, Snapshot>> = {
  "KRW-BTC": {
    "15m": {
      snapshot_at: "2026-06-28T05:30:00Z",
      price_close: 98500000,
      price_change_pct: 1.55,
      volatility_pct: 2.1,
      total_volume_krw: 7200000000,
      volume_surge_ratio: 1.8,
      whale_buy_krw: 2600000000,
      whale_sell_krw: 1200000000,
      retail_buy_krw: 2100000000,
      retail_sell_krw: 1300000000,
      whale_net_ratio: 0.1944,
      retail_net_ratio: 0.1111,
      trade_count: 18420,
      whale_count: 211,
    },
    "4h": {
      snapshot_at: "2026-06-28T04:00:00Z",
      price_close: 98240000,
      price_change_pct: 2.84,
      volatility_pct: 3.7,
      total_volume_krw: 58600000000,
      volume_surge_ratio: 1.42,
      whale_buy_krw: 16800000000,
      whale_sell_krw: 10400000000,
      retail_buy_krw: 17800000000,
      retail_sell_krw: 13600000000,
      whale_net_ratio: 0.1092,
      retail_net_ratio: 0.0717,
      trade_count: 261540,
      whale_count: 2938,
    },
  },
  "KRW-ETH": {
    "15m": {
      snapshot_at: "2026-06-28T05:30:00Z",
      price_close: 5420000,
      price_change_pct: -0.62,
      volatility_pct: 1.35,
      total_volume_krw: 2860000000,
      volume_surge_ratio: 1.22,
      whale_buy_krw: 620000000,
      whale_sell_krw: 910000000,
      retail_buy_krw: 740000000,
      retail_sell_krw: 590000000,
      whale_net_ratio: -0.1014,
      retail_net_ratio: 0.0524,
      trade_count: 9230,
      whale_count: 87,
    },
    "4h": {
      snapshot_at: "2026-06-28T04:00:00Z",
      price_close: 5455000,
      price_change_pct: 0.48,
      volatility_pct: 2.4,
      total_volume_krw: 19400000000,
      volume_surge_ratio: 1.08,
      whale_buy_krw: 4200000000,
      whale_sell_krw: 3980000000,
      retail_buy_krw: 5730000000,
      retail_sell_krw: 4920000000,
      whale_net_ratio: 0.0113,
      retail_net_ratio: 0.0417,
      trade_count: 112830,
      whale_count: 920,
    },
  },
  "KRW-XRP": {
    "15m": {
      snapshot_at: "2026-06-28T05:30:00Z",
      price_close: 725,
      price_change_pct: -2.14,
      volatility_pct: 3.22,
      total_volume_krw: 4180000000,
      volume_surge_ratio: 2.05,
      whale_buy_krw: 610000000,
      whale_sell_krw: 1660000000,
      retail_buy_krw: 780000000,
      retail_sell_krw: 1130000000,
      whale_net_ratio: -0.2512,
      retail_net_ratio: -0.0837,
      trade_count: 31180,
      whale_count: 154,
    },
    "4h": {
      snapshot_at: "2026-06-28T04:00:00Z",
      price_close: 739,
      price_change_pct: -1.02,
      volatility_pct: 4.12,
      total_volume_krw: 34400000000,
      volume_surge_ratio: 1.51,
      whale_buy_krw: 6400000000,
      whale_sell_krw: 8800000000,
      retail_buy_krw: 9800000000,
      retail_sell_krw: 9400000000,
      whale_net_ratio: -0.0698,
      retail_net_ratio: 0.0116,
      trade_count: 384200,
      whale_count: 1884,
    },
  },
};

const personas: Record<Market, Record<Timeframe, PersonaSnapshot>> = {
  "KRW-BTC": {
    "15m": { persona: "breakout", confidence: 0.82, reason_codes: ["volume_surge", "price_breakout", "whale_buy"] },
    "4h": { persona: "accumulation", confidence: 0.68, reason_codes: ["whale_net", "steady_volume", "range_expansion"] },
  },
  "KRW-ETH": {
    "15m": { persona: "retail_chop", confidence: 0.57, reason_codes: ["mixed_flow", "low_surge", "narrow_range"] },
    "4h": { persona: "sleep", confidence: 0.61, reason_codes: ["low_volatility", "balanced_flow", "quiet_count"] },
  },
  "KRW-XRP": {
    "15m": { persona: "panic_sell", confidence: 0.77, reason_codes: ["price_drop", "volume_surge", "whale_sell"] },
    "4h": { persona: "distribution_trap", confidence: 0.64, reason_codes: ["whale_sell_bias", "high_volatility", "retail_absorption"] },
  },
};

const series = [42, 46, 43, 51, 57, 55, 64, 62, 68, 73, 69, 78, 82, 80, 88];

function App() {
  const [market, setMarket] = React.useState<Market>("KRW-BTC");
  const [timeframe, setTimeframe] = React.useState<Timeframe>("15m");
  const [alerts, setAlerts] = React.useState(true);

  const snapshot = snapshots[market][timeframe];
  const persona = personas[market][timeframe];
  const marketRows = markets.map((item) => ({
    market: item,
    snapshot: snapshots[item][timeframe],
    persona: personas[item][timeframe],
  }));

  return (
    <main className="shell">
      <div className="mesh" aria-hidden="true" />
      <header className="topbar">
        <div className="brand">
          <div className="brand-mark">S</div>
          <span>SkySH</span>
        </div>
        <nav className="nav">
          <a href="#market">Market</a>
          <a href="#persona">Persona</a>
          <a href="#alerts">Alerts</a>
        </nav>
        <div className="actions">
          <button className="icon-button" aria-label="Search">
            <Search size={18} />
          </button>
          <button className="primary-button">
            <RefreshCw size={16} />
            Sync
          </button>
        </div>
      </header>

      <section className="hero" id="market">
        <div>
          <span className="tag">UTC snapshot · KST display</span>
          <h1>Market flow console</h1>
          <p className="lead">KRW-BTC, KRW-ETH, KRW-XRP의 1분 버킷 기반 지표와 Persona를 한 화면에서 비교합니다.</p>
        </div>
        <div className="hero-controls" aria-label="Market controls">
          <div className="select-wrap">
            <select value={market} onChange={(event) => setMarket(event.target.value as Market)}>
              {markets.map((item) => (
                <option key={item}>{item}</option>
              ))}
            </select>
            <ChevronDown size={16} />
          </div>
          <div className="segment">
            {timeframes.map((item) => (
              <button key={item} className={item === timeframe ? "active" : ""} onClick={() => setTimeframe(item)}>
                {item}
              </button>
            ))}
          </div>
        </div>
      </section>

      <section className="metrics-grid" aria-label="Snapshot metrics">
        <Metric label="현재가" value={formatPrice(market, snapshot.price_close)} delta={snapshot.price_change_pct} />
        <Metric label="거래대금" value={formatKrw(snapshot.total_volume_krw)} delta={snapshot.volume_surge_ratio - 1} suffix="surge" />
        <Metric label="고래 순매수" value={formatKrw(snapshot.whale_buy_krw - snapshot.whale_sell_krw)} delta={snapshot.whale_net_ratio} />
        <Metric label="변동성" value={`${snapshot.volatility_pct.toFixed(2)}%`} delta={snapshot.volatility_pct / 10} />
      </section>

      <section className="workbench">
        <div className="panel chart-panel">
          <div className="panel-head">
            <div>
              <span className="eyebrow">IndicatorSnapshot</span>
              <h2>{market} · {timeframe}</h2>
            </div>
            <span className="timestamp">{toKst(snapshot.snapshot_at)}</span>
          </div>
          <Chart />
          <div className="flow-grid">
            <Flow label="Whale buy" value={snapshot.whale_buy_krw} tone="buy" />
            <Flow label="Whale sell" value={snapshot.whale_sell_krw} tone="sell" />
            <Flow label="Retail buy" value={snapshot.retail_buy_krw} tone="buy" />
            <Flow label="Retail sell" value={snapshot.retail_sell_krw} tone="sell" />
          </div>
        </div>

        <aside className="panel persona-panel" id="persona">
          <div className="panel-head compact">
            <div>
              <span className="eyebrow">PersonaSnapshot</span>
              <h2>{personaLabel(persona.persona)}</h2>
            </div>
            <ShieldAlert size={22} />
          </div>
          <div className={`persona-badge ${persona.persona}`}>
            <span>{persona.persona}</span>
            <strong>{Math.round(persona.confidence * 100)}%</strong>
          </div>
          <div className="reason-list">
            {persona.reason_codes.map((reason) => (
              <span key={reason}>{reason}</span>
            ))}
          </div>
          <div className="persona-stats">
            <div>
              <span>Trade count</span>
              <strong>{formatCount(snapshot.trade_count)}</strong>
            </div>
            <div>
              <span>Whale count</span>
              <strong>{formatCount(snapshot.whale_count)}</strong>
            </div>
          </div>
        </aside>
      </section>

      <section className="table-section">
        <div className="section-head">
          <div>
            <span className="eyebrow">Market board</span>
            <h2>Snapshot comparison</h2>
          </div>
          <button className="secondary-button">
            <LineChart size={16} />
            Export
          </button>
        </div>
        <div className="data-table">
          <div className="table-row table-head">
            <span>Market</span>
            <span>Persona</span>
            <span>Price</span>
            <span>Change</span>
            <span>Volume</span>
            <span>Whale net</span>
          </div>
          {marketRows.map((row) => (
            <button key={row.market} className="table-row" onClick={() => setMarket(row.market)}>
              <span className="market-cell">
                <Signal size={16} />
                {row.market}
              </span>
              <span>{personaLabel(row.persona.persona)}</span>
              <span className="num">{formatPrice(row.market, row.snapshot.price_close)}</span>
              <span className={`num ${row.snapshot.price_change_pct >= 0 ? "positive" : "negative"}`}>
                {row.snapshot.price_change_pct.toFixed(2)}%
              </span>
              <span className="num">{formatKrw(row.snapshot.total_volume_krw)}</span>
              <span className={`num ${row.snapshot.whale_net_ratio >= 0 ? "positive" : "negative"}`}>
                {(row.snapshot.whale_net_ratio * 100).toFixed(2)}%
              </span>
            </button>
          ))}
        </div>
      </section>

      <section className="ops-band" id="alerts">
        <div className="ops-copy">
          <span className="tag">Pipeline status</span>
          <h2>15m 알림은 Persona 계산과 분리되어 발송 대상에서만 적용됩니다.</h2>
        </div>
        <div className="ops-items">
          <Status icon={<Waves size={18} />} label="Upbit stream" value="mock trade events" />
          <Status icon={<Database size={18} />} label="MinuteBucket" value="fixture 15m / 4h" />
          <label className="toggle">
            <Bell size={18} />
            <span>15m alert</span>
            <input type="checkbox" checked={alerts} onChange={() => setAlerts((value) => !value)} />
          </label>
          <button className="icon-button" aria-label="Settings">
            <Settings2 size={18} />
          </button>
        </div>
      </section>
    </main>
  );
}

function Metric({ label, value, delta, suffix }: { label: string; value: string; delta: number; suffix?: string }) {
  const positive = delta >= 0;
  return (
    <article className="metric">
      <span>{label}</span>
      <strong>{value}</strong>
      <em className={positive ? "positive" : "negative"}>{positive ? "+" : ""}{suffix ? delta.toFixed(2) : (delta * 100).toFixed(2)}{suffix ? ` ${suffix}` : "%"}</em>
    </article>
  );
}

function Chart() {
  const points = series.map((value, index) => `${(index / (series.length - 1)) * 100},${100 - value}`).join(" ");
  return (
    <div className="chart">
      <svg viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">
        <polyline points={points} fill="none" stroke="#533afd" strokeWidth="2.4" vectorEffect="non-scaling-stroke" />
        <polyline points={`0,100 ${points} 100,100`} fill="rgba(83,58,253,0.08)" stroke="none" />
      </svg>
    </div>
  );
}

function Flow({ label, value, tone }: { label: string; value: number; tone: "buy" | "sell" }) {
  return (
    <div className="flow-item">
      <span>{label}</span>
      <strong className={tone === "buy" ? "positive" : "negative"}>{formatKrw(value)}</strong>
    </div>
  );
}

function Status({ icon, label, value }: { icon: React.ReactNode; label: string; value: string }) {
  return (
    <div className="status">
      {icon}
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function formatKrw(value: number) {
  const abs = Math.abs(value);
  const sign = value < 0 ? "-" : "";
  if (abs >= 1_0000_0000) return `${sign}${(abs / 1_0000_0000).toFixed(1)}억`;
  if (abs >= 10_000) return `${sign}${(abs / 10_000).toFixed(0)}만`;
  return `${sign}${abs.toLocaleString("ko-KR")}`;
}

function formatPrice(market: Market, value: number) {
  if (market === "KRW-XRP") return `${value.toLocaleString("ko-KR")}원`;
  return `${Math.round(value).toLocaleString("ko-KR")}원`;
}

function formatCount(value: number) {
  return value.toLocaleString("ko-KR");
}

function toKst(value: string) {
  return new Intl.DateTimeFormat("ko-KR", {
    timeZone: "Asia/Seoul",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  }).format(new Date(value));
}

function personaLabel(value: Persona) {
  const labels: Record<Persona, string> = {
    accumulation: "Accumulation",
    breakout: "Breakout",
    distribution_trap: "Distribution trap",
    panic_sell: "Panic sell",
    retail_chop: "Retail chop",
    sleep: "Sleep",
  };
  return labels[value];
}

createRoot(document.getElementById("root")!).render(<App />);
