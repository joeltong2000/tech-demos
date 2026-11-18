"""Specialized agent roles mirroring TradingAgents team structure."""

from __future__ import annotations

from dataclasses import dataclass

from tradingagents_debate.llm import LLMClient, OpenAICompatLLM
from tradingagents_debate.market import MarketSnapshot


@dataclass(frozen=True)
class AgentMessage:
    role: str
    title: str
    content: str


def _avg_sentiment(snapshot: MarketSnapshot) -> float:
    if not snapshot.headlines:
        return 0.0
    return sum(float(h["sentiment"]) for h in snapshot.headlines) / len(snapshot.headlines)


def _pe_label(pe: float | None) -> str:
    if pe is None:
        return "n/a (pre-profit / pre-revenue)"
    if pe > 50:
        return f"{pe:.1f} (rich)"
    if pe < 25:
        return f"{pe:.1f} (reasonable vs growth)"
    return f"{pe:.1f} (elevated)"


class DebateAgents:
    """Produce analyst → researcher → trader → risk messages."""

    def __init__(self, llm: LLMClient, *, seed: int = 42) -> None:
        self.llm = llm
        self.seed = seed

    def _live(self) -> bool:
        return isinstance(self.llm, OpenAICompatLLM)

    def fundamentals_analyst(self, snap: MarketSnapshot) -> AgentMessage:
        f = snap.fundamentals
        pe = f.get("pe_ratio")
        body = (
            f"{snap.name} ({snap.ticker}) — {snap.sector}. "
            f"TTM revenue ${f['revenue_ttm_b']}B, YoY {f['revenue_yoy_pct']}%, "
            f"gross margin {f['gross_margin_pct']}%, D/E {f['debt_to_equity']}, "
            f"P/E {_pe_label(pe)}. Note: {f['notes']}"
        )
        if self._live():
            content = self.llm.complete(
                "You are a fundamentals analyst. Be concise (3-5 sentences).",
                body,
                role="fundamentals",
            )
        else:
            lean = "constructive" if float(f["revenue_yoy_pct"]) > 20 else "cautious"
            content = f"Fundamentals lean {lean}: {body}"
        return AgentMessage("Fundamentals Analyst", "Company fundamentals", content)

    def sentiment_analyst(self, snap: MarketSnapshot) -> AgentMessage:
        avg = _avg_sentiment(snap)
        samples = "; ".join(f"\"{h['headline']}\" ({h['sentiment']:+.2f})" for h in snap.headlines[:3])
        tone = "bullish" if avg > 0.2 else "bearish" if avg < -0.1 else "mixed"
        body = f"Avg headline sentiment {avg:+.2f} → {tone}. Samples: {samples}."
        if self._live():
            content = self.llm.complete(
                "You are a sentiment analyst. Summarize market mood briefly.",
                body,
                role="sentiment",
            )
        else:
            content = f"Short-term mood looks {tone}. {body}"
        return AgentMessage("Sentiment Analyst", "Headline / social mood", content)

    def news_analyst(self, snap: MarketSnapshot) -> AgentMessage:
        latest = sorted(snap.headlines, key=lambda h: h["date"], reverse=True)[:2]
        bullets = " | ".join(f"[{h['date']}] {h['headline']}" for h in latest)
        if self._live():
            content = self.llm.complete(
                "You are a news analyst for equities. Flag catalysts and risks.",
                f"As of {snap.as_of}. Headlines: {bullets}",
                role="news",
            )
        else:
            risk = next((h for h in snap.headlines if float(h["sentiment"]) < 0), None)
            catalyst = next((h for h in snap.headlines if float(h["sentiment"]) > 0.3), None)
            content = (
                f"As of {snap.as_of}: key wires — {bullets}. "
                f"Primary catalyst: {catalyst['headline'] if catalyst else 'none clear'}. "
                f"Primary risk: {risk['headline'] if risk else 'none flagged'}."
            )
        return AgentMessage("News Analyst", "Macro / event tape", content)

    def technical_analyst(self, snap: MarketSnapshot) -> AgentMessage:
        t = snap.technicals
        body = (
            f"Last {t.last_close}, SMA5 {t.sma_5}, SMA20 {t.sma_20}, "
            f"RSI14 {t.rsi_14}, 5d momentum {t.momentum_5d_pct:+.2f}%, "
            f"trend={t.trend}, avg vol5={t.avg_volume_5:,.0f}."
        )
        if self._live():
            content = self.llm.complete(
                "You are a technical analyst. Interpret indicators briefly.",
                body,
                role="technical",
            )
        else:
            bias = (
                "momentum supportive"
                if t.trend == "uptrend" and t.rsi_14 < 70
                else "caution on mean-reversion / soft tape"
                if t.trend != "uptrend"
                else "extended; wait for pullback"
            )
            content = f"Technicals: {bias}. {body}"
        return AgentMessage("Technical Analyst", "Price / indicators", content)

    def bull_researcher(self, snap: MarketSnapshot, briefs: list[AgentMessage]) -> AgentMessage:
        digest = " ".join(m.content for m in briefs)
        if self._live():
            content = self.llm.complete(
                "You are a bullish researcher. Argue the long case in 4 sentences.",
                f"Ticker {snap.ticker}. Analyst briefs: {digest}",
                role="bull",
            )
        else:
            f = snap.fundamentals
            content = (
                f"BULL case for {snap.ticker}: growth ({f['revenue_yoy_pct']}% YoY) and "
                f"sector positioning outweigh near-term noise. Price {snap.last_close} with "
                f"trend={snap.technicals.trend} and RSI {snap.technicals.rsi_14}. "
                f"Positive tape can extend if catalysts in the briefs hold. "
                f"Risk/reward favors accumulating on dips, not chasing blindly."
            )
        return AgentMessage("Bull Researcher", "Long thesis", content)

    def bear_researcher(self, snap: MarketSnapshot, briefs: list[AgentMessage]) -> AgentMessage:
        digest = " ".join(m.content for m in briefs)
        if self._live():
            content = self.llm.complete(
                "You are a bearish researcher. Argue the short/cautious case in 4 sentences.",
                f"Ticker {snap.ticker}. Analyst briefs: {digest}",
                role="bear",
            )
        else:
            pe = snap.fundamentals.get("pe_ratio")
            content = (
                f"BEAR case for {snap.ticker}: valuation "
                f"({_pe_label(pe)}) leaves little room for disappointment. "
                f"Negative headlines and {snap.technicals.momentum_5d_pct:+.2f}% 5d momentum "
                f"argue for patience. Asymmetry favors waiting or trimming strength. "
                f"Capital preservation > forced exposure given bundled risks in the briefs."
            )
        return AgentMessage("Bear Researcher", "Short / caution thesis", content)

    def trader(
        self,
        snap: MarketSnapshot,
        briefs: list[AgentMessage],
        bull: AgentMessage,
        bear: AgentMessage,
        *,
        cash: float,
        position: float,
    ) -> AgentMessage:
        avg_sent = _avg_sentiment(snap)
        t = snap.technicals
        # Deterministic heuristic proposal for mock mode.
        score = 0
        if float(snap.fundamentals["revenue_yoy_pct"]) > 25:
            score += 2
        elif float(snap.fundamentals["revenue_yoy_pct"]) < 5:
            score -= 1
        if avg_sent > 0.2:
            score += 1
        elif avg_sent < -0.15:
            score -= 1
        if t.trend == "uptrend" and t.rsi_14 < 68:
            score += 2
        elif t.rsi_14 > 72 or t.trend == "overextended_or_soft":
            score -= 1
        if snap.fundamentals.get("pe_ratio") is None:
            score -= 1  # speculative names

        max_buy = max(0.0, cash / snap.last_close * 0.35)
        if score >= 3:
            action, size = "BUY", round(min(max_buy, max(1.0, max_buy)), 2)
            if size < 1 and max_buy >= 0.1:
                size = round(max_buy, 2)
        elif score <= 0 and position > 0:
            action, size = "SELL", round(min(position, max(position * 0.5, 1.0)), 2)
        elif score <= 0:
            action, size = "HOLD", 0.0
        else:
            action, size = "HOLD", 0.0

        prompt = (
            f"Cash ${cash:.2f}, position {position:g} shares, price {snap.last_close}. "
            f"Bull: {bull.content} Bear: {bear.content}"
        )
        if self._live():
            content = self.llm.complete(
                "You are a trader. End with exactly: FINAL DECISION: BUY|SELL|HOLD size=N",
                prompt,
                role="trader",
            )
        else:
            content = (
                f"Trader proposal after weighing bull/bear and analyst stack "
                f"(internal score={score}). "
                f"FINAL DECISION: {action} size={size:g}"
            )
        return AgentMessage("Trader", "Trade proposal", content)

    def risk_manager(
        self,
        snap: MarketSnapshot,
        trader_msg: AgentMessage,
        *,
        cash: float,
        position: float,
        proposed_action: str,
        proposed_size: float,
    ) -> AgentMessage:
        notional = proposed_size * snap.last_close
        # Reject oversized buys or sells beyond inventory.
        reject = False
        reason = "within paper-risk limits"
        if proposed_action == "BUY" and notional > cash * 0.4:
            reject = True
            reason = "buy notional exceeds 40% of cash"
        elif proposed_action == "SELL" and proposed_size > position + 1e-9:
            reject = True
            reason = "sell size exceeds current position"
        elif proposed_action == "BUY" and snap.technicals.rsi_14 > 78:
            reject = True
            reason = "RSI too extended for new risk"

        verdict = "REJECT" if reject else "APPROVE"
        if self._live():
            content = self.llm.complete(
                "You are a risk manager. Reply with APPROVE or REJECT and a short reason. "
                "Restate FINAL DECISION.",
                f"Proposal: {trader_msg.content}. Cash={cash}, pos={position}, "
                f"RSI={snap.technicals.rsi_14}",
                role="risk",
            )
        else:
            final_action = "HOLD" if reject else proposed_action
            final_size = 0.0 if reject else proposed_size
            content = (
                f"Risk Manager: {verdict} — {reason}. "
                f"Portfolio cash ${cash:.2f}, position {position:g}. "
                f"FINAL DECISION: {final_action} size={final_size:g}"
            )
        return AgentMessage("Risk Manager", "Risk / portfolio check", content)
