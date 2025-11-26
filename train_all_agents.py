import asyncio
import logging
from pathlib import Path
from datetime import datetime
import json

from app.key_management.vault_config import KeyVaultManager, VaultConfig
from app.key_management.llm_config import LLMConfigManager
from app.learning.civil_engineering_trainer import CivilEngineeringTrainer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def train_all_agents():
    """Train all agents in parallel."""
    
    # Initialize Key Vault
    vault_config = VaultConfig(
        vault_url="https://projectanalysis2.vault.azure.net/",
        tenant_id="b56ae302-d62f-40e6-bfc4-a6ce38e28b61",
        use_interactive=True
    )
    
    vault_manager = KeyVaultManager(vault_config)
    llm_manager = LLMConfigManager(vault_manager)
    
    # Initialize trainer
    trainer = CivilEngineeringTrainer(
        llm_manager=llm_manager,
        vault_manager=vault_manager,
        training_data_path=Path("training_data")
    )
    
    # List of all agents to train
    agents = [
        # Main agents
        "civil_engineering",
        "geotechnical",
        "bav",
        "stormwater",
        "siteworks",
        "recommender",
        "sewer",
        
        # Civil Engineering sub-agents
        "structural_design",
        "transportation",
        "environmental",
        "construction_management",
        
        # Geotechnical sub-agents
        "foundation_engineering",
        "soil_mechanics",
        "rock_mechanics",
        "ground_improvement"
    ]
    
    # Start continuous training for each agent
    training_tasks = []
    for agent in agents:
        logger.info(f"\nStarting training for {agent.upper()}...")
        
        # Get initial proficiency
        summary = trainer.get_training_summary(agent)
        logger.info(f"Initial proficiency:\n{json.dumps(summary, indent=2)}")
        
        # Start continuous training
        task = asyncio.create_task(
            trainer.continuous_training(
                agent,
                hours_per_day=8,
                days=21  # 3 weeks of training
            )
        )
        training_tasks.append((agent, task))
    
    # Wait for all training to complete
    results = {}
    for agent, task in training_tasks:
        try:
            await task
            summary = trainer.get_training_summary(agent)
            results[agent] = {
                "status": "completed",
                "summary": summary
            }
            logger.info(f"\nTraining completed for {agent.upper()}:")
            logger.info(json.dumps(summary, indent=2))
        except Exception as e:
            logger.error(f"Training failed for {agent}: {e}")
            results[agent] = {
                "status": "failed",
                "error": str(e)
            }
    
    # Save final results
    output_path = Path("training_results.json")
    with open(output_path, 'w') as f:
        json.dump({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "results": results
        }, f, indent=2)
    
    logger.info(f"\nResults saved to: {output_path}")
    
    return results

async def main():
    print("\nStarting Training for All Agents...")
    print("=" * 50)
    
    results = await train_all_agents()
    
    # Print summary
    print("\nTraining Status Summary:")
    print("=" * 50)
    
    for agent, result in results.items():
        status = result["status"]
        if status == "completed":
            proficiencies = {
                module: data["proficiency"]
                for module, data in result["summary"]["modules"].items()
            }
            avg_proficiency = sum(proficiencies.values()) / len(proficiencies) if proficiencies else 0
            print(f"* {agent.upper()}: {status} (Average Proficiency: {avg_proficiency:.2%})")
        else:
            print(f"* {agent.upper()}: {status} - {result.get('error', 'Unknown error')}")

if __name__ == "__main__":
    asyncio.run(main())
