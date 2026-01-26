# Per-Game Threshold Configuration

## Overview

The threshold alert system now supports **per-game configuration**. This means you can set different threshold settings for each lottery game, or disable thresholds for specific games.

## Current Configuration

### Lucky Day Lotto (Midday & Evening)
- **Min Threshold**: $500,000
- **Step Increment**: $50,000
- **Alerts**: Enabled ✅

### Powerball & Mega Millions
- **Min Threshold**: `null` (disabled)
- **Step Increment**: `null` (disabled)
- **Alerts**: Disabled ❌

## How It Works

1. **Per-Game Settings**: Each game in `config.json` can have its own `min_threshold` and `step_increment` values
2. **Fallback Defaults**: If a game doesn't specify thresholds, it falls back to `.env` values (currently only used for Lucky Day Lotto)
3. **Disabled Games**: Set `min_threshold: null` to disable threshold alerts for that game

## Configuration File (`config.json`)

```json
{
  "lottery_games": {
    "lucky_day_lotto_evening": {
      "min_threshold": 500000,      // Minimum jackpot to start alerting
      "step_increment": 50000       // Alert every $50K increase
    },
    "powerball": {
      "min_threshold": null,        // No threshold alerts
      "step_increment": null        // No threshold alerts
    }
  }
}
```

## Customizing Thresholds

### For Lucky Day Lotto Only

Edit `config.json` and modify the `min_threshold` and `step_increment` values:

```json
"lucky_day_lotto_evening": {
  "min_threshold": 1000000,    // Only alert if jackpot >= $1M
  "step_increment": 100000     // Alert every $100K increase
}
```

### To Enable Thresholds for Powerball/Mega Millions

Edit `config.json`:

```json
"powerball": {
  "min_threshold": 100000000,  // Alert if jackpot >= $100M
  "step_increment": 10000000   // Alert every $10M increase
}
```

### To Disable Thresholds for Lucky Day Lotto

Set values to `null`:

```json
"lucky_day_lotto_evening": {
  "min_threshold": null,
  "step_increment": null
}
```

## Environment Variables (`.env`)

The `.env` file values (`MIN_JACKPOT_THRESHOLD` and `JACKPOT_STEP_INCREMENT`) are now **fallback defaults** only. They're used if a game doesn't specify its own thresholds in `config.json`.

**Note**: Currently, these are only used for Lucky Day Lotto, but you can override them per-game in `config.json`.

## Examples

### Example 1: Different thresholds for different games
```json
"lucky_day_lotto_evening": {
  "min_threshold": 500000,
  "step_increment": 50000
},
"powerball": {
  "min_threshold": 100000000,
  "step_increment": 10000000
}
```

### Example 2: No thresholds for any game
Set all games to `null`:
```json
"lucky_day_lotto_evening": {
  "min_threshold": null,
  "step_increment": null
}
```

## Testing

After changing thresholds:
1. Save `config.json`
2. Run: `python main.py check`
3. Check logs: `lottery_assistant.log`

The system will use the per-game thresholds from `config.json` and only send alerts for games with thresholds configured.
