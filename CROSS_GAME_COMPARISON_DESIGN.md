# 🎯 Cross-Game Comparison Feature Design

## 📊 How It Works

Cross-game comparison shows all lottery games **side-by-side** so users can instantly see:
- **Which game has the best EV right now**
- **Which game is closest to positive EV**
- **Which game offers the best value for their budget**

---

## 🎨 Visual Design

### **Option 1: Comparison Table View** (Recommended)

A clean table that shows all games in one view:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    🎰 Best Value Right Now                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ⭐ BEST VALUE: Powerball                                                │
│                                                                           │
│  ┌──────────────┬──────────────┬──────────────┬──────────────┐         │
│  │              │ Lucky Day    │ Powerball    │ Mega Millions│         │
│  │              │ Lotto        │              │              │         │
│  ├──────────────┼──────────────┼──────────────┼──────────────┤         │
│  │ 💰 Jackpot   │ $400,000     │ $300,000,000 │ $285,000,000 │         │
│  │ 📊 Net EV    │ -$0.67 ❌    │ -$0.50 ⚠️    │ -$1.20 ❌    │         │
│  │ 📈 EV %      │ -67%         │ -25%         │ -24%         │         │
│  │ 💵 Ticket    │ $1.00        │ $2.00        │ $2.00        │         │
│  │ 🎯 Odds      │ 1:575,757    │ 1:292M       │ 1:302M       │         │
│  │ ⏰ Next Draw │ Tomorrow     │ Tonight      │ Tonight      │         │
│  │ 🏆 Rank      │ #3           │ #1 ⭐        │ #2           │         │
│  └──────────────┴──────────────┴──────────────┴──────────────┘         │
│                                                                           │
│  💡 Recommendation: If you only buy one ticket, buy Powerball          │
│     (Best EV: -$0.50, closest to break-even)                            │
└─────────────────────────────────────────────────────────────────────────┘
```

### **Option 2: Card Comparison View**

Keep current card layout but add a "Comparison Mode" toggle:

```
┌─────────────────────────────────────────────────────────────────────────┐
│  [View Mode: Individual ▼] [Comparison Mode]                           │
└─────────────────────────────────────────────────────────────────────────┘

┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ Lucky Day    │  │ Powerball    │  │ Mega Millions│
│ Lotto        │  │ ⭐ BEST VALUE│  │              │
│              │  │              │  │              │
│ EV: -$0.67   │  │ EV: -$0.50   │  │ EV: -$1.20   │
│ Rank: #3     │  │ Rank: #1     │  │ Rank: #2     │
└──────────────┘  └──────────────┘  └──────────────┘
```

### **Option 3: Dashboard Banner** (Simplest)

Add a banner at the top of the dashboard:

```
┌─────────────────────────────────────────────────────────────────────────┐
│  🏆 Best Value Right Now: Powerball                                     │
│                                                                           │
│  Powerball: -$0.50 EV (25% loss)  |  Mega Millions: -$1.20 EV (24%)   │
│  Lucky Day Lotto: -$0.67 EV (67% loss)                                  │
│                                                                           │
│  💡 Recommendation: Powerball offers the best value                      │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 🎯 Key Features

