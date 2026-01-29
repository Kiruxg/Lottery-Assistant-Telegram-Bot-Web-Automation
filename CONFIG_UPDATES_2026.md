# Configuration Updates - January 27, 2026

## Critical Updates Based on Official Fact Sheet

### 1. Mega Millions Ticket Cost ✅ FIXED
- **Was**: $2.00 (incorrect)
- **Now**: $5.00 (correct - price increased in 2025/2026)
- **Impact**: This significantly affects EV calculations. With $5 tickets, break-even jackpot is much higher.

### 2. Lucky Day Lotto Odds ✅ FIXED
- **Was**: 1 in 575,757 (incorrect)
- **Now**: 1 in 1,221,759 (correct)
- **Impact**: This is a MAJOR correction - the odds are actually worse than previously configured, which means:
  - EV calculations were showing better values than reality
  - Break-even jackpot is higher than previously calculated
  - All historical EV calculations need to be re-evaluated

### 3. Verified Correct Settings
- **Powerball**: $2.00 ticket cost ✅
- **Powerball Odds**: 1 in 292,201,338 ✅
- **Mega Millions Odds**: 1 in 302,575,350 ✅
- **Lucky Day Lotto**: $1.00 ticket cost ✅
- **Draw Times**: All correct ✅

## Impact on EV Calculations

### Mega Millions ($285M jackpot)
- **Before (wrong $2 ticket)**: Net EV = -$1.49, EV% = -74.40%
- **After (correct $5 ticket)**: Net EV = -$4.49, EV% = -89.76%
- **Break-even**: Now $3.8B (was $1.4B with wrong ticket cost)

### Lucky Day Lotto ($450K jackpot)
- **Before (wrong odds 575,757)**: Net EV = -$0.60, EV% = -59.96%
- **After (correct odds 1,221,759)**: Net EV = -$0.76, EV% = -75.85%
- **Break-even**: Now $1.7M (was $1.3M with wrong odds)

## Action Required

1. ✅ **Config updated** - All values now match official fact sheet
2. ⚠️ **Historical data** - Any stored EV calculations from before this update are incorrect
3. ⚠️ **User notifications** - Users may notice EV values are now more negative (more accurate)

## Verification

All values have been verified against the official fact sheet provided on January 27, 2026.
