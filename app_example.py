from azure.identity import InteractiveBrowserCredential, DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
import os
from typing import Dict, Optional

class SecureConfig:
    """Secure configuration manager using Azure Key Vault."""
    
    def __init__(self, vault_url: str):
        self._vault_url = vault_url
        self._secrets: Dict[str, str] = {}
        
        # Use InteractiveBrowserCredential locally, DefaultAzureCredential in Azure
        if os.getenv("AZURE_DEPLOYMENT"):
            self._credential = DefaultAzureCredential()
        else:
            self._credential = InteractiveBrowserCredential()
        
        self._client = SecretClient(
            vault_url=self._vault_url,
            credential=self._credential
        )
    
    def get_secret(self, secret_name: str, use_cache: bool = True) -> str:
        """Gets a secret from Key Vault or cache."""
        if use_cache and secret_name in self._secrets:
            return self._secrets[secret_name]
            
        value = self._client.get_secret(secret_name).value
        if use_cache:
            self._secrets[secret_name] = value
        return value

# Example usage
if __name__ == "__main__":
    # Initialize configuration
    config = SecureConfig("https://projectanalysis2.vault.azure.net/")
    
    # Example: Configure OpenAI
    try:
        import openai
        openai.api_key = config.get_secret("openai-key")
        print("✓ OpenAI configured successfully")
    except Exception as e:
        print(f"! Error configuring OpenAI: {e}")
    
    # Example: Configure Anthropic
    try:
        import anthropic
        anthropic.api_key = config.get_secret("anthropic-key")
        print("✓ Anthropic configured successfully")
    except Exception as e:
        print(f"! Error configuring Anthropic: {e}")
    
    # Example: Get other secrets
    try:
        google_api_key = config.get_secret("google-api-key")
        print("✓ Google API key retrieved")
    except Exception as e:
        print(f"! Error getting Google API key: {e}")
