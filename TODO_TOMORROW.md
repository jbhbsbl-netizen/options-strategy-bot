# TODO for Tomorrow - February 15, 2026

## 🚨 Priority Issues

### 1. **Speed Issue - Still Too Slow**
**Problem:** Bot took **7-9 minutes** on last run (expected 2-3 minutes)

**Expected:**
- 9 questions total (5 stock + 4 strategy)
- ~20 articles
- 2-3 minutes

**Actual:**
- Unknown question count
- Unknown article count
- 7-9 minutes ⚠️

**Investigation Needed:**
- [ ] Check console output - how many questions actually generated?
- [ ] Check article counts - are we scraping too many?
- [ ] Check satisfaction logic - is it working?
- [ ] Check LLM categorization - are questions being marked LLM-only?
- [ ] Time each phase to find bottleneck

**Possible Causes:**
- LLM question generation creating too many questions
- Satisfaction check not stopping early enough
- Search/scraping taking longer than expected
- Network latency issues

---

### 2. **Clarify Conviction Meaning in UI**

**Current:** Conviction field shows as "75% Conviction" with no explanation

**What It Actually Means:**
- Conviction = **Confidence in the DIRECTION**, not magnitude
- `BULLISH + 90%` = "Very confident stock will go UP"
- `BULLISH + 30%` = "Weakly think it goes up, uncertain"

**User Wants:**
- Make this clearer in the UI
- Add tooltip or explanation
- Show what conviction means in context

**Implementation Ideas:**
```python
# Option 1: Tooltip
"🟢 BULLISH - 75% Conviction"
ℹ️ Hover: "75% confident the stock will move UP"

# Option 2: Descriptive text
"🟢 BULLISH Direction"
"75% Confidence in upward move"

# Option 3: Plain English
"Moderately confident (75%) the stock will go UP"
```

**Files to Modify:**
- `app_professional.py` - Results page, thesis display section

---

### 3. **Display More Research/Thesis/Thoughts**

**Problem:** Bot does tons of research but user only sees ~10 sentences of output

**User Wants:**
- More detailed research findings
- More thesis explanation
- More reasoning/thought process
- Show what the bot learned from articles

**Current Display:**
- Thesis summary: 2-3 sentences
- Research insights: 5-10 sentences (if populated)
- Strategy rationale: 2-3 sentences
- Strategy explanation: 5-8 sentences

**What's Missing:**
- Specific findings from SEC filings
- Key data points discovered
- Article-by-article insights
- Reasoning chain (how research → thesis)
- Bull/bear case details (currently hidden in expander)

**Possible Solution: Use ChatGPT to Synthesize**

**Idea:** After research completes, use LLM to create:

1. **Research Summary (Detailed)**
   ```
   Input: All articles + questions
   Output: "Key Findings" section with:
   - 10-K Highlights: [Revenue growth, margin trends, risks]
   - 10-Q Updates: [Recent quarter performance, guidance]
   - Market Sentiment: [Analyst views, price targets]
   - Competitive Position: [Market share, advantages]
   ```

2. **Thesis Reasoning Chain**
   ```
   Input: Research findings + thesis
   Output: "How We Got Here" section with:
   - "Based on 10-K data showing 45% revenue growth..."
   - "Analysts are bullish with $200 avg target..."
   - "Therefore: BULLISH thesis with 75% conviction"
   ```

3. **Strategy Selection Reasoning**
   ```
   Input: Thesis + strategy research
   Output: "Why This Strategy" section with:
   - "Given 75% conviction (moderate), we want defined risk"
   - "Bull Call Spread limits downside to $X"
   - "Research shows 70 delta works best for this IV environment"
   ```

**Implementation:**
- [ ] Add `_synthesize_research_summary()` method
- [ ] Add `_explain_thesis_reasoning()` method
- [ ] Add `_explain_strategy_choice()` method
- [ ] Display these in expandable sections on results page

**Files to Modify:**
- `src/research/research_orchestrator.py` - Add synthesis methods
- `src/ai/thesis_generator_v3.py` - Add reasoning chain
- `app_professional.py` - Display detailed findings

---

## 📋 Implementation Plan for Tomorrow

### Step 1: Investigate Speed Issue (30 min)
- [ ] Run bot with NVDA
- [ ] Watch console output carefully
- [ ] Count actual questions/articles
- [ ] Time each phase
- [ ] Identify bottleneck

### Step 2: Fix Speed (if needed) (30 min)
- [ ] Adjust limits if generating too many questions
- [ ] Fix satisfaction logic if not working
- [ ] Optimize slowest phase

### Step 3: Add Conviction Tooltip/Explanation (15 min)
- [ ] Add clear text explaining conviction
- [ ] Test that it displays correctly

### Step 4: Implement Research Display (2-3 hours)
- [ ] Add LLM synthesis for research summary
- [ ] Add reasoning chain for thesis
- [ ] Add detailed strategy explanation
- [ ] Create expandable sections in UI
- [ ] Test with real analysis

