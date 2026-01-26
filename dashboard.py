"""
Dashboard Web UI for Lottery Assistant
Provides visual display of jackpots, EV, thresholds, and alerts
"""

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, jsonify, make_response
from dotenv import load_dotenv

from src.lottery_assistant import LotteryAssistant
from src.threshold_alert import ThresholdAlert
from src.buy_signal import BuySignal
from datetime import datetime, time, timedelta

load_dotenv()

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0


def load_state():
    """Load state from JSON file"""
    state_file = os.getenv('LOTTERY_STATE_FILE', 'lottery_state.json')
    if os.path.exists(state_file):
        try:
            with open(state_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading state: {e}")
            return {}
    return {}


def load_config():
    """Load configuration"""
    config_path = os.getenv('CONFIG_FILE', 'config.json')
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
            return {}
    return {}


def get_next_draw_time(game_id: str, config: dict) -> datetime:
    """Calculate next draw time for a game"""
    game_config = config.get('lottery_games', {}).get(game_id, {})
    draw_time_str = game_config.get('draw_time', '12:00')
    
    try:
        parts = draw_time_str.split(':')
        draw_hour = int(parts[0])
        draw_minute = int(parts[1])
        draw_time = time(draw_hour, draw_minute)
    except (ValueError, IndexError):
        return None
    
    # Draw days mapping
    draw_days = {
        'powerball': [0, 2, 5],  # Monday, Wednesday, Saturday
        'mega_millions': [1, 4],  # Tuesday, Friday
        'lucky_day_lotto_midday': list(range(7)),  # Daily
        'lucky_day_lotto_evening': list(range(7))  # Daily
    }
    
    now = datetime.now()
    draw_datetime = datetime.combine(now.date(), draw_time)
    game_draw_days = draw_days.get(game_id, list(range(7)))
    
    # If draw time has passed today, move to next draw
    if draw_datetime <= now:
        if len(game_draw_days) == 7:  # Daily
            draw_datetime += timedelta(days=1)
        else:
            # Find next draw day
            current_weekday = now.weekday()  # 0=Monday, 6=Sunday
            days_ahead = 1
            while days_ahead <= 7:
                next_date = now.date() + timedelta(days=days_ahead)
                next_weekday = next_date.weekday()
                if next_weekday in game_draw_days:
                    draw_datetime = datetime.combine(next_date, draw_time)
                    break
                days_ahead += 1
            if days_ahead > 7:
                draw_datetime += timedelta(days=1)
    
    return draw_datetime


def format_time_to_draw(game_id: str, config: dict) -> str:
    """Format time until next draw as 'Xh Ym' or 'Xm'"""
    next_draw = get_next_draw_time(game_id, config)
    if not next_draw:
        return "Unknown"
    
    now = datetime.now()
    time_diff = next_draw - now
    
    if time_diff.total_seconds() < 0:
        return "Draw passed"
    
    total_minutes = int(time_diff.total_seconds() / 60)
    
    if total_minutes < 1:
        return "Less than 1m"
    
    hours = total_minutes // 60
    minutes = total_minutes % 60
    
    if hours > 0:
        if minutes > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{hours}h"
    else:
        return f"{minutes}m"


def get_rollover_count(game_id: str, state: dict) -> int:
    """Get rollover count for a game"""
    game_state = state.get('games', {}).get(game_id, {})
    rollover_count = game_state.get('rollover_count', 0)
    
    # If rollover count is 0 but jackpot is above starting amount, calculate it
    if rollover_count == 0:
        config = load_config()
        game_config = config.get('lottery_games', {}).get(game_id, {})
        starting_jackpot = game_config.get('starting_jackpot', 0)
        rollover_increment = game_config.get('rollover_increment', 0)
        current_jackpot = game_state.get('last_jackpot', 0)
        
        if starting_jackpot > 0 and rollover_increment > 0 and current_jackpot >= starting_jackpot:
            jackpot_increase = current_jackpot - starting_jackpot
            rollover_count = int(jackpot_increase / rollover_increment)
    
    return rollover_count


def get_ev_tier(ev_percentage: float) -> dict:
    """Get EV tier label and color based on EV percentage"""
    if ev_percentage >= 50:
        return {'label': '+EV Crazy Anomaly', 'color': '#10b981', 'class': 'ev-anomaly'}
    elif ev_percentage >= 10:
        return {'label': '+EV but Small', 'color': '#34d399', 'class': 'ev-positive-small'}
    elif ev_percentage >= 0:
        return {'label': 'Neutral-ish', 'color': '#fbbf24', 'class': 'ev-neutral'}
    elif ev_percentage >= -20:
        return {'label': 'Bad EV', 'color': '#f59e0b', 'class': 'ev-bad'}
    else:
        return {'label': 'Terrible EV', 'color': '#ef4444', 'class': 'ev-terrible'}


@app.route('/')
def index():
    """Main dashboard page"""
    template_path = Path('templates/dashboard.html')
    response = make_response(render_template('dashboard.html'))
    # Disable caching
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    # Add last-modified header for live reload
    if template_path.exists():
        import time
        mtime = template_path.stat().st_mtime
        response.headers['Last-Modified'] = time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime(mtime))
    return response


