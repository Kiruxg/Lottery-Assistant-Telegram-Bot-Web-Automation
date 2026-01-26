"""
Smart Scheduler Module
Handles automated scheduling based on draw times from config
"""

import logging
import json
import os
import sys
from typing import Dict, List, Tuple
from datetime import datetime, time, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)


class LotteryScheduler:
    """Smart scheduler that reads draw times from config"""
    
    def __init__(self, config_path: str = "config.json"):
        """
        Initialize scheduler
        
        Args:
            config_path: Path to configuration file
        """
        self.config_path = config_path
        self.config = self._load_config()
        
        # Draw days mapping
        self.draw_days = {
            'powerball': [0, 2, 5],  # Monday, Wednesday, Saturday (0=Monday)
            'mega_millions': [1, 4],  # Tuesday, Friday
            'lucky_day_lotto_midday': list(range(7)),  # Daily
            'lucky_day_lotto_evening': list(range(7))  # Daily
        }
    
    def _load_config(self) -> Dict:
        """Load configuration from JSON file"""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Config file not found: {self.config_path}")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config file: {e}")
            return {}
    
    def _parse_draw_time(self, time_str: str) -> time:
        """
        Parse draw time string (HH:MM) to time object
        
        Args:
            time_str: Time string in format "HH:MM" or "HH:MM:SS"
            
        Returns:
            time object
        """
        try:
            parts = time_str.split(':')
            hour = int(parts[0])
            minute = int(parts[1])
            return time(hour, minute)
        except (ValueError, IndexError) as e:
            logger.error(f"Invalid time format: {time_str}, error: {e}")
            return time(12, 0)  # Default to noon
    
    def get_schedule_times(self, minutes_after: int = 30, include_reminders: bool = True, reminder_hours_before: int = 3) -> List[Tuple[str, str, time]]:
        """
        Get all scheduled check times based on draw times
        
        Args:
            minutes_after: Minutes after draw to check (default 30)
            include_reminders: Whether to include reminder checks (default True)
            reminder_hours_before: Hours before draw for reminder check (default 3)
            
        Returns:
            List of tuples: (game_id, description, time_object)
        """
        schedule_times = []
        games = self.config.get('lottery_games', {})
        
        for game_id, game_config in games.items():
            if not game_config.get('enabled', False):
                continue
            
            draw_time_str = game_config.get('draw_time', '12:00')
            draw_time = self._parse_draw_time(draw_time_str)
            game_name = game_config.get('name', game_id)
            
            # Calculate check times
            draw_datetime = datetime.combine(datetime.today(), draw_time)
            
            # Regular check - 30 minutes after draw
            after_time = (draw_datetime + timedelta(minutes=minutes_after)).time()
            schedule_times.append((
                game_id,
                f"{game_name} - {minutes_after}min after draw",
                after_time
            ))
            
            # Buy signal reminder - 3 hours before draw
            if include_reminders:
                reminder_minutes = reminder_hours_before * 60
                reminder_time = (draw_datetime - timedelta(minutes=reminder_minutes)).time()
                schedule_times.append((
                    game_id,
                    f"{game_name} - Buy Signal Reminder ({reminder_hours_before}h before)",
                    reminder_time
                ))
        
        return schedule_times
    
    def get_windows_task_scheduler_xml(self) -> str:
        """
        Generate Windows Task Scheduler XML for all scheduled checks
        
        Returns:
            XML string for Task Scheduler
        """
        schedule_times = self.get_schedule_times()
        script_path = os.path.abspath(Path(__file__).parent.parent / "main.py")
        python_exe = sys.executable
        
        xml_parts = []
        
        for game_id, description, check_time in schedule_times:
            # Get draw days for this game
            draw_days = self.draw_days.get(game_id, list(range(7)))
            
            # Create task name
            task_name = f"LotteryCheck_{game_id}_{check_time.strftime('%H%M')}"
            task_name = task_name.replace(' ', '_').replace('-', '_')
            
            # Build schedule based on draw days
            if len(draw_days) == 7:  # Daily
                schedule = f"<ScheduleByDay><DaysInterval>1</DaysInterval></ScheduleByDay>"
            else:
                # Specific days
                day_map = {0: 'Monday', 1: 'Tuesday', 2: 'Wednesday', 3: 'Thursday', 
                          4: 'Friday', 5: 'Saturday', 6: 'Sunday'}
                days = [day_map[d] for d in draw_days]
                schedule = f"<ScheduleByWeek><DaysOfWeek><{','.join(days)}/></DaysOfWeek><WeeksInterval>1</WeeksInterval></ScheduleByWeek>"
            
            xml = f"""<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Description>{description}</Description>
  </RegistrationInfo>
  <Triggers>
    <CalendarTrigger>
      <StartBoundary>{datetime.now().strftime('%Y-%m-%d')}T{check_time.strftime('%H:%M:%S')}</StartBoundary>
      <Enabled>true</Enabled>
      {schedule}
    </CalendarTrigger>
  </Triggers>
  <Actions>
    <Exec>
      <Command>{python_exe}</Command>
      <Arguments>"{script_path}" check</Arguments>
      <WorkingDirectory>{os.path.dirname(script_path)}</WorkingDirectory>
    </Exec>
  </Actions>
</Task>"""
            xml_parts.append((task_name, xml))
        
        return xml_parts
    
    def get_schedule_summary(self) -> str:
        """Get human-readable schedule summary"""
        schedule_times = self.get_schedule_times()
        summary = ["📅 Scheduled Check Times:\n"]
        
        # Group by game
        by_game = {}
        for game_id, description, check_time in schedule_times:
            if game_id not in by_game:
                by_game[game_id] = []
            by_game[game_id].append((description, check_time))
        
        for game_id, times in by_game.items():
            game_config = self.config.get('lottery_games', {}).get(game_id, {})
            game_name = game_config.get('name', game_id)
            draw_time = game_config.get('draw_time', '12:00')
            
            summary.append(f"\n🎰 {game_name} (Draw: {draw_time})")
            for desc, check_time in sorted(times, key=lambda x: x[1]):
                summary.append(f"   • {check_time.strftime('%H:%M')} - {desc}")
        
        return "\n".join(summary)
