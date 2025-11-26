from typing import Dict, Any, Optional, List
from secret_manager import SecretManager, get_secret
import logging
from functools import lru_cache

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

VAULT_URL = "https://projectanalysis2.vault.azure.net/"

class AIAgentManager:
    """Manages AI agent configurations and credentials."""
    
    def __init__(self, vault_url: str = VAULT_URL, environment: str = None):
        self.secret_manager = SecretManager(vault_url, environment)
        self.environment = environment or "dev"
        self._configs: Dict[str, Any] = {}
        
    def _get_secret_name(self, base_name: str) -> str:
        """Get environment-specific secret name."""
        if self.environment != "prod":
            return f"{base_name}-{self.environment}"
        return base_name
    
    def init_llm_providers(self) -> Dict[str, Any]:
        """Initialize all LLM providers."""
        configs = {}
        
        # OpenAI
        try:
            configs["openai"] = {
                "api_key": self.secret_manager.get_secret(self._get_secret_name("openai-key")),
                "org_id": self.secret_manager.get_secret(self._get_secret_name("openai-org-id")),
                "model": "gpt-4o-mini"  # Default model
            }
        except Exception as e:
            logger.warning(f"OpenAI configuration failed: {e}")
        
        # Anthropic
        try:
            configs["anthropic"] = {
                "api_key": self.secret_manager.get_secret(self._get_secret_name("anthropic-key")),
                "model": "claude-3-haiku-20240307"
            }
        except Exception as e:
            logger.warning(f"Anthropic configuration failed: {e}")
        
        # Google AI
        try:
            configs["google"] = {
                "api_key": self.secret_manager.get_secret(self._get_secret_name("google-api-key")),
                "model": "gemini-1.5-pro"
            }
        except Exception as e:
            logger.warning(f"Google AI configuration failed: {e}")
        
        # Deepseek
        try:
            configs["deepseek"] = {
                "api_key": self.secret_manager.get_secret(self._get_secret_name("deepseek-key")),
                "model": "deepseek-chat"
            }
        except Exception as e:
            logger.warning(f"Deepseek configuration failed: {e}")
        
        return configs
    
    def init_agent_specific_configs(self) -> Dict[str, Any]:
        """Initialize agent-specific configurations."""
        configs = {}
        
        # BAV Agent
        try:
            configs["bav_agent"] = {
                "api_key": self.secret_manager.get_secret(self._get_secret_name("bav-api-key")),
                "visualization_config": {
                    "include_tooltips": True,
                    "enable_3d": True
                }
            }
        except Exception as e:
            logger.warning(f"BAV Agent configuration failed: {e}")
        
        # Stormwater Agent
        try:
            configs["stormwater_agent"] = {
                "api_key": self.secret_manager.get_secret(self._get_secret_name("stormwater-api-key")),
                "enable_groundwater_modeling": True
            }
        except Exception as e:
            logger.warning(f"Stormwater Agent configuration failed: {e}")
        
        # Road Construction Agent
        try:
            configs["road_construction_agent"] = {
                "api_key": self.secret_manager.get_secret(self._get_secret_name("road-construction-api-key")),
                "enable_cost_optimization": True
            }
        except Exception as e:
            logger.warning(f"Road Construction Agent configuration failed: {e}")
        
        # Recommender Agent
        try:
            configs["recommender_agent"] = {
                "api_key": self.secret_manager.get_secret(self._get_secret_name("recommender-api-key")),
                "enable_analytics": True
            }
        except Exception as e:
            logger.warning(f"Recommender Agent configuration failed: {e}")
        
        # Sewer Expert Agent
        try:
            configs["sewer_expert_agent"] = {
                "api_key": self.secret_manager.get_secret(self._get_secret_name("sewer-expert-api-key")),
                "power_rate_usd_kwh": 0.13
            }
        except Exception as e:
            logger.warning(f"Sewer Expert Agent configuration failed: {e}")
        
        # Financial Analyst Agent
        try:
            configs["financial_analyst_agent"] = {
                "api_key": self.secret_manager.get_secret(self._get_secret_name("financial-analyst-api-key")),
                "enable_real_time_data": True
            }
        except Exception as e:
            logger.warning(f"Financial Analyst Agent configuration failed: {e}")
        
        return configs
    
    def init_all(self) -> Dict[str, Any]:
        """Initialize all AI configurations."""
        self._configs = {
            "llm_providers": self.init_llm_providers(),
            "agents": self.init_agent_specific_configs()
        }
        return self._configs
    
    @lru_cache(maxsize=None)
    def get_agent_config(self, agent_name: str) -> Dict[str, Any]:
        """Get configuration for a specific agent."""
        if not self._configs:
            self.init_all()
        
        agent_config = self._configs.get("agents", {}).get(agent_name, {})
        llm_config = self._configs.get("llm_providers", {})
        
        return {
            "agent_config": agent_config,
            "llm_config": llm_config
        }
    
    def refresh_configs(self) -> None:
        """Force refresh all configurations."""
        self._configs = {}
        self.get_agent_config.cache_clear()
        self.init_all()