### **1. Ranking System**
- Automatically ranks games by Net EV (best to worst)
- Shows "⭐ BEST VALUE" badge on top game
- Displays rank number (#1, #2, #3)

### **2. Visual Indicators**
- Color coding: Green (best), Yellow (medium), Red (worst)
- EV badges show relative performance
- Clear "winner" highlighting

### **3. Smart Recommendations**
- "If you only buy one ticket, buy [Game]"
- "Best value for your budget: [Game]"
- "Closest to positive EV: [Game]"

### **4. Side-by-Side Metrics**
All key metrics visible at once:
- Jackpot amount
- Net EV (dollar amount)
- EV percentage
- Ticket cost
- Odds
- Next draw time
- Recommendation status

---

## 💻 Implementation

### **Backend Changes** (`dashboard.py`)

Add comparison logic to `api_status()`:

```python
def api_status():
    # ... existing code ...
    
    # After calculating all games, add comparison data
    games_list = []
    for game_id, game_data in status_data['games'].items():
        games_list.append({
            'id': game_id,
            'name': game_data['name'],
            'net_ev': game_data['net_ev'],
            'ev_percentage': game_data['ev_percentage'],
            'current_jackpot': game_data['current_jackpot'],
            'ticket_cost': game_data['ticket_cost'],
            'odds': game_data['odds'],
            'is_positive_ev': game_data['is_positive_ev']
        })
    
    # Sort by Net EV (best to worst)
    games_list.sort(key=lambda x: x['net_ev'], reverse=True)
    
    # Add ranking
    for i, game in enumerate(games_list):
        game['rank'] = i + 1
        game['is_best_value'] = (i == 0)
    
    # Find best value game
    best_value = games_list[0] if games_list else None
    
    # Add comparison data to response
    status_data['comparison'] = {
        'best_value_game': best_value['id'] if best_value else None,
        'best_value_name': best_value['name'] if best_value else None,
        'best_value_ev': best_value['net_ev'] if best_value else None,
        'games_ranked': games_list,
        'recommendation': generate_recommendation(games_list)
    }
    
    return jsonify(status_data)

def generate_recommendation(games_list):
    """Generate smart recommendation text"""
    if not games_list:
        return None
    
    best = games_list[0]
    
    # If best game has positive EV
    if best['is_positive_ev']:
        return f"🟢 {best['name']} has POSITIVE EV! This is the best opportunity."
    
    # If best game is close to break-even
    if best['ev_percentage'] >= -10:
        return f"🟡 {best['name']} is closest to break-even (EV: {best['ev_percentage']:.1f}%). Best value right now."
    
    # If best game is significantly better than others
    if len(games_list) > 1:
        second_best = games_list[1]
        ev_diff = best['net_ev'] - second_best['net_ev']
        if ev_diff > 0.20:  # $0.20+ better
            return f"📊 {best['name']} offers the best value (${best['net_ev']:.2f} EV vs ${second_best['net_ev']:.2f} for {second_best['name']})"
    
    # Default recommendation
    return f"💡 If you only buy one ticket, {best['name']} offers the best value (EV: ${best['net_ev']:.2f})"
```

### **Frontend Changes** (`dashboard.html`)

Add comparison section before games grid:

```javascript
function renderComparison(comparisonData) {
    if (!comparisonData || !comparisonData.games_ranked) {
        return '';
    }
    
    const best = comparisonData.games_ranked[0];
    const games = comparisonData.games_ranked;
    
    return `
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    border-radius: 15px; 
                    padding: 25px; 
                    margin-bottom: 30px; 
                    color: white;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.2);">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px;">
                <h2 style="margin: 0; font-size: 1.8em;">🏆 Best Value Right Now</h2>
                <div style="background: rgba(255,255,255,0.2); padding: 8px 16px; border-radius: 20px; font-weight: bold;">
                    ${best.name} ⭐
                </div>
            </div>
            
            <div style="background: rgba(255,255,255,0.1); border-radius: 10px; padding: 20px; margin-bottom: 15px;">
                <div style="font-size: 1.1em; margin-bottom: 10px; font-weight: 600;">
                    💡 ${comparisonData.recommendation || 'Compare games below'}
                </div>
            </div>
            
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">
                ${games.map((game, index) => `
                    <div style="background: rgba(255,255,255,${index === 0 ? '0.25' : '0.1'}); 
                                border-radius: 10px; 
                                padding: 15px;
                                ${index === 0 ? 'border: 2px solid #fbbf24;' : ''}">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                            <div style="font-weight: bold; font-size: 1.1em;">${game.name}</div>
                            ${index === 0 ? '<span style="font-size: 1.5em;">⭐</span>' : `<span style="color: rgba(255,255,255,0.7);">#${game.rank}</span>`}
                        </div>
                        <div style="font-size: 0.9em; opacity: 0.9;">
                            <div>EV: ${formatCurrency(game.net_ev)}</div>
                            <div>${game.ev_percentage >= 0 ? '+' : ''}${formatNumber(game.ev_percentage)}%</div>
                        </div>
                    </div>
                `).join('')}
            </div>
        </div>
    `;
}

// In loadData() function, after rendering games:
if (statusData.comparison) {
    const comparisonHtml = renderComparison(statusData.comparison);
    gamesContainer.insertAdjacentHTML('beforebegin', comparisonHtml);
}
```

---

## 📱 Telegram Bot Integration

Add `/compare` command:

```python
async def compare_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /compare command - show side-by-side comparison"""
    try:
        if not self.assistant:
            self.assistant = LotteryAssistant()
        
        results = await self.assistant.check_jackpots(only_near_draw=False, suppress_messages=True)
        
        # Build comparison
        games_data = []
        for game_id, result in results.items():
            if not result:
                continue
            
            game_config = self.assistant.config.get('lottery_games', {}).get(game_id, {})
            ev_result = result.get('ev_result', {})
            jackpot_data = result.get('jackpot_data', {})
            
            games_data.append({
                'name': game_config.get('name', game_id),
                'net_ev': ev_result.get('net_ev', 0),
                'ev_percentage': ev_result.get('ev_percentage', 0),
                'jackpot': jackpot_data.get('jackpot', 0),
                'ticket_cost': game_config.get('ticket_cost', 0)
            })
        
        # Sort by EV
        games_data.sort(key=lambda x: x['net_ev'], reverse=True)
        
        # Build message
        message = "📊 *Game Comparison*\n\n"
        
        for i, game in enumerate(games_data):
            rank_emoji = "⭐" if i == 0 else f"#{i+1}"
            message += f"{rank_emoji} *{game['name']}*\n"
            message += f"   EV: ${game['net_ev']:.2f} ({game['ev_percentage']:+.1f}%)\n"
            message += f"   Jackpot: ${game['jackpot']:,.0f}\n\n"
        
        # Add recommendation
        if games_data:
            best = games_data[0]
            message += f"💡 *Best Value:* {best['name']}\n"
            message += f"   If you only buy one ticket, buy {best['name']}"
        
        await update.message.reply_text(message, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Error in compare command: {e}")
        await update.message.reply_text(f"❌ Error: {str(e)}")
```

---

## 🎯 User Value

### **Before Comparison**:
- User sees 3 separate cards
- Has to mentally compare EV values
- Might miss that Powerball is better than Mega Millions
- No clear recommendation

### **After Comparison**:
- User instantly sees "Powerball is #1"
- Clear recommendation: "Buy Powerball"
- Side-by-side metrics make comparison easy
- Saves time and mental effort

---

## 📊 Example Scenarios

### **Scenario 1: All Negative EV**
```
Powerball:    -$0.50 EV (25% loss)  ⭐ BEST
Mega Millions: -$1.20 EV (24% loss)  #2
Lucky Day:    -$0.67 EV (67% loss)   #3

Recommendation: "Powerball offers the best value (-$0.50 EV)"
```

### **Scenario 2: One Positive EV**
```
Powerball:    +$2.45 EV (122% profit) ⭐ BEST - BUY THIS!
Mega Millions: -$1.20 EV (24% loss)   #2
Lucky Day:    -$0.67 EV (67% loss)    #3

Recommendation: "🟢 Powerball has POSITIVE EV! This is the best opportunity."
```

### **Scenario 3: Close Values**
```
Powerball:    -$0.50 EV (25% loss)  ⭐ BEST
Mega Millions: -$0.55 EV (27% loss)  #2
Lucky Day:    -$0.67 EV (67% loss)   #3

Recommendation: "Powerball and Mega Millions are very close. Powerball slightly better."
```

---

## ✅ Benefits

1. **Instant Clarity**: See best value at a glance
2. **Time Saving**: No need to compare manually
3. **Better Decisions**: Clear recommendation
4. **Budget Optimization**: Know which game to prioritize
5. **Educational**: Learn which games typically offer better value

---

## 🚀 Quick Implementation (Simplest Version)

Just add a banner at the top of the dashboard:

```javascript
// In loadData(), after getting statusData:
const games = Object.values(statusData.games);
if (games.length > 1) {
    // Sort by EV
    games.sort((a, b) => b.net_ev - a.net_ev);
    const best = games[0];
    
    // Add simple banner
    const banner = `
        <div style="background: #667eea; color: white; padding: 20px; 
                    border-radius: 10px; margin-bottom: 20px; text-align: center;">
            <div style="font-size: 1.3em; font-weight: bold; margin-bottom: 8px;">
                🏆 Best Value: ${best.name}
            </div>
            <div style="font-size: 0.95em; opacity: 0.9;">
                EV: ${formatCurrency(best.net_ev)} (${best.ev_percentage >= 0 ? '+' : ''}${formatNumber(best.ev_percentage)}%)
            </div>
        </div>
    `;
    gamesContainer.insertAdjacentHTML('beforebegin', banner);
}
```

**This takes 5 minutes to implement and adds immediate value!**

---

**Last Updated**: 2026-01-27
**Status**: Design Document - Ready for Implementation
