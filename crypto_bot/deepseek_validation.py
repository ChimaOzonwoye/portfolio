# deepseek_validation.py
import openai
import json
from config import DEEPSEEK_API_KEY, USE_DEEPSEEK

def deepseek_validate_trade(symbol, price, amount, side):
    """Validate trades using DeepSeek's reasoning model"""
    if not USE_DEEPSEEK:
        return True, "Validation disabled (config)"
    
    openai.api_base = "https://api.deepseek.com/v1"
    openai.api_key = DEEPSEEK_API_KEY
    
    try:
        response = openai.ChatCompletion.create(
            model="deepseek-r1",  # Updated to reasoning model
            messages=[
                {
                    "role": "system",
                    "content": json.dumps({
                        "instruction": "Analyze crypto trades",
                        "requirements": "Respond strictly with 'Yes: <reason>' or 'No: <reason>'",
                        "parameters": {
                            "consider": ["market trend", "liquidity", "recent volatility"],
                            "risk_analysis": True
                        }
                    })
                },
                {
                    "role": "user",
                    "content": f"Should I {side} {symbol} at ${price}? Amount: ${amount}"
                }
            ],
            temperature=0.3,
            max_tokens=128,
            timeout=15
        )
        
        ai_response = response.choices[0].message.content.strip()
        return _parse_deepseek_response(ai_response)
        
    except Exception as e:
        print(f"[DeepSeek] Validation Error: {str(e)[:100]}")
        return False, "API validation failed"

def _parse_deepseek_response(response):
    """Parse DeepSeek's structured response"""
    clean_resp = response.lower().replace('*', '').strip()
    
    if clean_resp.startswith('yes:'):
        return True, clean_resp.split(':', 1)[1].strip()
    elif clean_resp.startswith('no:'):
        return False, clean_resp.split(':', 1)[1].strip()
        
    return False, f"Unparseable response: {response[:75]}"

# Example usage:
# should_trade, reason = deepseek_validate_trade("BTC", 50000, 1500, "buy")
