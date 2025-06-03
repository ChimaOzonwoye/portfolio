import anthropic
import json

def validate_trade(api_key, symbol, price, amount, side):
    """Validate trade before execution"""
    client = anthropic.Anthropic(api_key=api_key)
    
    try:
        message = client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=1024,
            temperature=0.5,
            messages=[{
                "role": "user",
                "content": f"Should I {side} {symbol} at ${price}? Amount: ${amount}. Consider current market conditions and provide a clear yes/no with brief reasoning."
            }]
        )
        
        # Get Claude's response
        response = message.content
        return "yes" in response.lower(), response
        
    except Exception as e:
        print(f"Claude validation error: {e}")
        return True, "Validation failed, proceeding with caution"
