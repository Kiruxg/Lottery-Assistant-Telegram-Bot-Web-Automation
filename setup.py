"""
Setup script for Lottery Assistant
Helps users configure the system
"""

import os
import json
from pathlib import Path


def create_env_file():
    """Create .env file from template if it doesn't exist"""
    env_file = Path('.env')
    env_example = Path('env.example')
    
    if env_file.exists():
        print("✅ .env file already exists")
        return
    
    if env_example.exists():
        with open(env_example, 'r') as f:
            content = f.read()
        
        print("📝 Creating .env file from template...")
        print("⚠️  Please edit .env and add your Telegram bot credentials!")
        
        with open(env_file, 'w') as f:
            f.write(content)
        
        print("✅ .env file created")
    else:
        print("❌ env.example not found")


def verify_config():
    """Verify configuration files exist"""
    config_file = Path('config.json')
    
    if not config_file.exists():
        print("❌ config.json not found!")
        return False
    
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        print("✅ config.json is valid")
        return True
    except json.JSONDecodeError:
        print("❌ config.json is invalid JSON")
        return False


def check_dependencies():
    """Check if required packages are installed"""
    required_packages = [
        'requests',
        'beautifulsoup4',
        'telegram',
        'playwright',
        'python-dotenv',
        'schedule'
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing.append(package)
    
    if missing:
        print(f"❌ Missing packages: {', '.join(missing)}")
        print("   Run: pip install -r requirements.txt")
        return False
    else:
        print("✅ All required packages installed")
        return True


def main():
    """Run setup checks"""
    print("🔧 Lottery Assistant Setup\n")
    
    create_env_file()
    print()
    
    verify_config()
    print()
    
    check_dependencies()
    print()
    
    print("📋 Next steps:")
    print("1. Edit .env and add your TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID")
    print("2. (Optional) Edit config.json to customize game settings")
    print("3. Run: python main.py test")
    print("4. Run: python main.py check")


if __name__ == "__main__":
    main()
