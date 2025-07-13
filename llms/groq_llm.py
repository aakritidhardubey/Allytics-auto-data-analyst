import os
import requests
import time
from pandasai.llm.base import LLM
from pandasai.helpers.logger import Logger
import streamlit as st

GROQ_API_KEY=st.secrets["GROQ_API_KEY"]

class GroqLLM(LLM):
    def __init__(self, api_key=None, model="llama-3.1-8b-instant"):  # ✅ Changed to faster model
        
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY must be provided")
        
        self.model = model
        self._logger = Logger()

    @property
    def type(self):
        return "groq"

    def call(self, instruction, context=None):
        """
        Make API call to Groq with rate limit handling
        """
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Handle different instruction types
                if hasattr(instruction, 'to_string'):
                    prompt_text = instruction.to_string()
                elif hasattr(instruction, '__str__'):
                    prompt_text = str(instruction)
                else:
                    prompt_text = instruction
                
                # Clean the prompt
                prompt_text = prompt_text.strip()
                if not prompt_text:
                    prompt_text = "Please provide a response."
                
                # More conservative payload for rate limiting
                payload = {
                    "model": self.model,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt_text
                        }
                    ],
                    "temperature": 0.3,   # Lower temperature for faster processing
                    "max_tokens": 512     #  Reduced token limit to avoid rate limits
                }
                
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                response = requests.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=30
                )
                
                # Handle rate limiting
                if response.status_code == 429:
                    if attempt < max_retries - 1:
                        # Extract wait time from error message or use default
                        wait_time = 3  # Default wait time
                        try:
                            error_data = response.json()
                            error_msg = error_data.get('error', {}).get('message', '')
                            if 'Please try again in' in error_msg:
                                # Extract wait time from message
                                import re
                                match = re.search(r'Please try again in (\d+\.?\d*)s', error_msg)
                                if match:
                                    wait_time = float(match.group(1)) + 1  # Add 1 second buffer
                        except:
                            pass
                        
                        print(f"Rate limit hit. Waiting {wait_time} seconds... (Attempt {attempt + 1}/{max_retries})")
                        time.sleep(wait_time)
                        continue
                    else:
                        raise Exception("Rate limit exceeded. Please wait a moment and try again.")
                
                # Other error handling
                if response.status_code != 200:
                    error_msg = f"Groq API error {response.status_code}: {response.text}"
                    self._logger.log(error_msg)
                    raise Exception(error_msg)
                
                result = response.json()
                
                if "choices" not in result or not result["choices"]:
                    raise Exception("Invalid response from Groq API")
                
                return result["choices"][0]["message"]["content"].strip()
                
            except Exception as e:
                if "rate_limit_exceeded" in str(e) or "429" in str(e):
                    if attempt < max_retries - 1:
                        wait_time = 3 * (attempt + 1)  # Exponential backoff
                        print(f"Rate limit error. Waiting {wait_time} seconds... (Attempt {attempt + 1}/{max_retries})")
                        time.sleep(wait_time)
                        continue
                
                self._logger.log(f"GroqLLM error: {str(e)}")
                raise Exception(f"GroqLLM Error: {str(e)}")

# Test function
def test_groq_connection():
    """Test Groq API connection"""
    print("Testing Groq API connection...")
    
    # Check if API key is set
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("GROQ_API_KEY environment variable not set")
        print("Please set it with: export GROQ_API_KEY='your_api_key_here'")
        return False
    
    # Test direct API call
    try:
        llm = GroqLLM()
        response = llm.call("What is 2+2?")
        print(f" Direct API test successful: {response}")
        return True
    except Exception as e:
        print(f" Direct API test failed: {e}")
        return False

def test_with_pandasai():
    """Test with PandasAI"""
    try:
        import pandas as pd
        from pandasai import Agent
        
        print("\nTesting with PandasAI...")
        
        # Simple test data
        data = {
            'height': [170, 180, 165, 175, 190, 160, 185],
            'name': ['Alice', 'Bob', 'Charlie', 'Diana', 'Eve', 'Frank', 'Grace']
        }
        df = pd.DataFrame(data)
        
        # Create LLM and agent
        llm = GroqLLM()
        agent = Agent(df, config={"llm": llm, "verbose": False})
        
        # Test the problematic query
        result = agent.chat("what is max height?")
        print(f"PandasAI test successful: {result}")
        
        # Additional test
        result2 = agent.chat("what is the average height?")
        print(f"Average height: {result2}")
        
        return True
        
    except Exception as e:
        print(f"PandasAI test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Groq LLM tests...")
    
    # Test 1: Direct API connection
    if test_groq_connection():
        # Test 2: With PandasAI
        test_with_pandasai()
    else:
        print("\nTroubleshooting steps:")
        print("1. Make sure you have a valid Groq API key")
        print("2. Set the environment variable: export GROQ_API_KEY='your_key'")
        print("3. Check your internet connection")
        print("4. Verify the API key at https://console.groq.com/keys")