@app.route('/api/status')
def api_status():
    """Get current status of all games (from state, fast)"""
    try:
        config = load_config()
        state = load_state()
        
        status_data = {
            'timestamp': datetime.now().isoformat(),
            'version': '1.0.0',  # Version for cache busting
            'games': {}
        }
        
        # Get enabled games from config
        enabled_games = [
            game_id for game_id, game_config in config.get('lottery_games', {}).items()
            if game_config.get('enabled', False)
        ]
        
        if not enabled_games:
            return jsonify({
                'timestamp': datetime.now().isoformat(),
                'games': {},
                'message': 'No games enabled in config.json'
            })
        
        # Calculate EV for each game based on last known jackpot
        from src.ev_calculator import EVCalculator
        ev_calculator = EVCalculator(config)
        buy_signal = BuySignal(config)
        
        for game_id in enabled_games:
            game_config = config.get('lottery_games', {}).get(game_id, {})
            game_state = state.get('games', {}).get(game_id, {})
            
            current_jackpot = game_state.get('last_jackpot', 0)
            
            # Calculate EV
            odds = game_config.get('odds', 1)
            ticket_cost = game_config.get('ticket_cost', 1.0)
            secondary_ev = game_config.get('secondary_prize_ev', 0)
            
            ev_result = ev_calculator.calculate_ev(
                current_jackpot,
                odds,
                ticket_cost,
                secondary_ev
            ) if current_jackpot > 0 else {
                'net_ev': 0,
                'is_positive_ev': False,
                'is_recommended': False,
                'ev_percentage': 0,
                'break_even_jackpot': 0
            }
            
            # Get EV tier
            ev_tier = get_ev_tier(ev_result.get('ev_percentage', 0))
            
            # Calculate buy signal
            rollover_count = get_rollover_count(game_id, state)
            next_draw = get_next_draw_time(game_id, config)
            time_to_draw_minutes = None
            if next_draw:
                time_diff = next_draw - datetime.now()
                time_to_draw_minutes = int(time_diff.total_seconds() / 60) if time_diff.total_seconds() > 0 else None
            
            buy_signal_result = buy_signal.calculate_buy_signal(
                game_id=game_id,
                current_jackpot=current_jackpot,
                ev_result=ev_result,
                rollover_count=rollover_count,
                time_to_draw_minutes=time_to_draw_minutes,
                game_config=game_config
            )
            
            status_data['games'][game_id] = {
                'name': game_config.get('name', game_id),
                'current_jackpot': current_jackpot,
                'last_jackpot': current_jackpot,  # Same as current for now
                'change': 0,  # No change data without history
                'change_percent': 0,
                'net_ev': ev_result.get('net_ev', 0),
                'is_positive_ev': ev_result.get('is_positive_ev', False),
                'is_recommended': ev_result.get('is_recommended', False),
                'ev_percentage': ev_result.get('ev_percentage', 0),
                'ev_tier': ev_tier['label'],
                'ev_tier_class': ev_tier['class'],
                'ev_tier_color': ev_tier['color'],
                'break_even_jackpot': ev_result.get('break_even_jackpot', 0),
                'last_threshold': game_state.get('last_threshold', 0),
                'min_threshold': game_config.get('min_threshold'),
                'thresholds_hit_count': len(game_state.get('thresholds_hit', [])),
                'last_alert_time': game_state.get('last_alert_time'),
                'draw_time': game_config.get('draw_time', ''),
                'time_to_draw': format_time_to_draw(game_id, config),
                'next_draw_time': get_next_draw_time(game_id, config).isoformat() if get_next_draw_time(game_id, config) else None,
                'rollover_count': get_rollover_count(game_id, state),
                'ticket_cost': game_config.get('ticket_cost', 0),
                'odds': game_config.get('odds', 0),
                'buy_signal': buy_signal_result.get('has_signal', False),
                'buy_signal_type': buy_signal_result.get('signal_type'),
                'buy_signal_confidence': buy_signal_result.get('confidence'),
                'buy_signal_message': buy_signal_result.get('message'),
                'buy_signal_reasons': buy_signal_result.get('reasons', [])
            }
        
        return jsonify(status_data)
    
    except Exception as e:
        import traceback
        print(f"Error in api_status: {e}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@app.route('/api/refresh')
def api_refresh():
    """Force a fresh check and update state"""
    try:
        # Run async check
        assistant = LotteryAssistant()
        try:
            results = asyncio.run(assistant.check_jackpots())
        finally:
            asyncio.run(assistant.cleanup())
        
        # Return updated status with cache-busting
        response = api_status()
        if isinstance(response, tuple):
            response[0].headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        else:
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        return response
    
    except Exception as e:
        import traceback
        print(f"Error in api_refresh: {e}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@app.route('/api/history')
def api_history():
    """Get threshold alert history"""
    try:
        state = load_state()
        history = []
        
        for game_id, game_state in state.get('games', {}).items():
            config = load_config()
            game_config = config.get('lottery_games', {}).get(game_id, {})
            game_name = game_config.get('name', game_id)
            
            for threshold_hit in game_state.get('thresholds_hit', []):
                history.append({
                    'game_id': game_id,
                    'game_name': game_name,
                    'threshold': threshold_hit.get('threshold', 0),
                    'jackpot': threshold_hit.get('jackpot', 0),
                    'timestamp': threshold_hit.get('timestamp', '')
                })
        
        # Sort by timestamp (newest first)
        history.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        return jsonify({'history': history[:50]})  # Last 50 alerts
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/config')
def api_config():
    """Get configuration"""
    try:
        config = load_config()
        return jsonify(config)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    templates_dir = Path('templates')
    templates_dir.mkdir(exist_ok=True)
    
    port = int(os.getenv('DASHBOARD_PORT', 5000))
    debug = os.getenv('DASHBOARD_DEBUG', 'true').lower() == 'true'  # Default to True for auto-reload
    
    print(f"🎰 Starting Lottery Assistant Dashboard on http://localhost:{port}")
    print(f"📝 Debug mode: {debug} (templates will auto-reload)")
    app.run(host='0.0.0.0', port=port, debug=debug, use_reloader=True)
