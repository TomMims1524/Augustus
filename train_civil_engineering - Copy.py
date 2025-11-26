import asyncio
import logging
from pathlib import Path
from datetime import datetime
import json

from app.key_management.vault_config import KeyVaultManager, VaultConfig
from app.key_management.llm_config import LLMConfigManager, AgentKeyManager
from app.learning.civil_engineering_trainer import CivilEngineeringTrainer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    # Initialize Key Vault
    vault_config = VaultConfig(
        vault_url="https://projectanalysis2.vault.azure.net/",
        tenant_id="b56ae302-d62f-40e6-bfc4-a6ce38e28b61",
        use_interactive=True
    )
    
    vault_manager = KeyVaultManager(vault_config)
    
    # Initialize LLM and Agent managers
    llm_manager = LLMConfigManager(vault_manager)
    agent_manager = AgentKeyManager(vault_manager)
    
    # Verify configurations
    logger.info("Verifying LLM configurations...")
    llm_status = llm_manager.verify_all_providers()
    logger.info(f"LLM Status:\n{json.dumps(llm_status, indent=2)}")
    
    logger.info("\nVerifying agent keys...")
    agent_status = agent_manager.verify_agent_keys()
    logger.info(f"Agent Status:\n{json.dumps(agent_status, indent=2)}")
    
    # Initialize trainer
    trainer = CivilEngineeringTrainer(
        llm_manager=llm_manager,
        vault_manager=vault_manager,
        training_data_path=Path("training_data")
    )
    
    # Start training for each agent
    agents = ["bav", "stormwater", "siteworks", "recommender", "sewer"]
    training_tasks = []
    
    for agent in agents:
        if agent_status.get(agent, False):
            logger.info(f"\nStarting training for {agent.upper()} agent...")
            
            # Get initial proficiency
            summary = trainer.get_training_summary(agent)
            logger.info(f"Initial proficiency:\n{json.dumps(summary, indent=2)}")
            
            # Start continuous training
            task = asyncio.create_task(
                trainer.continuous_training(
                    agent,
                    hours_per_day=8,
                    days=21
                )
            )
            training_tasks.append(task)
        else:
            logger.warning(f"Skipping {agent} - key verification failed")
    
    # Wait for all training to complete
    if training_tasks:
        await asyncio.gather(*training_tasks)
        
        # Print final summaries
        logger.info("\nTraining Complete!")
        logger.info("Final Proficiency Levels:")
        
        for agent in agents:
            if agent_status.get(agent, False):
                summary = trainer.get_training_summary(agent)
                logger.info(f"\n{agent.upper()}:")
                logger.info(json.dumps(summary, indent=2))
    
    # Save final state
    output_path = Path("training_results.json")
    results = {
        "timestamp": datetime.now().isoformat(),
        "llm_status": llm_status,
        "agent_status": agent_status,
        "training_results": {
            agent: trainer.get_training_summary(agent)
            for agent in agents
            if agent_status.get(agent, False)
        }
    }
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"\nResults saved to: {output_path}")

if __name__ == "__main__":
    asyncio.run(main())
