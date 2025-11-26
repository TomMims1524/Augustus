import asyncio
import logging
from pathlib import Path
import json

from app.keyring.secrets import SecretManager
from app.keyring.providers import ProviderCatalog
from app.learning.enhanced_trainer import EnhancedTrainer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Agent training configurations
AGENT_CONFIGS = {
    "civil_engineering": {
        "domain": "civil_engineering",
        "provider_order": ["azure_openai", "openai", "anthropic"],
        "use_fine_tuning": True,
        "use_rag": True,
        "embedding_provider": "azure_openai",
        "hyperparameters": {
            "epochs": 3,
            "batch_size": 4,
            "learning_rate": 1e-5
        }
    },
    "geotechnical": {
        "domain": "geotechnical",
        "provider_order": ["azure_openai", "openai", "anthropic"],
        "use_fine_tuning": True,
        "use_rag": True,
        "embedding_provider": "azure_openai",
        "hyperparameters": {
            "epochs": 3,
            "batch_size": 4,
            "learning_rate": 1e-5
        }
    },
    
    # Civil Engineering sub-agents
    "structural_design": {
        "domain": "structural_design",
        "provider_order": ["azure_openai", "openai", "anthropic"],
        "use_fine_tuning": True,
        "use_rag": True,
        "embedding_provider": "azure_openai"
    },
    "transportation": {
        "domain": "transportation",
        "provider_order": ["azure_openai", "openai", "anthropic"],
        "use_fine_tuning": True,
        "use_rag": True,
        "embedding_provider": "azure_openai"
    },
    "environmental": {
        "domain": "environmental",
        "provider_order": ["azure_openai", "openai", "anthropic"],
        "use_fine_tuning": True,
        "use_rag": True,
        "embedding_provider": "azure_openai"
    },
    "construction_management": {
        "domain": "construction_management",
        "provider_order": ["azure_openai", "openai", "anthropic"],
        "use_fine_tuning": True,
        "use_rag": True,
        "embedding_provider": "azure_openai"
    },
    
    # Geotechnical sub-agents
    "foundation_engineering": {
        "domain": "foundation_engineering",
        "provider_order": ["azure_openai", "openai", "anthropic"],
        "use_fine_tuning": True,
        "use_rag": True,
        "embedding_provider": "azure_openai"
    },
    "soil_mechanics": {
        "domain": "soil_mechanics",
        "provider_order": ["azure_openai", "openai", "anthropic"],
        "use_fine_tuning": True,
        "use_rag": True,
        "embedding_provider": "azure_openai"
    },
    "rock_mechanics": {
        "domain": "rock_mechanics",
        "provider_order": ["azure_openai", "openai", "anthropic"],
        "use_fine_tuning": True,
        "use_rag": True,
        "embedding_provider": "azure_openai"
    },
    "ground_improvement": {
        "domain": "ground_improvement",
        "provider_order": ["azure_openai", "openai", "anthropic"],
        "use_fine_tuning": True,
        "use_rag": True,
        "embedding_provider": "azure_openai"
    },
    
    # Other agents
    "bav": {
        "domain": "bid_analysis",
        "provider_order": ["azure_openai", "openai", "anthropic"],
        "use_fine_tuning": True,
        "use_rag": True,
        "embedding_provider": "azure_openai"
    },
    "stormwater": {
        "domain": "stormwater",
        "provider_order": ["azure_openai", "openai", "anthropic"],
        "use_fine_tuning": True,
        "use_rag": True,
        "embedding_provider": "azure_openai"
    },
    "siteworks": {
        "domain": "siteworks",
        "provider_order": ["azure_openai", "openai", "anthropic"],
        "use_fine_tuning": True,
        "use_rag": True,
        "embedding_provider": "azure_openai"
    },
    "recommender": {
        "domain": "recommendations",
        "provider_order": ["azure_openai", "openai", "anthropic"],
        "use_fine_tuning": True,
        "use_rag": True,
        "embedding_provider": "azure_openai"
    },
    "sewer": {
        "domain": "sewer_systems",
        "provider_order": ["azure_openai", "openai", "anthropic"],
        "use_fine_tuning": True,
        "use_rag": True,
        "embedding_provider": "azure_openai"
    }
}

async def main():
    # Initialize components
    secret_manager = SecretManager(vault_name="projectanalysis2")
    provider_catalog = ProviderCatalog.from_yaml("config/providers.yaml", secret_manager=secret_manager)
    
    trainer = EnhancedTrainer(
        secret_manager=secret_manager,
        provider_catalog=provider_catalog,
        training_data_path=Path("training_data"),
        rag_data_path=Path("rag_data")
    )
    
    print("\nStarting Enhanced Training...")
    print("=" * 50)
    
    # Start training
    results = await trainer.train_all_agents(AGENT_CONFIGS)
    
    # Save results
    output_path = Path("enhanced_training_results.json")
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print("\nTraining Status:")
    print("=" * 50)
    
    for agent_id, result in results.items():
        if "error" in result:
            print(f"* {agent_id:25} ERROR: {result['error']}")
        else:
            status = []
            if result.get("fine_tuning"):
                status.append(f"Fine-tuning: {result['fine_tuning']['status']}")
            if result.get("rag"):
                status.append(f"RAG: {result['rag']['status']}")
            print(f"* {agent_id:25} {', '.join(status)}")
    
    print(f"\nDetailed results saved to: {output_path}")

if __name__ == "__main__":
    asyncio.run(main())
