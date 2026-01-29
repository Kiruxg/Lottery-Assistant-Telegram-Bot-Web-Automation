"""
Dashboard Web UI for Lottery Assistant
Provides visual display of jackpots, EV, thresholds, and alerts
"""

import asyncio
import json
import os
import logging
import threading
import time as time_module
from datetime import datetime, time, timedelta
from pathlib import Path
from flask import Flask, render_template, jsonify, make_response, request
from dotenv import load_dotenv

from src.lottery_assistant import LotteryAssistant
from src.threshold_alert import ThresholdAlert
from src.buy_signal import BuySignal
from src.ev_calculator import EVCalculator
from src.subscription_manager import SubscriptionManager
from src.telegram_notifier import TelegramNotifier
from src.entitlements import (
    get_plan_limits, 
    get_history_start_date,
    format_history_window,
    can_access_feature
)
from src.buy_signal_logger import BuySignalLogger

load_dotenv()

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

# Global refresh state tracking
refresh_state = {
    'in_progress': False,
    'start_time': None,
    'last_update': None
}
refresh_lock = threading.Lock()


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
    
    # Handle multiple draw times (e.g., "12:40,21:22")
    draw_times = []
    for time_str in draw_time_str.split(','):
        time_str = time_str.strip()
        try:
            parts = time_str.split(':')
            draw_hour = int(parts[0])
            draw_minute = int(parts[1])
            draw_times.append(time(draw_hour, draw_minute))
        except (ValueError, IndexError):
            continue
    
    if not draw_times:
        return None
    
    # For games with multiple draws per day, find the next one
    # For single draw games, use the first (and only) time
    draw_time = draw_times[0] if len(draw_times) == 1 else None
    
    # Draw days mapping
    draw_days = {
        'powerball': [0, 2, 5],  # Monday, Wednesday, Saturday
        'mega_millions': [1, 4],  # Tuesday, Friday
        'lucky_day_lotto_midday': list(range(7)),  # Daily
        'lucky_day_lotto_evening': list(range(7)),  # Daily
        'lotto': [0, 3],  # Monday, Thursday
        'pick_3': list(range(7)),  # Daily (twice per day)
        'pick_4': list(range(7)),  # Daily (twice per day)
        'hot_wins': list(range(7))  # Daily (every 4 minutes)
    }
    
    now = datetime.now()
    game_draw_days = draw_days.get(game_id, list(range(7)))
    
    # For games with multiple draws per day, find the next draw time today or tomorrow
    if len(draw_times) > 1:
        # Check today's remaining draws first
        for draw_time in sorted(draw_times):
            draw_datetime = datetime.combine(now.date(), draw_time)
            if draw_datetime > now:
                return draw_datetime
        
        # If no draws left today, use first draw tomorrow
        if len(game_draw_days) == 7:  # Daily
            next_date = now.date() + timedelta(days=1)
            return datetime.combine(next_date, sorted(draw_times)[0])
        else:
            # Find next draw day
            current_weekday = now.weekday()
            days_ahead = 1
            while days_ahead <= 7:
                next_date = now.date() + timedelta(days=days_ahead)
                next_weekday = next_date.weekday()
                if next_weekday in game_draw_days:
                    return datetime.combine(next_date, sorted(draw_times)[0])
                days_ahead += 1
            return datetime.combine(now.date() + timedelta(days=1), sorted(draw_times)[0])
    
    # Single draw time games
    draw_time = draw_times[0]
    draw_datetime = datetime.combine(now.date(), draw_time)
    
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
    """Homepage"""
    return render_template('index.html')


