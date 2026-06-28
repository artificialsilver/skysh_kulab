import React from "react";
import { createRoot } from "react-dom/client";
import {
  ArrowLeft,
  Info,
  Plus,
  RefreshCw,
  Search,
  Waves,
  X,
} from "lucide-react";
import "./styles.css";

type Market = "KRW-BTC" | "KRW-ETH" | "KRW-XRP";
type Timeframe = "15m" | "4h";
type Persona = "accumulation" | "breakout" | "distribution_trap" | "panic_sell" | "retail_chop" | "sleep";
type MainTab = "watchlist" | "alerts";

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

type SnapshotsResponse = {
  snapshots: Snapshot[];
};

type PersonaResponse = PersonaSnapshot & {
  market: Market;
  timeframe: Timeframe;
  snapshot_at: string;
};

type AlertSettingResponse = {
  enabled: boolean;
};

type TickersResponse = {
  tickers: Partial<Record<Market, { price: number }>>;
};

type MarketRow = {
  market: Market;
  snapshot?: Snapshot;
  persona?: PersonaSnapshot;
};

const markets: Market[] = ["KRW-BTC", "KRW-ETH", "KRW-XRP"];
const timeframes: Timeframe[] = ["15m", "4h"];

function isMarket(value: string | null): value is Market {
  return value !== null && (markets as string[]).includes(value);
}

