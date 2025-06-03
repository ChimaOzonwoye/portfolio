# New safety features
import argparse 
from risk_management import StopLossManager, SystemSafety, ConnectionPreserver
import psutil
import ccxt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
import time
import sys
import sqlite3

def is_trading_hour():
    """Controls bot's operating hours. Set to 24/7 operation."""
    current_hour = datetime.now().hour
    return 0 <= current_hour <= 23

class TradingMemory:
    """Stores and analyzes trading history for learning"""
    def __init__(self, db_path='trading_memory.db'):
        self.conn = sqlite3.connect(db_path)
        self.setup_database()
        self.success_patterns = {}
        self.failure_patterns = {}

    def setup_database(self):
        """Create database tables for storing trading history"""
        with self.conn:
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY,
                    timestamp TEXT,
                    symbol TEXT,
                    entry_price REAL,
                    exit_price REAL,
                    profit_loss REAL,
                    market_conditions TEXT,
                    confidence REAL,
                    success BOOLEAN
                )
            ''')

            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS market_conditions (
                    trade_id INTEGER,
                    price_change REAL,
                    volume_change REAL,
                    sentiment_score REAL,
                    volatility REAL,
                    FOREIGN KEY(trade_id) REFERENCES trades(id)
                )
            ''')

    def record_trade(self, trade_data, market_conditions):
        """Record trade and its conditions"""
        try:
            with self.conn:
                cursor = self.conn.cursor()
                cursor.execute('''
                    INSERT INTO trades (
                        timestamp, symbol, entry_price, exit_price,
                        profit_loss, market_conditions, confidence, success
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    trade_data['timestamp'],
                    trade_data['symbol'],
                    trade_data['entry_price'],
                    trade_data.get('exit_price', None),
                    trade_data.get('profit_loss', None),
                    json.dumps(market_conditions),
                    trade_data['confidence'],
                    trade_data.get('success', None)
                ))

                trade_id = cursor.lastrowid
                cursor.execute('''
                    INSERT INTO market_conditions VALUES (?, ?, ?, ?, ?)
                ''', (
                    trade_id,
                    market_conditions['price_change'],
                    market_conditions['volume_change'],
                    market_conditions['sentiment_score'],
                    market_conditions['volatility']
                ))
        except Exception as e:
            print(f"Error recording trade: {str(e)}")

    def analyze_patterns(self):
        """Analyze historical trades to identify successful patterns"""
        try:
            successful_conditions = []
            failed_conditions = []

            cursor = self.conn.execute('''
                SELECT t.*, mc.*
                FROM trades t
                JOIN market_conditions mc ON t.id = mc.trade_id
                WHERE t.success IS NOT NULL
            ''')

            for row in cursor.fetchall():
                conditions = {
                    'price_change': row[8],
                    'volume_change': row[9],
                    'sentiment_score': row[10],
                    'volatility': row[11]
                }

                if row[7]:  # success column
                    successful_conditions.append(conditions)
                else:
                    failed_conditions.append(conditions)

            if successful_conditions:
                self.success_patterns = {
                    'avg_price_change': np.mean([c['price_change'] for c in successful_conditions]),
                    'avg_volume_change': np.mean([c['volume_change'] for c in successful_conditions]),
                    'avg_sentiment': np.mean([c['sentiment_score'] for c in successful_conditions]),
                    'avg_volatility': np.mean([c['volatility'] for c in successful_conditions])
                }

            if failed_conditions:
                self.failure_patterns = {
                    'avg_price_change': np.mean([c['price_change'] for c in failed_conditions]),
                    'avg_volume_change': np.mean([c['volume_change'] for c in failed_conditions]),
                    'avg_sentiment': np.mean([c['sentiment_score'] for c in failed_conditions]),
                    'avg_volatility': np.mean([c['volatility'] for c in failed_conditions])
                }

            return self.success_patterns, self.failure_patterns

        except Exception as e:
            print(f"Error analyzing patterns: {str(e)}")
            return None, None

class ProfitManager:
    """Manages profit distribution and reinvestment"""
    def __init__(self):
        self.reserves = 0.0
        self.trading_pools = {
            'stable_alts': 0.0,
            'volatile_alts': 0.0
        }
        self.investment_tracking = {}

    def process_profit(self, amount, coin_type, coin_category):
        """Process and distribute profits"""
        if coin_category == 'blue_chip':
            self.reserves += amount * 0.5
            alt_amount = amount * 0.5
            self.trading_pools['stable_alts'] += alt_amount * 0.5
            self.trading_pools['volatile_alts'] += alt_amount * 0.5
            print(f"Profit distributed - Reserves: ${self.reserves:.2f}, "
                  f"Stable Alts: ${self.trading_pools['stable_alts']:.2f}, "
                  f"Volatile Alts: ${self.trading_pools['volatile_alts']:.2f}")

        elif coin_category == 'volatile_alts':
            investment = self.investment_tracking.get(coin_type, {})
            if investment:
                current_value = investment.get('current_value', 0)
                initial_investment = investment.get('initial_investment', 0)
                if current_value > initial_investment * 1.5:  # 50% profit
                    profit = current_value - initial_investment
                    self.trading_pools['volatile_alts'] += initial_investment
                    investment['initial_investment'] = profit
                    investment['current_value'] = profit
                    print(f"Took profits from {coin_type} - Reinvesting: ${profit:.2f}")

class SafetyChecks:
    """Implements critical safety features"""
    @staticmethod
    def check_balance(exchange, min_balance=0.0):
        try:
            balance = exchange.fetch_balance()
            usd_balance = float(balance['USD']['free'])
            return usd_balance >= min_balance
        except Exception as e:
            print(f"Error checking balance: {str(e)}")
            return False

    @staticmethod
    def verify_connection(exchange):
        try:
            exchange.fetch_balance()
            return True
        except Exception as e:
            print(f"Connection Error: {str(e)}")
            return False

class EnhancedTradeBot:
    """Main trading bot with learning capabilities"""
    def __init__(self, api_key, api_secret, test_mode=False):
        self.test_mode = test_mode
        self.exchange = ccxt.coinbase({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True
        })
        if self.test_mode:
            print("\n🔧 TEST MODE: No real trades will execute")
        print("Exchange connection initialized successfully")
        
        self.stop_loss = StopLossManager(risk_ratio=3.0)
        self.connection = ConnectionPreserver(self.exchange)
        self.execute_trade = self.connection.secure_execute(self.execute_trade)
        self._init_process_priority()

        self.memory = TradingMemory()
        self.profit_manager = ProfitManager()
        self.safety = SafetyChecks()
        self.sentiment_analyzer = SentimentIntensityAnalyzer()
        nltk.download('vader_lexicon', quiet=True)

        # Initialize tracking variables
        self.last_price_change = 0
        self.last_volume_change = 0
        self.last_sentiment_score = 0
        self.last_volatility = 0
        self.last_confidence = 0

        self.load_config()
        self.active_positions = {}  # Track our positions

    def _init_process_priority(self):
        try:
            psutil.Process().nice(10)
        except Exception as e:
            print(f"Couldn't set process priority: {str(e)}")        

    def load_config(self):
        try:
            from config import MAX_INVESTMENT, TRADING_PAIRS
            self.max_investment = MAX_INVESTMENT
            self.trading_pairs = TRADING_PAIRS
            print(f"Loaded configuration: Max Investment=${self.max_investment}")
        except Exception as e:
            print(f"Error loading configuration: {str(e)}")
            sys.exit(1)

    def analyze_journal_entries(self, sentiment):
        """
        Enhanced journal analysis that better extracts wisdom and personality
        """
        try:
            with open('trading_journal.txt', 'r') as file:
                journal_entries = file.readlines()

            relevant_insights = []

            for entry in journal_entries:
                entry = entry.strip()
                if not entry:  # Skip empty lines
                    continue

                # Analyze sentiment of this insight
                scores = self.sentiment_analyzer.polarity_scores(entry)

                # Look for both direct trading insights and general wisdom
                if sentiment['fear_level'] > 0:
                    # Look for wisdom about handling fear or uncertainty
                    if any(word in entry.lower() for word in ['fear', 'panic', 'worry', 'uncertain']):
                        relevant_insights.append({
                            'entry': entry,
                            'sentiment': scores,
                            'relevance': 'fear_handling'
                        })

                    # Look for wisdom about opportunities
                    if any(word in entry.lower() for word in ['opportunity', 'chance', 'potential']):
                        relevant_insights.append({
                            'entry': entry,
                            'sentiment': scores,
                            'relevance': 'opportunity'
                        })

                # Look for wisdom about patience and timing
                if any(word in entry.lower() for word in ['patient', 'wait', 'timing', 'right time']):
                    relevant_insights.append({
                        'entry': entry,
                        'sentiment': scores,
                        'relevance': 'timing'
                    })

                # Look for wisdom about risk and reward
                if any(word in entry.lower() for word in ['risk', 'reward', 'profit', 'loss']):
                    relevant_insights.append({
                        'entry': entry,
                        'sentiment': scores,
                        'relevance': 'risk_reward'
                    })

                # Look for wisdom about market psychology
                if any(word in entry.lower() for word in ['people', 'market', 'emotion', 'react']):
                    relevant_insights.append({
                        'entry': entry,
                        'sentiment': scores,
                        'relevance': 'psychology'
                    })

            # Apply wisdom to current situation
            if relevant_insights:
                for insight in relevant_insights:
                    if insight['relevance'] == 'fear_handling':
                        # Adjust fear level based on wisdom about handling fear
                        sentiment['fear_level'] *= insight['sentiment']['compound']
                    elif insight['relevance'] == 'opportunity':
                        # Mark potential opportunity
                        sentiment['market_impact'] += " (Opportunity insight found)"
                    elif insight['relevance'] == 'timing':
                        # Add timing consideration
                        sentiment['timing_factor'] = insight['sentiment']['compound']
                    elif insight['relevance'] == 'psychology':
                        # Add market psychology insight
                        sentiment['psychology_factor'] = insight['sentiment']['compound']

            return relevant_insights

        except FileNotFoundError:
            print("Journal file not found")
            return []
        except Exception as e:
            print(f"Error in journal analysis: {str(e)}")
            return []

    def execute_trade(self, symbol, amount, side='buy'):
        """Execute trade with proper market orders"""
        if self.test_mode:
            print(f"\n📊 SIMULATED {side.upper()}: ${amount} {symbol}")
            return {"simulated": True}
        
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            current_price = ticker['last']
            print(f"Current price: ${current_price}")

            # Calculate the amount in crypto
            crypto_amount = amount / current_price
            print(f"Calculated crypto amount: {crypto_amount}")

            if side == 'buy':
                print(f"Placing market buy order: ${amount} of {symbol}")
                order = self.exchange.create_order(
                    symbol=symbol,
                    type='market',
                    side='buy',
                    amount=None,
                    params={
                        'createMarketBuyOrderRequiresPrice': False,
                        'cost': amount  # Specify the amount in USD to spend
                    }
                )
            else:
                print(f"Placing market sell order: {crypto_amount} {symbol}")
                order = self.exchange.create_order(
                    symbol=symbol,
                    type='market',
                    side='sell',
                    amount=crypto_amount
                )

            if order:
                print(f"Order executed: {json.dumps(order, indent=2)}")

            if side == 'buy':
                self.active_positions[symbol] = {
                    'entry_price': current_price,
                    'amount': crypto_amount,
                    'time': datetime.now()
                }
                print(f"Position opened: {symbol} at ${current_price}")

                trade_data = {
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'symbol': symbol,
                    'entry_price': current_price,
                    'confidence': self.last_confidence
                }

                market_conditions = {
                    'price_change': self.last_price_change,
                    'volume_change': self.last_volume_change,
                    'sentiment_score': self.last_sentiment_score,
                    'volatility': self.last_volatility
                }

                self.memory.record_trade(trade_data, market_conditions)
                print(f"Trade recorded in database")

            return order

        except Exception as e:
            print(f"Error executing trade: {str(e)}")
            print(f"Error type: {type(e)}")
            print(f"Full error details: {repr(e)}")
            return None

    def analyze_market_sentiment(self, symbol):
        """Analyze market with guidance from journal wisdom"""
        try:
            df = self.get_market_data(symbol)
            if df is None or df.empty:
                return None

            # Calculate base metrics
            df['price_change'] = df['close'].pct_change() * 100
            recent_change = df['price_change'].iloc[-1]

            sentiment = {
                'fear_level': 0,
                'market_impact': '',
                'action_required': False,
                'timing_factor': 0,
                'psychology_factor': 0
            }

            # Detect basic market conditions
            if recent_change < -2:  # Price drop
                sentiment['fear_level'] = abs(recent_change)
                sentiment['market_impact'] = 'Price drop detected'
                sentiment['action_required'] = True

                # Check volume confirmation
                avg_volume = df['volume'].mean()
                recent_volume = df['volume'].iloc[-1]
                if recent_volume > avg_volume * 1.5:
                    sentiment['market_impact'] += ' with high volume'
                    sentiment['fear_level'] *= 1.2

            # Get journal insights
            insights = self.analyze_journal_entries(sentiment)

            # Apply journal wisdom to decision making
            if insights:
                trade_confidence = 0.0

                for insight in insights:
                    # Adjust confidence based on relevant insights
                    if insight['relevance'] == 'opportunity' and insight['sentiment']['compound'] > 0:
                        trade_confidence += 0.2
                    elif insight['relevance'] == 'psychology' and insight['sentiment']['compound'] > 0:
                        trade_confidence += 0.1
                    elif insight['relevance'] == 'timing' and insight['sentiment']['compound'] > 0:
                        trade_confidence += 0.15

                # If we have good confidence from wisdom, slightly lower the requirements
                if trade_confidence > 0.3:
                    sentiment['fear_level'] *= 0.8  # Reduce fear impact
                    sentiment['action_required'] = True
                    sentiment['market_impact'] += f" (Wisdom confidence: {trade_confidence:.2f})"

            return sentiment

        except Exception as e:
            print(f"Error in market analysis: {str(e)}")
            return None

    def get_market_data(self, symbol):
        """Retrieve market data for analysis"""
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, '1h', limit=24)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df['price_change'] = df['close'].pct_change() * 100
            return df
        except Exception as e:
            print(f"Error fetching market data: {str(e)}")
            return None

    def check_positions(self):
        for symbol, position in self.active_positions.copy().items():
            try:
                if not hasattr(self, 'max_daily_loss'):
                    self.max_daily_loss = 0.02  # Max 2% loss per day
                    print(f"Safety initialized: {self.max_daily_loss*100}% daily loss limit")
                ticker = self.exchange.fetch_ticker(symbol)
                current_price = ticker['last']
                entry_price = position['entry_price']
                # Get actual volatility from market data
                df = self.get_market_data(symbol)
                if df is not None and not df.empty:
                    volatility = df['close'].pct_change().std() * np.sqrt(24)  # 24h volatility
                else:
                    volatility = 0.02  # Fallback value

                
                # Calculate safety levels
                stop_price = self.stop_loss.calculate_dynamic_stop(entry_price, volatility)
                profit_target = self.stop_loss.update_profit_target(entry_price, stop_price)
                
                # Check exit conditions
                if current_price <= stop_price:
                    print(f"Safety stop at {stop_price}")
                    self.execute_trade(symbol, position['amount'], 'sell')
                elif current_price >= profit_target:
                    print(f"Profit hit at {profit_target}")
                    self.execute_trade(symbol, position['amount'], 'sell')
                    
            except Exception as e:
                print(f"Position check error: {str(e)}")
                
    def run(self):
        """Main bot loop with enhanced features"""
        print("Starting Enhanced Trading Bot...")
        print(f"Maximum investment per trade: ${self.max_investment}")
        print("Trading pairs:", self.trading_pairs)
        print("Press Ctrl+C to stop the bot safely")
        
        while True:
            try:
                if not is_trading_hour():
                    print("\nOutside trading hours (0-23). Bot sleeping...")
                    time.sleep(300)
                    continue
                
                if not self.safety.verify_connection(self.exchange):
                    print("Connection check failed. Waiting before retry...")
                    time.sleep(300)
                    continue
                
                # Analyze patterns before trading
                success_patterns, failure_patterns = self.memory.analyze_patterns()
                if success_patterns:
                    print("\nLearned patterns:")
                    print(f"Success patterns: {json.dumps(success_patterns, indent=2)}")
                    print(f"Failure patterns: {json.dumps(failure_patterns, indent=2)}")
                
                for symbol in self.trading_pairs:
                    print(f"\nAnalyzing {symbol}...")
                    
                    sentiment = self.analyze_market_sentiment(symbol)
                    if not sentiment:
                        continue
                    
                    # Calculate confidence with learning adjustment
                    base_confidence = 0.0
                    if sentiment['action_required']:
                        df = self.get_market_data(symbol)  # Get fresh data
                        price_drop = abs(df['price_change'].iloc[-1])  # Use pre-calculated value
                        base_confidence = round(price_drop * 0.1, 2)  # 10% per 1% drop
                        base_confidence = max(0.3, min(base_confidence, 0.7))
                        print(f"Dynamic Confidence: {base_confidence} (Price Drop: {price_drop:.2f}%)")
                    
                    # Store for trade recording
                    self.last_confidence = base_confidence
                    
                    if base_confidence > 0.4:
                        print(f"Trading opportunity found! Confidence: {base_confidence}")
                        
                        balance = self.exchange.fetch_balance()
                        available_usd = float(balance['USD']['free'])
                        
                        if available_usd >= 1.0:
                            # Add DeepSeek validation here
                            from config import DEEPSEEK_API_KEY, USE_DEEPSEEK
                            if USE_DEEPSEEK:
                                from deepseek_validation import deepseek_validate_trade
                                current_price = self.exchange.fetch_ticker(symbol)['last']
                                approved, reasoning = deepseek_validate_trade(
                                    symbol,
                                    current_price,
                                    min(self.max_investment, available_usd),
                                    'buy'
                                )
                                if approved:
                                    order = self.execute_trade(symbol, min(self.max_investment, available_usd))
                                    if order:
                                        print("Trade executed successfully!")
                                else:
                                    print(f"Trade rejected by DeepSeek: {reasoning}")
                            else:
                                # Original code without AI validation
                                order = self.execute_trade(symbol, min(self.max_investment, available_usd))
                                if order:
                                    print("Trade executed successfully!")
                                
                                # Check our positions
                                if self.active_positions:
                                    print("\nChecking current positions...")
                                    self.check_positions()
                time.sleep(60)
                
            except KeyboardInterrupt:
                print("\nBot stopped safely by user.")
                break
            except Exception as e:
                print(f"Error in main loop: {str(e)}")
                time.sleep(60)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--test', action='store_true', help='Enable simulation mode')
    args = parser.parse_args()

    try:
        from config import COINBASE_KEYS
        
        bot = EnhancedTradeBot(
            api_key=COINBASE_KEYS['api_key'],
            api_secret=COINBASE_KEYS['api_secret'],
            test_mode=args.test
        )
        
        bot.run()
        
    except KeyboardInterrupt:
        print("\nBot shutdown initiated by user")
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
