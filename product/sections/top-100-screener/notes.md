# Top 100 High-Conviction Screener - Design Notes

## Core Feature
- Scan top 100 most liquid options stocks daily
- Filter for ≥90% conviction setups
- Display ranked opportunities
- User clicks ticker → full analysis

## Critical Rules
1. **NEVER force convictions** - If no stocks are ≥90%, say so clearly
2. **Honest reporting** - Show "No high-conviction setups today" when true
3. **User-adjustable threshold** - Allow lowering to 70-80% if desired

## Schedule
- **Run frequency:** Once daily at 4:30 PM ET (after market close)
- **Analysis depth:** Price + fundamentals + news summaries (skip full articles/10-K for speed)
- **10-K caching:** Parse quarterly, reuse daily

## Storage
- **Database:** SQLite
- **Schema:** stock_analysis table (ticker, date, direction, conviction, thesis, strategy)
- **Retention:** Keep 30 days of history

## Cost
- ~100 stocks × $0.01 = $1/day = $30/month
- Affordable for value provided

## UI
```
🔍 HIGH-CONVICTION OPPORTUNITIES (≥90%)
Last scan: Feb 10, 2025 4:45 PM ET

[Table: Ticker, Conv%, Direction, Expected Move, Strategy]

If no ≥90%:
"No setups meet the 90% conviction threshold today
 Highest found: 78% (NVDA - BULLISH)
 [Lower threshold to 70%] to see more"
```

## IMPORTANT FEATURE REQUEST
**Enable/Disable Toggle:**
- Add setting to turn off automated daily scanning
- Saves $30/month when not actively trading
- Options:
  - "Auto-scan: ON/OFF"
  - "Manual scan: [Scan Now]" (on-demand, user pays per scan)
  - "Pause until: [Date picker]" (vacation mode)

**Implementation:**
```python
# config.py
SCANNER_ENABLED = os.getenv("SCANNER_ENABLED", "true").lower() == "true"

# background_job.py
if SCANNER_ENABLED:
    scheduler.add_job(scan_top_100, 'cron', hour=16, minute=30)
else:
    print("Scanner disabled - set SCANNER_ENABLED=true to enable")
```

**UI Toggle:**
```
┌────────────────────────────────────────┐
│ Settings                               │
├────────────────────────────────────────┤
│ Daily Auto-Scan: [ON] OFF              │
│                                        │
│ Cost: ~$30/month when enabled          │
│ Last scan: Feb 10, 2025 4:45 PM        │
│                                        │
│ [Run Manual Scan Now] ($1.00)          │
└────────────────────────────────────────┘
```

## Build Priority
- **Now:** Finish single-ticker flow (contract picker → P&L → UI)
- **Then:** Add screener (reuses all single-ticker logic)
- **Finally:** Add enable/disable toggle for cost control
