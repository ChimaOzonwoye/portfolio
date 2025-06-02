"""
Configuration file for Crypto Trading Bot
IMPORTANT: Rename this file to config.py and add your actual API keys
"""

# Coinbase API Configuration
API_KEY = 'your-coinbase-api-key-here'
API_SECRET = 'your-coinbase-api-secret-here'

# Optional: AI Validation API Keys
ANTHROPIC_API_KEY = 'your-claude-api-key-here'  # Optional for AI validation
DEEPSEEK_API_KEY = 'your-deepseek-api-key-here'  # Optional for AI validation

# Trading Configuration
TEST_MODE = True  # Set to False for real trading
PAUSE_HOURS = []  # Hours to pause trading (e.g., [22, 23, 0, 1])
DEFAULT_TRADE_AMOUNT = 7.50  # USD per trade

# Database Configuration
DB_PATH = 'trading_memory.db'

# Journal Configuration
JOURNAL_PATH = 'trading_journal.txt'  # Your trading journal/notes file