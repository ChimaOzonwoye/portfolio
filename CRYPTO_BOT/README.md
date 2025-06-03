# Advanced Cryptocurrency Trading Bot with AI Validation

An sophisticated automated trading system that combines technical analysis, sentiment analysis, and AI-powered decision validation for cryptocurrency trading.

## 🚀 Key Features

- **Multi-Currency Support**: Trades 8 major cryptocurrency pairs (BTC, ETH, SOL, XRP, DOGE, ADA, AVAX, DOT)
- **AI Decision Validation**: Dual AI integration with Claude and DeepSeek for trade validation
- **Advanced Risk Management**: Dynamic volatility-adjusted stop-loss and 3:1 risk-reward targeting
- **Machine Learning**: Pattern recognition system that learns from historical trades
- **Sentiment Analysis**: NLTK-powered sentiment scoring with unique journal-based wisdom extraction
- **24/7 Operation**: Continuous market monitoring with configurable trading hours
- **Production Safety**: Comprehensive error handling, rate limiting, and resource monitoring

## 🏗️ Architecture

The bot uses a modular object-oriented design with specialized components:

- `EnhancedTradeBot`: Main trading orchestrator
- `TradingMemory`: SQLite-based historical data management
- `ProfitManager`: Automated profit distribution logic
- `SafetyChecks`: Critical validation systems
- `StopLossManager`: Volatility-based risk calculations
- `ConnectionPreserver`: Network resilience and recovery

## 📋 Requirements

- Python 3.12+
- Coinbase Pro account with API access
- Required Python packages (see requirements.txt)
- Optional: Anthropic Claude API key for AI validation
- Optional: DeepSeek API key for additional AI validation

## 🔧 Setup

1. Clone this repository
2. Install dependencies: `pip install -r requirements.txt`
3. Copy `config_example.py` to `config.py`
4. Add your API keys to `config.py`
5. Create a `trading_journal.txt` file for sentiment analysis
6. Run: `python trading_bot.py`

## ⚠️ Important Notes

- This bot involves real financial risk. Start with TEST_MODE = True
- Past performance does not guarantee future results
- Always monitor the bot's operation and set appropriate risk limits
- The journal-based sentiment analysis is unique to this implementation

## 🔐 Security

- API keys are stored locally and never committed to version control
- All exchange communications use encrypted HTTPS
- Balance verification prevents overdrafts
- Rate limiting ensures API compliance

## 📊 Performance Tracking

The bot maintains a comprehensive SQLite database tracking:
- Entry/exit prices and timestamps
- Profit/loss for each trade
- Market conditions at trade time
- Confidence scores and decision factors

## 🤖 AI Integration

The optional AI validation layer provides an additional safety check by:
- Analyzing market conditions
- Evaluating trade confidence
- Providing reasoning for trade decisions
- Acting as a circuit breaker for uncertain conditions

---

**Disclaimer**: This software is for educational purposes. Cryptocurrency trading carries substantial risk of loss.