function readDetailMarket(): Market | null {
  const route = new URLSearchParams(window.location.hash.replace(/^#/, ""));
  const detailMarket = route.get("detail");
  return isMarket(detailMarket) ? detailMarket : null;
}

const PERSONA_UI: Record<Persona, { name: string; insight: string }> = {
  breakout: {
    name: "폭주 기관차",
    insight: "고래 매수세와 거래량이 함께 붙으며 가격 상승을 강하게 밀어올리는 구간입니다.",
  },
  panic_sell: {
    name: "무자비한 불도저",
    insight: "고래 매도 압력과 큰 변동성이 겹치며 하락이 빠르게 진행되는 위험 구간입니다.",
  },
  distribution_trap: {
    name: "교활한 낚시꾼",
    insight: "가격은 버티거나 오르지만 고래는 빠지고 개미가 받아내는 수급 불일치 구간입니다.",
  },
  accumulation: {
    name: "심해의 진공청소기",
    insight: "가격은 조용하지만 고래 순매수가 쌓이며 매집 가능성이 보이는 구간입니다.",
  },
  retail_chop: {
    name: "시끄러운 시장통",
    insight: "뚜렷한 주도 세력 없이 개미 수급 중심으로 짧은 등락이 반복되는 구간입니다.",
  },
  sleep: {
    name: "겨울잠 자는 곰",
    insight: "거래와 수급이 모두 잠잠해 의미 있는 방향성이 거의 보이지 않는 관망 구간입니다.",
  },
};

const series = [42, 46, 43, 51, 57, 55, 64, 62, 68, 73, 69, 78, 82, 80, 88];

function App() {
  const [selectedMarket, setSelectedMarket] = React.useState<Market | null>(null);
  const [activeMainTab, setActiveMainTab] = React.useState<MainTab>("watchlist");
  const [watchlist, setWatchlist] = React.useState<Market[]>(markets);
  const [timeframe, setTimeframe] = React.useState<Timeframe>("15m");
  const [searchOpen, setSearchOpen] = React.useState(false);
  const [alertMarkets, setAlertMarkets] = React.useState<Market[]>(["KRW-BTC"]);
  const [alertPersonas, setAlertPersonas] = React.useState<Persona[]>(["breakout", "panic_sell", "distribution_trap"]);
  const [apiSnapshots, setApiSnapshots] = React.useState<Partial<Record<Market, Snapshot>>>({});
  const [apiPersonas, setApiPersonas] = React.useState<Partial<Record<Market, PersonaSnapshot>>>({});
  const [tickerPrices, setTickerPrices] = React.useState<Partial<Record<Market, number>>>({});
  const [apiReady, setApiReady] = React.useState(false);

  React.useEffect(() => {
    function syncDetailRoute() {
      setSelectedMarket(readDetailMarket());
    }

    syncDetailRoute();
    window.addEventListener("hashchange", syncDetailRoute);
    return () => window.removeEventListener("hashchange", syncDetailRoute);
  }, []);

  React.useEffect(() => {
    let cancelled = false;

    async function loadMarketData() {
      try {
        const pairs = await Promise.all(
          markets.map(async (item) => {
            const [snapshotResponse, personaResponse] = await Promise.all([
              fetch(`/api/market/${item}/snapshots?timeframe=${timeframe}`),
              fetch(`/api/market/${item}/persona?timeframe=${timeframe}`),
            ]);
            if (!snapshotResponse.ok || !personaResponse.ok) {
              throw new Error("API response was not ready");
            }
            const snapshotBody = (await snapshotResponse.json()) as SnapshotsResponse;
            const personaBody = (await personaResponse.json()) as PersonaResponse;
            const latestSnapshot = snapshotBody.snapshots[0];
            if (!latestSnapshot) {
              throw new Error("API snapshot was empty");
            }
            return [item, latestSnapshot, personaBody] as const;
          }),
        );
        if (cancelled) return;
        setApiSnapshots(Object.fromEntries(pairs.map(([item, snapshotValue]) => [item, snapshotValue])));
        setApiPersonas(Object.fromEntries(pairs.map(([item, , personaValue]) => [item, personaValue])));
        setApiReady(true);
      } catch {
        if (cancelled) return;
        setApiSnapshots({});
        setApiPersonas({});
        setApiReady(false);
      }
    }

    loadMarketData();
    return () => {
      cancelled = true;
    };
  }, [timeframe]);

  React.useEffect(() => {
    let cancelled = false;

    async function loadTickers() {
      try {
        const response = await fetch("/api/tickers");
        if (!response.ok) return;
        const body = (await response.json()) as TickersResponse;
        if (!cancelled) {
          setTickerPrices(Object.fromEntries(markets.map((item) => [item, body.tickers[item]?.price]).filter(([, price]) => typeof price === "number")));
        }
      } catch {
        if (!cancelled) setTickerPrices({});
      }
    }

    loadTickers();
    const timer = window.setInterval(loadTickers, 10000);
    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, []);

  const market = selectedMarket ?? watchlist[0] ?? "KRW-BTC";
  const snapshot = apiSnapshots[market] ? withLivePrice(market, apiSnapshots[market], tickerPrices) : undefined;
  const persona = apiPersonas[market];
  const detailOpen = Boolean(selectedMarket && snapshot && persona);
  const marketRows: MarketRow[] = watchlist.map((item) => ({
    market: item,
    snapshot: apiSnapshots[item] ? withLivePrice(item, apiSnapshots[item], tickerPrices) : undefined,
    persona: apiPersonas[item],
  }));

  function addWatchMarket(nextMarket: Market) {
    if (watchlist.includes(nextMarket) || watchlist.length >= 3) return;
    setWatchlist((items) => [...items, nextMarket]);
  }

  function removeWatchMarket(nextMarket: Market) {
    setWatchlist((items) => items.filter((item) => item !== nextMarket));
    if (selectedMarket === nextMarket) window.location.hash = "watchlist";
    setAlertMarkets((items) => items.filter((item) => item !== nextMarket));
  }

  function openDetail(nextMarket: Market) {
    setSelectedMarket(nextMarket);
    window.location.hash = `detail=${encodeURIComponent(nextMarket)}`;
  }

  function closeDetail() {
    window.location.hash = "watchlist";
  }

  function toggleAlertMarket(nextMarket: Market) {
    setAlertMarkets((items) =>
      items.includes(nextMarket) ? items.filter((item) => item !== nextMarket) : [...items, nextMarket],
    );
  }

  function toggleAlertPersona(nextPersona: Persona) {
    setAlertPersonas((items) =>
      items.includes(nextPersona) ? items.filter((item) => item !== nextPersona) : [...items, nextPersona],
    );
  }

  return (
    <main className="shell">
      <div className="mesh" aria-hidden="true" />
      <header className="topbar">
        <div className="brand">
          <div className="brand-mark">S</div>
          <span>SkySH</span>
        </div>
        <nav className="nav">
          <button
            className={activeMainTab === "watchlist" ? "active" : ""}
            onClick={() => {
              setActiveMainTab("watchlist");
              window.location.hash = "watchlist";
            }}
          >
            관심종목
          </button>
          <button
            className={activeMainTab === "alerts" ? "active" : ""}
            onClick={() => {
              setActiveMainTab("alerts");
              window.location.hash = "alerts";
            }}
          >
            알림조건
          </button>
        </nav>
        <div className="actions">
          <button
            className="icon-button"
            aria-label="Search"
            onClick={() => {
              setActiveMainTab("watchlist");
              window.location.hash = "watchlist";
              setSearchOpen((value) => !value);
            }}
          >
            <Search size={18} />
          </button>
          <button className="primary-button">
            <RefreshCw size={16} />
            Sync
          </button>
        </div>
      </header>

      {!detailOpen ? (
        <>
      <section className="hero" id="watchlist">
        <div>
          <span className="tag">UTC snapshot · KST display</span>
          <h1>Watchlist console</h1>
          <p className="lead">등록된 관심종목의 Persona와 핵심 흐름을 먼저 보고, 종목을 선택해 지표 상세를 확인합니다.</p>
        </div>
        <div className="hero-controls" aria-label="Market controls">
          <div className="main-tabs" role="tablist" aria-label="Main sections">
            <button
              role="tab"
              aria-selected={activeMainTab === "watchlist"}
              className={activeMainTab === "watchlist" ? "active" : ""}
              onClick={() => setActiveMainTab("watchlist")}
            >
              관심종목
            </button>
            <button
              role="tab"
              aria-selected={activeMainTab === "alerts"}
              className={activeMainTab === "alerts" ? "active" : ""}
              onClick={() => setActiveMainTab("alerts")}
            >
              알림조건
            </button>
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

      {activeMainTab === "watchlist" && searchOpen ? (
        <section className="search-panel" aria-label="Search watchlist market">
          <div className="section-head">
            <div>
              <span className="eyebrow">Search</span>
              <h2>관심종목 추가</h2>
            </div>
            <span className="timestamp">v1에서는 3개 마켓만 등록 가능</span>
          </div>
          <div className="search-list">
            {markets.map((item) => {
              const registered = watchlist.includes(item);
              const disabled = registered || watchlist.length >= 3;
              return (
                <button key={item} className="search-row" disabled={disabled} onClick={() => addWatchMarket(item)}>
                  <span>{item}</span>
                  <em>{registered ? "등록됨" : watchlist.length >= 3 ? "최대 3개" : "추가 가능"}</em>
                  <Plus size={16} />
                </button>
              );
            })}
          </div>
        </section>
      ) : null}

      {activeMainTab === "watchlist" ? (
        <section className="watchlist-section" aria-label="Registered watchlist">
          <div className="section-head">
            <div>
              <span className="eyebrow">Watchlist</span>
              <h2>등록된 관심종목</h2>
            </div>
            <span className="timestamp">{apiReady ? "FastAPI connected" : "Mock fallback"}</span>
          </div>
          <div className="watchlist-grid">
            {marketRows.map((row) => (
              <article
                key={row.market}
                className={`watch-card ${row.market === selectedMarket ? "selected" : ""} ${!row.snapshot || !row.persona ? "empty" : ""}`}
                onClick={() => {
                  if (row.snapshot && row.persona) openDetail(row.market);
                }}
                onKeyDown={(event) => {
                  if ((event.key === "Enter" || event.key === " ") && row.snapshot && row.persona) openDetail(row.market);
                }}
                role="button"
                tabIndex={0}
              >
                <button
                  className="delete-watch"
                  aria-label={`${row.market} delete`}
                  onClick={(event) => {
                    event.stopPropagation();
                    removeWatchMarket(row.market);
                  }}
                >
                  <X size={14} />
                </button>
                {row.persona ? <PersonaBadge persona={row.persona.persona} /> : <span className="persona-icon empty"><Waves size={18} /></span>}
                <span className="watch-main">
                  <strong>{row.market}</strong>
                  <small>{row.persona ? personaInsight(row.persona.persona) : "Redis bucket과 DB snapshot이 아직 없습니다."}</small>
                </span>
                <span className="watch-kpis">
                  <span>
                    <small>현재가</small>
                    <strong>{row.snapshot ? formatPrice(row.market, row.snapshot.price_close) : formatOptionalPrice(row.market, tickerPrices[row.market])}</strong>
                  </span>
                  <span>
                    <small>변화율</small>
                    <strong className={row.snapshot && row.snapshot.price_change_pct >= 0 ? "positive" : "negative"}>
                      {row.snapshot ? `${row.snapshot.price_change_pct.toFixed(2)}%` : "-"}
                    </strong>
                  </span>
                  <span>
                    <small>고래 순매수</small>
                    <strong className={row.snapshot && row.snapshot.whale_net_ratio >= 0 ? "positive" : "negative"}>
                      {row.snapshot ? `${(row.snapshot.whale_net_ratio * 100).toFixed(2)}%` : "-"}
                    </strong>
                  </span>
                </span>
              </article>
            ))}
          </div>
        </section>
      ) : null}

      {activeMainTab === "alerts" ? (
        <section className="alert-panel" id="alerts">
          <div className="section-head">
            <div>
              <span className="eyebrow">Alert</span>
              <h2>알림 조건</h2>
            </div>
            <span className="timestamp">종목 + Persona 조합으로 수신</span>
          </div>
          <div className="alert-grid">
            <div>
              <span className="alert-label">종목</span>
              <div className="chip-row">
                {watchlist.map((item) => (
                  <button key={item} className={`chip ${alertMarkets.includes(item) ? "active" : ""}`} onClick={() => toggleAlertMarket(item)}>
                    {item}
                  </button>
                ))}
              </div>
            </div>
            <div>
              <span className="alert-label">Persona</span>
              <div className="chip-row">
                {Object.keys(PERSONA_UI).map((item) => {
                  const personaKey = item as Persona;
                  return (
                    <button
                      key={item}
                      className={`chip persona-chip ${alertPersonas.includes(personaKey) ? "active" : ""}`}
                      onClick={() => toggleAlertPersona(personaKey)}
                      aria-label={`${personaLabel(personaKey)} 알림 조건`}
                    >
                      {personaLabel(personaKey)}
                    </button>
                  );
                })}
              </div>
            </div>
          </div>
        </section>
      ) : null}
        </>
      ) : null}

      {detailOpen && selectedMarket && snapshot && persona ? (
        <section className="detail-page" aria-label={`${selectedMarket} detail`}>
          <button className="back-button" onClick={closeDetail}>
            <ArrowLeft size={18} />
            Watchlist
          </button>
          <section className="detail-header">
            <div>
              <span className="eyebrow">Selected detail</span>
              <h1>{market}</h1>
            </div>
            <div className={`persona-title ${persona.persona}`}>
              <PersonaIcon persona={persona.persona} />
              <strong>{personaLabel(persona.persona)}</strong>
            </div>
          </section>
          <section className="metrics-grid" aria-label="Snapshot metrics">
            <Metric label="현재가" value={formatPrice(market, snapshot.price_close)} trendText={formatSignedPct(snapshot.price_change_pct)} positive={snapshot.price_change_pct >= 0} explanation="선택한 timeframe의 시작가 대비 현재 종가 변화율입니다." />
            <Metric label="거래대금" value={formatKrw(snapshot.total_volume_krw)} trendText={`x${snapshot.volume_surge_ratio.toFixed(2)}`} positive={snapshot.volume_surge_ratio >= 1} explanation="최근 window의 총 거래대금과 평소 거래대금 대비 배율입니다." />
            <Metric label="고래 순매수" value={formatKrw(snapshot.whale_buy_krw - snapshot.whale_sell_krw)} trendText={formatSignedPct(snapshot.whale_net_ratio * 100)} positive={snapshot.whale_net_ratio >= 0} explanation="고래 매수 금액에서 고래 매도 금액을 뺀 값입니다." />
            <Metric label="변동성" value={`${snapshot.volatility_pct.toFixed(2)}%`} trendText={formatSignedPct(snapshot.volatility_pct)} positive={snapshot.volatility_pct >= 0} explanation="window 내 고가와 저가의 가격 흔들림 비율입니다." />
          </section>

          <section className="workbench">
            <div className="panel chart-panel">
              <div className="panel-head">
                <div>
                  <span className="eyebrow">Selected detail</span>
                  <h2>{market} · {timeframe} 상세</h2>
                </div>
                <span className="timestamp">{toKst(snapshot.snapshot_at)}</span>
              </div>
              <Chart />
              <div className="flow-grid">
                <Flow label="Whale buy" value={snapshot.whale_buy_krw} tone="buy" explanation="고래로 분류된 체결의 매수 금액입니다." />
                <Flow label="Whale sell" value={snapshot.whale_sell_krw} tone="sell" explanation="고래로 분류된 체결의 매도 금액입니다." />
                <Flow label="Retail buy" value={snapshot.retail_buy_krw} tone="buy" explanation="개인으로 분류된 체결의 매수 금액입니다." />
                <Flow label="Retail sell" value={snapshot.retail_sell_krw} tone="sell" explanation="개인으로 분류된 체결의 매도 금액입니다." />
              </div>
            </div>

            <aside className="panel persona-panel" id="persona">
              <div className="panel-head compact">
                <div>
                  <span className="eyebrow">PersonaSnapshot</span>
                  <h2>{market}</h2>
                </div>
                <PersonaBadge persona={persona.persona} dark />
              </div>
              <div className={`persona-badge ${persona.persona}`}>
                <span className="persona-badge-icon" tabIndex={0} aria-label={`${personaLabel(persona.persona)}: ${personaInsight(persona.persona)}`}>
                  <PersonaIcon persona={persona.persona} />
                  <span className="tooltip persona-tooltip">{personaInsight(persona.persona)}</span>
                </span>
                <span className="persona-badge-name">{personaLabel(persona.persona)}</span>
                <strong>{Math.round(persona.confidence * 100)}%</strong>
                <InfoTip text="Persona 판별 신뢰도입니다. 조건에 부합한 reason code 수가 많을수록 높아집니다." />
              </div>
              <p className="persona-insight">{personaInsight(persona.persona)}</p>
              <div className="reason-list">
                {persona.reason_codes.map((reason) => (
                  <span key={reason}>{reason}</span>
                ))}
              </div>
              <div className="persona-stats">
                <div>
                  <span>Trade count <InfoTip text="선택한 timeframe 안에서 집계된 총 체결 횟수입니다." /></span>
                  <strong>{formatCount(snapshot.trade_count)}</strong>
                </div>
                <div>
                  <span>Whale count <InfoTip text="선택한 timeframe 안에서 고래 기준을 넘긴 체결 횟수입니다." /></span>
                  <strong>{formatCount(snapshot.whale_count)}</strong>
                </div>
              </div>
            </aside>
          </section>
        </section>
      ) : null}
    </main>
  );
}

function Metric({ label, value, trendText, positive, explanation }: { label: string; value: string; trendText: string; positive: boolean; explanation: string }) {
  return (
    <article className="metric">
      <span>{label} <InfoTip text={explanation} /></span>
      <strong>{value}</strong>
      <em className={positive ? "positive" : "negative"}>{trendText}</em>
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

function Flow({ label, value, tone, explanation }: { label: string; value: number; tone: "buy" | "sell"; explanation: string }) {
  return (
    <div className="flow-item">
      <span>{label} <InfoTip text={explanation} /></span>
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

function PersonaIcon({ persona }: { persona: Persona }) {
  if (persona === "breakout") return <span className="shape-icon train" aria-hidden="true"><span /></span>;
  if (persona === "panic_sell") return <span className="shape-icon bulldozer" aria-hidden="true"><span /></span>;
  if (persona === "distribution_trap") return <span className="shape-icon fisher" aria-hidden="true"><span /></span>;
  if (persona === "accumulation") return <span className="shape-icon vacuum" aria-hidden="true"><span /></span>;
  if (persona === "retail_chop") return <span className="shape-icon market" aria-hidden="true"><span /></span>;
  return <span className="shape-icon bear" aria-hidden="true"><span /></span>;
}

function PersonaBadge({ persona, dark = false }: { persona: Persona; dark?: boolean }) {
  return (
    <span className={`persona-icon ${persona} ${dark ? "dark" : ""}`} tabIndex={0} aria-label={`${personaLabel(persona)}: ${personaInsight(persona)}`}>
      <PersonaIcon persona={persona} />
      <span className="tooltip persona-tooltip">{personaInsight(persona)}</span>
    </span>
  );
}

function InfoTip({ text }: { text: string }) {
  return (
    <span className="info-tip" tabIndex={0} aria-label={text}>
      <Info size={13} />
      <span className="tooltip">{text}</span>
    </span>
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

function formatOptionalPrice(market: Market, value?: number) {
  if (typeof value !== "number") return "-";
  return formatPrice(market, value);
}

function formatCount(value: number) {
  return value.toLocaleString("ko-KR");
}

function formatSignedPct(value: number) {
  return `${value >= 0 ? "+" : ""}${value.toFixed(2)}%`;
}

function withLivePrice(market: Market, snapshot: Snapshot, prices: Partial<Record<Market, number>>) {
  const livePrice = prices[market];
  if (typeof livePrice !== "number") return snapshot;
  return { ...snapshot, price_close: livePrice };
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
  return PERSONA_UI[value].name;
}

function personaInsight(value: Persona) {
  return PERSONA_UI[value].insight;
}

createRoot(document.getElementById("root")!).render(<App />);