### Step 5: Test Everything (30 min)
- [ ] Full end-to-end test with NVDA
- [ ] Verify speed < 3 minutes
- [ ] Verify detailed display works
- [ ] Verify conviction is clear

---

## 💡 Design Ideas for Research Display

### Option A: Collapsible Sections (Recommended)
```
📊 Investment Thesis
🟢 BULLISH - 75% Confident in upward move

▼ 🔬 Research Highlights (Click to expand)
  10-K Findings:
  - Revenue grew 45% YoY to $26.9B
  - Data center segment: 78% of revenue
  - Operating margin improved to 32%

  10-Q Updates:
  - Q4 beat expectations by 12%
  - Guidance raised for FY2025
  - New AI chip demand strong

  Analyst Sentiment:
  - Average price target: $200 (+12% upside)
  - 18 buys, 2 holds, 0 sells
  - Consensus: Strong Buy

▼ 🧠 How We Got Here (Click to expand)
  "Based on 10-K data showing 45% revenue growth and improving margins,
   combined with strong analyst sentiment (avg PT $200) and positive
   10-Q earnings beat, we have moderate-to-high confidence (75%) that
   NVDA will continue its upward trend."

▼ 🎯 Why Bull Call Spread (Click to expand)
  "Given 75% conviction (not certain enough for naked calls), we chose
   a Bull Call Spread to limit downside risk while capturing upside.
   Research shows 70 delta long leg and 30 delta short leg work best
   for this IV environment (35 percentile)."
```

### Option B: Always-Visible Summary
```
📊 Investment Thesis
🟢 BULLISH Direction
📊 75% Confidence (Moderately confident stock will move UP)

Key Research Findings:
✓ 10-K: 45% revenue growth, strong margins
✓ 10-Q: Beat expectations, raised guidance
✓ Analysts: $200 avg target (18 buys)

Reasoning: "Strong fundamentals + positive sentiment = moderate bullish conviction"
```

---

## 🎯 Success Criteria for Tomorrow

### Speed:
- [ ] Analysis completes in **< 4 minutes** (current: 7-9 min)
- [ ] Console shows expected question/article counts

### Clarity:
- [ ] Conviction meaning is obvious to user
- [ ] No confusion about what 75% means

### Display:
- [ ] User can see detailed research findings
- [ ] User understands how bot got to its thesis
- [ ] User knows why bot chose this strategy
- [ ] Information is organized and not overwhelming

---

## 📝 Notes

**From User:**
- "I think its good the way it is" (conviction interpretation)
- "just note we have to make that more clear to the user"
- "it took about 7-9 minutes to run last time"
- "we need to get the bot to display more of its research, more of its thesis, and more of its thoughts"
- "possibly chatgpt can help us do that in some way"

**Current Status:**
- Hybrid model implemented ✅
- Real contracts working ✅
- SEC filings guaranteed ✅
- BUT: Speed slower than expected ⚠️
- BUT: Research display minimal ⚠️

---

## 🔧 Technical Approach for Research Display

### Method 1: Post-Analysis Synthesis
```python
def synthesize_research_display(research: ComprehensiveResearch, thesis: InvestmentThesis):
    """Use LLM to create detailed, readable research summary."""

    # Combine all research
    sec_articles = [a for a in research.stock_research.articles if "10-k" in a.title.lower() or "10-q" in a.title.lower()]
    other_articles = [a for a in research.stock_research.articles if a not in sec_articles]

    prompt = f"""Summarize this research in a clear, organized way for a user making investment decisions:

SEC FILINGS:
{format_articles(sec_articles)}

OTHER RESEARCH:
{format_articles(other_articles)}

THESIS GENERATED:
Direction: {thesis.direction}
Conviction: {thesis.conviction}%
Summary: {thesis.thesis_summary}

Create a "Key Findings" section with:
1. SEC Filing Highlights (3-5 bullet points with specific numbers)
2. Market Sentiment (analyst views, price targets)
3. Reasoning Chain (how research led to this thesis)

Be specific with data. Use bullet points. Keep it scannable."""

    return call_llm(prompt)
```

### Method 2: Real-Time Article Summaries
```python
# As articles are read, summarize key points
for article in articles:
    key_points = extract_key_points_llm(article)
    article.summary = key_points

# Then display summaries in UI
```

---

## 📚 Reference

**Files to Review Tomorrow:**
- `src/research/research_orchestrator.py` - Check actual question counts
- `src/ai/thesis_generator_v3.py` - Where thesis is generated
- `app_professional.py` - Results display section
- `src/models/thesis.py` - Data model fields

**Questions to Answer:**
1. Why is it taking 7-9 minutes? (Expected 2-3)
2. How many questions are actually being generated?
3. How many articles are actually being scraped?
4. Is the satisfaction logic working?
5. Are LLM-only questions being categorized correctly?

---

**Ready to tackle tomorrow!** 🚀
