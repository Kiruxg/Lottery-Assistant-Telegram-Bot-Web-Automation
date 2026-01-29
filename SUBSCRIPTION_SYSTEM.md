# 🎯 Game Subscription System

## Overview

Users must now **subscribe to specific games** to receive alerts. This prevents message spam and creates clear value differentiation between tiers.

---

## 🎮 How It Works

### **Subscription Model**
- **1 Subscription = 1 Game = 1 Set of Alerts**
- Users only receive messages for games they're subscribed to
- Free users can subscribe to **1 game maximum**
- Premium/Pro users can subscribe to **all games** (unlimited)

### **Subscription Commands**

#### `/subscribe <game_id>`
Subscribe to alerts for a specific game.

**Available games:**
- `lucky_day_lotto_midday`
- `lucky_day_lotto_evening`
- `powerball`
- `mega_millions`

**Example:** `/subscribe powerball`

#### `/unsubscribe <game_id>`
Unsubscribe from a game.

**Example:** `/unsubscribe powerball`

#### `/mysubscriptions`
View your current subscriptions and tier status.

---

## 💰 Tier Limits

### **Free Tier**
- ✅ Subscribe to **1 game** only
- ✅ Basic EV calculations
- ✅ 1 alert per game subscription
- ✅ Web dashboard (read-only)
- ✅ Basic Telegram bot commands
- ❌ Buy signals
- ❌ Multiple game subscriptions
- ❌ Custom thresholds

### **Premium Tier ($9.99/month)**
- ✅ Subscribe to **ALL games** (unlimited)
- ✅ Advanced EV calculations
- ✅ Unlimited alerts per game
- ✅ Buy signal recommendations
- ✅ Purchase automation
- ✅ Full Telegram bot access
- ✅ 90-day history
- ✅ Custom thresholds per game
- ✅ Priority support
- ✅ Game comparison feature

### **Pro Tier ($19.99/month)**
- ✅ Everything in Premium
- ✅ Multi-state lottery support
- ✅ Advanced analytics & charts
- ✅ Data export (CSV/JSON)
- ✅ Custom alert schedules
- ✅ Unlimited history
- ✅ Email & SMS alerts
- ✅ Historical trend analysis
- ✅ Custom dashboard layouts
- ✅ Share alerts with family/friends

---

## 🔧 Technical Implementation

### **Files Created/Modified**

1. **`src/subscription_manager.py`** (NEW)
   - Manages user subscriptions
   - Enforces tier-based limits
   - Stores subscriptions in `user_subscriptions.json`

2. **`src/telegram_bot.py`** (MODIFIED)
   - Added `/subscribe` command
   - Added `/unsubscribe` command
   - Added `/mysubscriptions` command
   - Updated `/start` and `/help` commands

3. **`src/lottery_assistant.py`** (MODIFIED)
   - Checks subscriptions before sending messages
   - Only sends to users subscribed to specific game
   - Added `_send_to_subscribers()` helper method

4. **`templates/pricing.html`** (MODIFIED)
   - Updated Free tier: "Subscribe to 1 game only"
   - Updated Premium tier: "Subscribe to ALL games (unlimited)"
   - Better differentiation between tiers

### **Storage**

Subscriptions are stored in `user_subscriptions.json`:
```json
{
  "123456789": {
    "tier": "free",
    "games": ["powerball"]
  },
  "987654321": {
    "tier": "premium",
    "games": ["powerball", "mega_millions", "lucky_day_lotto_midday"]
  }
}
```

---

## 🚀 Usage

### **For Users**

1. **Start the bot:** `/start`
2. **Subscribe to a game:** `/subscribe powerball`
3. **View subscriptions:** `/mysubscriptions`
4. **Unsubscribe:** `/unsubscribe powerball`

### **For Developers**

**Set user tier (for testing):**
```python
from src.subscription_manager import SubscriptionManager

manager = SubscriptionManager()
manager.set_user_tier("123456789", "premium")  # or "free", "pro"
```

**Check if user is subscribed:**
```python
is_subscribed = manager.is_subscribed("123456789", "powerball")
```

**Get all subscribers for a game:**
```python
subscribers = manager.get_all_subscribers("powerball")
```

---

## ✅ Benefits

1. **No More Spam** - Users only get alerts for games they care about
2. **Clear Value** - Free tier gets a taste, Premium gets full value
3. **Better UX** - Users control what they receive
4. **Tier Differentiation** - Clear upgrade path from Free → Premium → Pro
5. **Scalable** - Easy to add more games or features per tier

---

## 📝 Migration Notes

**Existing Users:**
- All existing users default to "free" tier
- They need to subscribe to games manually using `/subscribe`
- No automatic subscriptions (prevents spam)

**Backward Compatibility:**
- `/status` command still works (doesn't require subscription)
- Manual commands don't require subscriptions
- Only automated alerts require subscriptions

---

**Last Updated**: 2026-01-27
**Status**: ✅ Implemented and Ready