@app.route('/dashboard')
def dashboard():
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
        # Get user ID and subscription info
        user_id = request.headers.get('X-User-ID') or request.args.get('user_id') or 'web_anonymous'
        subscription_manager = SubscriptionManager()
        user_tier = subscription_manager.get_user_tier(user_id)
        # Treat web dashboard user as configurable tier (admin by default for dev/testing)
        if user_id == 'web_anonymous':
            import os
            user_tier = os.getenv('WEB_USER_TIER', 'admin')
        
        # Initialize buy signal logger
        buy_signal_logger = BuySignalLogger()
        
        # Get plan limits
        plan_limits = get_plan_limits(user_tier)
        
        config = load_config()
        state = load_state()
        
        status_data = {
            'timestamp': datetime.now().isoformat(),
            'version': '1.0.0',  # Version for cache busting
            'games': {},
            'entitlements': {
                'tier': user_tier,
                'buy_signals_limit': None,  # Unlimited for all plans
                'buy_signals_remaining': None,  # Unlimited for all plans
                'history_window': format_history_window(user_tier),
                'can_export': plan_limits.get('can_export', False),
                'can_purchase_automate': plan_limits.get('can_purchase_automate', False),
                'can_compare_games': plan_limits.get('can_compare_games', False),
                'can_edit_thresholds': plan_limits.get('can_edit_thresholds', False),
            }
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
            
            # Debug logging for pick_4 and hot_wins
            if game_id in ['pick_4', 'hot_wins']:
                print(f"[DASHBOARD {game_id.upper()}] Loading from state:")
                print(f"  - game_state exists: {bool(game_state)}")
                print(f"  - game_state keys: {list(game_state.keys()) if game_state else 'N/A'}")
                print(f"  - last_jackpot from state: {current_jackpot}")
                print(f"  - Full game_state: {game_state}")
            
            # Calculate EV (always calculate, even with 0 jackpot, to show secondary prize EV)
            odds = game_config.get('odds', 1)
            ticket_cost = game_config.get('ticket_cost', 1.0)
            secondary_ev = game_config.get('secondary_prize_ev', 0)
            
            # Always calculate EV - even with 0 jackpot, secondary prizes contribute
            ev_result = ev_calculator.calculate_ev(
                current_jackpot,
                odds,
                ticket_cost,
                secondary_ev
            )
            
            # Get EV tier
            ev_tier = get_ev_tier(ev_result.get('ev_percentage', 0))
            
            # Calculate buy signal
            rollover_count = get_rollover_count(game_id, state)
            next_draw = get_next_draw_time(game_id, config)
            time_to_draw_minutes = None
            if next_draw:
                time_diff = next_draw - datetime.now()
                time_to_draw_minutes = int(time_diff.total_seconds() / 60) if time_diff.total_seconds() > 0 else None
            
            # Get previous jackpot for growth velocity calculation
            previous_jackpot = game_state.get('previous_jackpot', game_state.get('last_jackpot', current_jackpot))
            
            buy_signal_result = buy_signal.calculate_buy_signal(
                game_id=game_id,
                current_jackpot=current_jackpot,
                ev_result=ev_result,
                rollover_count=rollover_count,
                time_to_draw_minutes=time_to_draw_minutes,
                game_config=game_config,
                previous_jackpot=previous_jackpot
            )
            
            # Check buy signal entitlement
            has_buy_signal = buy_signal_result.get('has_signal', False)
            can_show_signal = True
            signal_blocked_reason = None
            
            if has_buy_signal:
                # Buy signals are unlimited - users get them as long as they're subscribed
                # Still log for analytics purposes
                signal_type = buy_signal_result.get('signal_type', 'basic')
                buy_signal_logger.log_buy_signal(
                    user_id=user_id,
                    game_id=game_id,
                    signal_type=signal_type,
                    draw_id=None  # Could add draw ID if available
                )
                # No limits, so always show
                can_show_signal = True
            
            # Calculate threshold progress for display (simplified - single threshold only)
            last_threshold = game_state.get('last_threshold', 0)
            min_threshold = game_config.get('min_threshold')
            threshold_progress = None
            
            if min_threshold:
                # Simple progress calculation: show progress toward minimum threshold
                if current_jackpot >= min_threshold:
                    # Threshold reached - show 100% progress
                    threshold_progress = 100
                else:
                    # Below minimum threshold - show progress to minimum
                    threshold_progress = min(100, max(0, (current_jackpot / min_threshold) * 100)) if min_threshold > 0 else 0
            
            # Calculate change from previous jackpot
            # Track previous_jackpot separately to show change between checks
            # If previous_jackpot doesn't exist, use last_jackpot as fallback
            previous_jackpot = game_state.get('previous_jackpot', game_state.get('last_jackpot', current_jackpot))
            last_jackpot = game_state.get('last_jackpot', current_jackpot)
            
            # Calculate change: current vs previous (not current vs current)
            # Only show change if we have valid previous data and it's different
            if previous_jackpot > 0 and previous_jackpot != current_jackpot:
                jackpot_change = current_jackpot - previous_jackpot
                change_percent = ((jackpot_change / previous_jackpot) * 100) if previous_jackpot > 0 else 0
            else:
                # No previous data or same value - no change to show
                jackpot_change = 0
                change_percent = 0
            
            status_data['games'][game_id] = {
                'name': game_config.get('name', game_id),
                'current_jackpot': current_jackpot,
                'last_jackpot': last_jackpot,
                'change': jackpot_change,
                'change_percent': change_percent,
                'net_ev': ev_result.get('net_ev', 0),
                'is_positive_ev': ev_result.get('is_positive_ev', False),
                'is_recommended': ev_result.get('is_recommended', False),
                'break_even_jackpot': ev_result.get('break_even_jackpot', 0),
                'ev_percentage': ev_result.get('ev_percentage', 0),
                'ev_tier': ev_tier['label'],
                'ev_tier_class': ev_tier['class'],
                'ev_tier_color': ev_tier['color'],
                'break_even_jackpot': ev_result.get('break_even_jackpot', 0),
                'last_threshold': last_threshold,
                'threshold_progress': threshold_progress,
                'min_threshold': min_threshold,
                'thresholds_hit_count': len(game_state.get('thresholds_hit', [])),
                'last_alert_time': game_state.get('last_alert_time'),
                'draw_time': game_config.get('draw_time', ''),
                'time_to_draw': format_time_to_draw(game_id, config),
                'next_draw_time': (lambda dt: dt.isoformat() if dt else None)(get_next_draw_time(game_id, config)),
                'rollover_count': get_rollover_count(game_id, state),
                'ticket_cost': game_config.get('ticket_cost', 0),
                'odds': game_config.get('odds', 0),
                'buy_signal': has_buy_signal,  # Always show if signal exists (unlimited)
                'buy_signal_blocked': False,  # No limits, so never blocked
                'buy_signal_blocked_reason': None,
                'buy_signal_type': buy_signal_result.get('signal_type') if can_show_signal else None,
                'buy_signal_confidence': buy_signal_result.get('confidence') if can_show_signal else None,
                'buy_signal_message': buy_signal_result.get('message') if can_show_signal else None,
                'buy_signal_reasons': buy_signal_result.get('reasons', []) if can_show_signal else []
            }
        
        return jsonify(status_data)
    
    except Exception as e:
        import traceback
        print(f"Error in api_status: {e}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


def _run_refresh_background():
    """Run refresh in background thread with timeout"""
    global refresh_state
    
    with refresh_lock:
        if refresh_state['in_progress']:
            return  # Already refreshing
        refresh_state['in_progress'] = True
        refresh_state['start_time'] = time_module.time()
    
    try:
        # Run async check with timeout
        assistant = LotteryAssistant()
        loop = None
        try:
            # Create new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Run check_jackpots with timeout (10 seconds max)
            try:
                results = loop.run_until_complete(
                    asyncio.wait_for(
                        assistant.check_jackpots(),
                        timeout=10.0  # 10 second timeout
                    )
                )
            except asyncio.TimeoutError:
                print("Refresh timed out after 10 seconds")
                results = {}
            except Exception as e:
                print(f"Error during check_jackpots: {e}")
                results = {}
            
            # Cleanup with same loop
            try:
                loop.run_until_complete(assistant.cleanup())
            except Exception as e:
                print(f"Error during cleanup: {e}")
        finally:
            if loop:
                try:
                    # Cancel any remaining tasks
                    pending = asyncio.all_tasks(loop)
                    for task in pending:
                        task.cancel()
                    # Run until all tasks are cancelled
                    if pending:
                        loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                except Exception:
                    pass
                finally:
                    loop.close()
        
        with refresh_lock:
            refresh_state['last_update'] = time_module.time()
    except Exception as e:
        import traceback
        print(f"Error in background refresh: {e}")
        print(traceback.format_exc())
    finally:
        with refresh_lock:
            refresh_state['in_progress'] = False


@app.route('/api/refresh')
def api_refresh():
    """Force a fresh check and update state (non-blocking)"""
    global refresh_state
    
    # Check if refresh is already in progress
    with refresh_lock:
        if refresh_state['in_progress']:
            # Check if it's been running too long (stuck)
            elapsed = time_module.time() - refresh_state['start_time'] if refresh_state['start_time'] else 0
            if elapsed > 15:  # If stuck for more than 15 seconds, allow restart
                refresh_state['in_progress'] = False
            else:
                # Return immediately - refresh already in progress
                return jsonify({
                    'status': 'in_progress',
                    'message': 'Refresh already in progress'
                }), 202
    
    # Start refresh in background thread
    thread = threading.Thread(target=_run_refresh_background, daemon=True)
    thread.start()
    
    # Return immediately with accepted status
    return jsonify({
        'status': 'started',
        'message': 'Refresh started in background'
    }), 202


@app.route('/api/history')
def api_history():
    """Get threshold alert history (filtered by plan limits)"""
    try:
        # Get user ID and subscription info
        user_id = request.headers.get('X-User-ID') or request.args.get('user_id') or 'web_anonymous'
        subscription_manager = SubscriptionManager()
        user_tier = subscription_manager.get_user_tier(user_id)
        if user_id == 'web_anonymous':
            import os
            user_tier = os.getenv('WEB_USER_TIER', 'admin')
        
        # Get history start date based on plan
        history_start_date = get_history_start_date(user_tier)
        
        state = load_state()
        history = []
        
        for game_id, game_state in state.get('games', {}).items():
            config = load_config()
            game_config = config.get('lottery_games', {}).get(game_id, {})
            game_name = game_config.get('name', game_id)
            
            for threshold_hit in game_state.get('thresholds_hit', []):
                # Filter by date if plan has limit
                timestamp_str = threshold_hit.get('timestamp', '')
                if history_start_date and timestamp_str:
                    try:
                        # Parse timestamp (assuming ISO format)
                        hit_date = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                        if hit_date < history_start_date:
                            continue  # Skip entries before allowed date
                    except (ValueError, AttributeError):
                        # If parsing fails, include it (better to show than hide)
                        pass
                
                history.append({
                    'game_id': game_id,
                    'game_name': game_name,
                    'threshold': threshold_hit.get('threshold', 0),
                    'jackpot': threshold_hit.get('jackpot', 0),
                    'timestamp': timestamp_str
                })
        
        # Sort by timestamp (newest first)
        history.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        # Return history with metadata
        plan_limits = get_plan_limits(user_tier)
        return jsonify({
            'history': history[:50],  # Last 50 alerts
            'history_window': format_history_window(user_tier),
            'history_days': plan_limits.get('history_days')
        })
    
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


@app.route('/pricing')
def pricing():
    """Pricing page"""
    return render_template('pricing.html')


@app.route('/api/export')
def api_export():
    """Export data as CSV/JSON (Pro-only)"""
    try:
        # Get user ID and subscription info
        user_id = request.headers.get('X-User-ID') or request.args.get('user_id') or 'web_anonymous'
        subscription_manager = SubscriptionManager()
        user_tier = subscription_manager.get_user_tier(user_id)
        if user_id == 'web_anonymous':
            import os
            user_tier = os.getenv('WEB_USER_TIER', 'admin')
        
        # Check entitlements - export is Pro-only
        if not can_access_feature(user_tier, 'can_export'):
            return jsonify({
                'error': 'Data export is a Pro feature. Please upgrade to export data.',
                'requires_tier': 'pro'
            }), 403
        
        # Get export format and game filter
        export_format = request.args.get('format', 'json').lower()
        game_id = request.args.get('game_id')
        
        if export_format not in ['json', 'csv']:
            return jsonify({'error': 'Invalid format. Use "json" or "csv".'}), 400
        
        # Get history data (unlimited for Pro)
        state = load_state()
        history = []
        
        for gid, game_state in state.get('games', {}).items():
            if game_id and gid != game_id:
                continue
            
            config = load_config()
            game_config = config.get('lottery_games', {}).get(gid, {})
            game_name = game_config.get('name', gid)
            
            for threshold_hit in game_state.get('thresholds_hit', []):
                history.append({
                    'game_id': gid,
                    'game_name': game_name,
                    'threshold': threshold_hit.get('threshold', 0),
                    'jackpot': threshold_hit.get('jackpot', 0),
                    'timestamp': threshold_hit.get('timestamp', '')
                })
        
        # Sort by timestamp
        history.sort(key=lambda x: x.get('timestamp', ''), reverse=False)  # Oldest first for export
        
        if export_format == 'json':
            response = make_response(jsonify({'history': history}))
            response.headers['Content-Type'] = 'application/json'
            response.headers['Content-Disposition'] = f'attachment; filename="lottery-history-{game_id or "all"}.json"'
            return response
        
        # CSV format
        import csv
        import io
        
        output = io.StringIO()
        if history:
            writer = csv.DictWriter(output, fieldnames=['game_id', 'game_name', 'threshold', 'jackpot', 'timestamp'])
            writer.writeheader()
            writer.writerows(history)
        
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename="lottery-history-{game_id or "all"}.csv"'
        return response
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/thresholds/<game_id>', methods=['POST'])
def update_threshold(game_id):
    """Update threshold settings for a game"""
    try:
        # Check entitlements - custom thresholds are Premium/Pro only (Admin always allowed)
        user_id = request.headers.get('X-User-ID') or request.args.get('user_id') or 'web_anonymous'
        subscription_manager = SubscriptionManager()
        user_tier = subscription_manager.get_user_tier(user_id)
        if user_id == 'web_anonymous':
            import os
            user_tier = os.getenv('WEB_USER_TIER', 'admin')
        
        if not can_access_feature(user_tier, 'can_edit_thresholds'):
            return jsonify({
                'error': 'Custom thresholds are a Premium feature. Please upgrade to edit thresholds.',
                'requires_tier': 'premium'
            }), 403
        
        import json
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        min_threshold = data.get('min_threshold')
        
        if min_threshold is None:
            return jsonify({'error': 'min_threshold is required'}), 400
        
        config = load_config()
        if game_id not in config.get('lottery_games', {}):
            return jsonify({'error': f'Game not found: {game_id}'}), 404
        
        # Validate thresholds based on game type
        is_ldl = 'lucky_day_lotto' in game_id
        min_limit = 100000 if is_ldl else 50000000
        max_limit = 1000000 if is_ldl else 1000000000
        
        min_value = float(min_threshold)
        
        if min_value < min_limit or min_value > max_limit:
            return jsonify({
                'error': f'Threshold must be between ${min_limit:,.0f} and ${max_limit:,.0f}'
            }), 400
        
        config['lottery_games'][game_id]['min_threshold'] = min_value
        
        # Save config
        config_path = os.getenv('CONFIG_FILE', 'config.json')
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"Updated threshold for {game_id}: min={min_value}")
        return jsonify({
            'success': True, 
            'min_threshold': min_value
        })
    
    except ValueError as e:
        return jsonify({'error': f'Invalid number format: {str(e)}'}), 400
    except Exception as e:
        import traceback
        print(f"Error updating threshold: {e}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@app.route('/api/subscriptions', methods=['GET'])
def api_get_subscriptions():
    """Get user's subscriptions"""
    try:
        user_id = request.headers.get('X-User-ID') or request.args.get('user_id')
        if not user_id:
            user_id = 'web_anonymous'
        
        subscription_manager = SubscriptionManager()
        subscriptions = subscription_manager.get_user_subscriptions(user_id)
        info = subscription_manager.get_subscription_info(user_id)
        
        return jsonify({
            'subscriptions': subscriptions,
            'tier': info['tier'],
            'subscription_count': info['subscription_count'],
            'max_subscriptions': info['max_subscriptions']
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


async def send_subscription_confirmation(chat_id: str, game_id: str):
    """
    Send Telegram confirmation message with game's latest info when subscribing via web
    
    Args:
        chat_id: Telegram chat ID
        game_id: Game ID user subscribed to
    """
    try:
        # Get latest game info
        assistant = LotteryAssistant()
        results = await assistant.check_jackpots(game_id_filter=game_id, only_near_draw=False, suppress_messages=True)
        await assistant.cleanup()
        
        result = results.get(game_id)
        
        # Extract game info from result or fallback to state
        if result:
            game_config = assistant.config.get('lottery_games', {}).get(game_id, {})
            game_name = game_config.get('name', game_id)
            jackpot_data = result.get('jackpot_data', {})
            current_jackpot = jackpot_data.get('jackpot', 0)
            ev_result = result.get('ev_result', {})
            buy_signal_result = result.get('buy_signal_details', {})
        else:
            # Fallback: use state data if live check fails
            config = load_config()
            state = load_state()
            game_config = config.get('lottery_games', {}).get(game_id, {})
            game_state = state.get('games', {}).get(game_id, {})
            game_name = game_config.get('name', game_id)
            current_jackpot = game_state.get('last_jackpot', 0)
            
            # Calculate EV from state
            ev_calculator = EVCalculator(config)
            buy_signal = BuySignal(config)
            
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
                'ev_percentage': 0
            }
            
            rollover_count = game_state.get('rollover_count', 0)
            next_draw = get_next_draw_time(game_id, config)
            time_to_draw_minutes = None
            if next_draw:
                time_diff = next_draw - datetime.now()
                time_to_draw_minutes = int(time_diff.total_seconds() / 60) if time_diff.total_seconds() > 0 else None
            
            # Get previous jackpot for growth velocity calculation
            previous_jackpot = game_state.get('previous_jackpot', game_state.get('last_jackpot', current_jackpot))
            
            buy_signal_result = buy_signal.calculate_buy_signal(
                game_id=game_id,
                current_jackpot=current_jackpot,
                ev_result=ev_result,
                rollover_count=rollover_count,
                time_to_draw_minutes=time_to_draw_minutes,
                game_config=game_config,
                previous_jackpot=previous_jackpot
            )
        
        # Get subscription info for tier
        subscription_manager = SubscriptionManager()
        info = subscription_manager.get_subscription_info(chat_id)
        
        # Build confirmation message
        game_display_name = game_id.replace('_', ' ').title()
        message = f"✅ Subscribed to {game_display_name}!\n\n"
        message += f"📋 *Subscription Status:*\n"
        message += f"• Tier: {info['tier'].title()}\n"
        message += f"• Subscribed to: {info['subscription_count']}/{info['max_subscriptions']} games\n\n"
        message += f"🎰 *{game_name}*\n\n"
        message += f"💰 Current Jackpot: ${current_jackpot:,.2f}\n"
        
        net_ev = ev_result.get('net_ev', 0)
        ev_percentage = ev_result.get('ev_percentage', 0)
        
        # Add buy signal info
        if buy_signal_result.get('has_signal'):
            message += f"{buy_signal_result.get('message', 'BUY SIGNAL')}\n"
        elif ev_result.get('is_positive_ev', False):
            message += f"✅ *BUY SIGNAL* - Positive EV: ${net_ev:.2f} ({ev_percentage:.2f}%)\n"
        else:
            message += f"❌ *NO BUY SIGNAL* - Net EV: ${net_ev:.2f} ({ev_percentage:.2f}%)\n"
        
        config = load_config()
        next_draw = get_next_draw_time(game_id, config)
        if next_draw:
            message += f"⏰ Time: {next_draw.strftime('%Y-%m-%d %H:%M:%S')}\n"
        else:
            message += f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        
        # Send via Telegram
        notifier = TelegramNotifier(chat_id=chat_id)
        await notifier.send_message(message, parse_mode="Markdown")
        
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to send subscription confirmation to {chat_id}: {e}")


def is_telegram_chat_id(user_id: str) -> bool:
    """
    Check if user_id looks like a Telegram chat ID (numeric string)
    
    Args:
        user_id: User ID to check
        
    Returns:
        True if looks like Telegram chat ID
    """
    if not user_id or user_id == 'web_anonymous':
        return False
    # Telegram chat IDs are numeric strings (can be negative for groups)
    try:
        int(user_id)
        return True
    except ValueError:
        return False


@app.route('/api/subscriptions/subscribe', methods=['POST'])
def api_subscribe():
    """Subscribe user to a game"""
    try:
        data = request.get_json()
        game_id = data.get('game_id')
        user_id = request.headers.get('X-User-ID') or data.get('user_id')
        
        if not user_id:
            user_id = 'web_anonymous'
        
        if not game_id:
            return jsonify({'error': 'game_id is required'}), 400
        
        subscription_manager = SubscriptionManager()
        success, message = subscription_manager.subscribe_to_game(user_id, game_id)
        
        if success:
            subscriptions = subscription_manager.get_user_subscriptions(user_id)
            info = subscription_manager.get_subscription_info(user_id)
            
            # Send Telegram confirmation if user_id is a Telegram chat_id
            if is_telegram_chat_id(user_id):
                try:
                    # Run async function in sync context
                    asyncio.run(send_subscription_confirmation(user_id, game_id))
                except Exception as e:
                    # Log error but don't fail the subscription
                    logger = logging.getLogger(__name__)
                    logger.warning(f"Could not send Telegram confirmation: {e}")
            
            return jsonify({
                'success': True,
                'message': message,
                'subscriptions': subscriptions,
                'tier': info['tier'],
                'subscription_count': info['subscription_count'],
                'max_subscriptions': info['max_subscriptions']
            })
        else:
            return jsonify({'error': message}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/subscriptions/unsubscribe', methods=['POST'])
def api_unsubscribe():
    """Unsubscribe user from a game"""
    try:
        data = request.get_json()
        game_id = data.get('game_id')
        user_id = request.headers.get('X-User-ID') or data.get('user_id')
        
        if not user_id:
            user_id = 'web_anonymous'
        
        if not game_id:
            return jsonify({'error': 'game_id is required'}), 400
        
        subscription_manager = SubscriptionManager()
        success, message = subscription_manager.unsubscribe_from_game(user_id, game_id)
        
        if success:
            subscriptions = subscription_manager.get_user_subscriptions(user_id)
            return jsonify({
                'success': True,
                'message': message,
                'subscriptions': subscriptions
            })
        else:
            return jsonify({'error': message}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    templates_dir = Path('templates')
    templates_dir.mkdir(exist_ok=True)
    
    port = int(os.getenv('DASHBOARD_PORT', 5000))
    debug = os.getenv('DASHBOARD_DEBUG', 'true').lower() == 'true'  # Default to True for auto-reload
    
    print(f"Starting Lottery Assistant Dashboard on http://localhost:{port}")
    print(f"Debug mode: {debug} (templates will auto-reload)")
    app.run(host='0.0.0.0', port=port, debug=debug, use_reloader=True)
