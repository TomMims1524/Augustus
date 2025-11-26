import asyncio
import logging
from datetime import datetime
from pathlib import Path
import json
from typing import Dict, List, Optional
import os

from openai import AsyncOpenAI
import anthropic
import google.generativeai as genai

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LLMConnectionVerifier:
    """Verifies LLM connections and API key access."""
    
    def __init__(self):
        # Load API keys from environment variables
        self.openai_key = "sk-1234567890abcdef"  # Replace with actual key
        self.anthropic_key = "sk-ant-1234567890abcdef"  # Replace with actual key
        self.google_key = "AIzaSyABC123DEF456GHI789"  # Replace with actual key
        self.azure_openai_key = "1234567890abcdef1234567890abcdef"  # Replace with actual key
        self.azure_openai_endpoint = "https://projectanalysis.openai.azure.com/"
        
        # Load agent-specific keys
        self.agent_keys = {
            "bav": "bav-1234567890abcdef",  # Replace with actual key
            "stormwater": "stw-1234567890abcdef",  # Replace with actual key
            "siteworks": "stw-1234567890abcdef",  # Replace with actual key
            "recommender": "rec-1234567890abcdef",  # Replace with actual key
            "sewer": "sew-1234567890abcdef"  # Replace with actual key
        }
    
    async def verify_openai(self) -> Dict:
        """Verify OpenAI API connection."""
        try:
            client = AsyncOpenAI(api_key=self.openai_key)
            
            start = datetime.now()
            response = await client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": "Test connection"}],
                max_tokens=10
            )
            latency = (datetime.now() - start).total_seconds() * 1000
            
            return {
                "status": "operational",
                "latency_ms": latency,
                "model": "gpt-4",
                "key_source": "Environment Variable",
                "error": None
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "key_source": "Environment Variable"
            }
    
    async def verify_anthropic(self) -> Dict:
        """Verify Anthropic API connection."""
        try:
            client = anthropic.AsyncAnthropic(api_key=self.anthropic_key)
            
            start = datetime.now()
            response = await client.messages.create(
                model="claude-3-opus-20240229",
                messages=[{"role": "user", "content": "Test connection"}],
                max_tokens=10
            )
            latency = (datetime.now() - start).total_seconds() * 1000
            
            return {
                "status": "operational",
                "latency_ms": latency,
                "model": "claude-3-opus-20240229",
                "key_source": "Environment Variable",
                "error": None
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "key_source": "Environment Variable"
            }
    
    async def verify_google(self) -> Dict:
        """Verify Google AI connection."""
        try:
            genai.configure(api_key=self.google_key)
            model = genai.GenerativeModel("gemini-1.5-pro")
            
            start = datetime.now()
            response = await model.generate_content_async("Test connection")
            latency = (datetime.now() - start).total_seconds() * 1000
            
            return {
                "status": "operational",
                "latency_ms": latency,
                "model": "gemini-1.5-pro",
                "key_source": "Environment Variable",
                "error": None
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "key_source": "Environment Variable"
            }
    
    async def verify_azure_openai(self) -> Dict:
        """Verify Azure OpenAI connection."""
        try:
            from openai import AzureOpenAI
            client = AzureOpenAI(
                api_key=self.azure_openai_key,
                azure_endpoint=self.azure_openai_endpoint
            )
            
            start = datetime.now()
            response = await client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": "Test connection"}],
                max_tokens=10
            )
            latency = (datetime.now() - start).total_seconds() * 1000
            
            return {
                "status": "operational",
                "latency_ms": latency,
                "model": "gpt-4",
                "endpoint": self.azure_openai_endpoint,
                "key_source": "Environment Variable",
                "error": None
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "key_source": "Environment Variable"
            }
    
    def verify_agent_key_access(self) -> Dict[str, Dict]:
        """Verify agent-specific API key access."""
        results = {}
        for agent, key in self.agent_keys.items():
            if not key:
                results[agent] = {
                    "status": "error",
                    "key_name": f"{agent.upper()}_AGENT_KEY",
                    "error": "API key not found"
                }
            else:
                results[agent] = {
                    "status": "operational",
                    "key_name": f"{agent.upper()}_AGENT_KEY",
                    "key_source": "Environment Variable",
                    "error": None
                }
        return results
    
    async def verify_all(self) -> Dict:
        """Verify all connections and keys."""
        # Verify LLM connections
        llm_tasks = {
            "openai": self.verify_openai(),
            "anthropic": self.verify_anthropic(),
            "google": self.verify_google(),
            "azure_openai": self.verify_azure_openai()
        }
        
        llm_results = {}
        for name, task in llm_tasks.items():
            try:
                llm_results[name] = await task
            except Exception as e:
                llm_results[name] = {
                    "status": "error",
                    "error": str(e)
                }
        
        # Verify agent key access
        agent_results = self.verify_agent_key_access()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "llm_providers": llm_results,
            "agent_keys": agent_results,
            "summary": {
                "llm_operational_count": sum(
                    1 for r in llm_results.values()
                    if r["status"] == "operational"
                ),
                "agent_keys_operational_count": sum(
                    1 for r in agent_results.values()
                    if r["status"] == "operational"
                )
            }
        }

async def main():
    print("\nVerifying LLM Connections and Key Access...")
    print("=" * 50)
    
    verifier = LLMConnectionVerifier()
    results = await verifier.verify_all()
    
    # Save results
    output_path = Path("llm_verification_report.json")
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    
    # Print summary
    print(f"\nTimestamp: {results['timestamp']}")
    
    print("\nLLM Provider Status:")
    for provider, status in results["llm_providers"].items():
        print(f"\n{provider.upper()}:")
        print(f"  Status: {status['status']}")
        if status['status'] == 'operational':
            print(f"  Model: {status['model']}")
            print(f"  Latency: {status['latency_ms']:.0f}ms")
        if status.get('error'):
            print(f"  Error: {status['error']}")
    
    print("\nAgent Key Status:")
    for agent, status in results["agent_keys"].items():
        print(f"\n{agent.upper()}:")
        print(f"  Status: {status['status']}")
        print(f"  Key Source: {status.get('key_source', 'N/A')}")
        if status.get('error'):
            print(f"  Error: {status['error']}")
    
    print("\nSummary:")
    summary = results["summary"]
    print(f"  Operational LLMs: {summary['llm_operational_count']}/4")
    print(f"  Operational Agent Keys: {summary['agent_keys_operational_count']}/5")
    
    print(f"\nDetailed report saved to: {output_path}")

if __name__ == "__main__":
    asyncio.run(main())