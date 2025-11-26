import asyncio
import logging
from pathlib import Path
from datetime import datetime
import json

from app.agents.agent_hierarchy import hierarchy
from app.key_management.vault_config import KeyVaultManager, VaultConfig
from app.key_management.llm_config import LLMConfigManager
from app.learning.civil_engineering_trainer import CivilEngineeringTrainer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def verify_and_train_agents():
    """Verify and train all agents in the hierarchy."""
    
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
    
    # Get all agents
    main_agents = hierarchy.get_all_agents()
    sub_agents = hierarchy.get_all_sub_agents()
    
    logger.info("\nVerifying Main Agents...")
    logger.info("=" * 50)
    
    main_agent_results = {}
    for agent in main_agents:
        try:
            # Verify API key
            api_key = vault_manager.get_secret(agent.api_key_secret)
            agent.active = bool(api_key)
            
            if agent.active:
                logger.info(f"{agent.name.upper()}: ACTIVE")
                logger.info(f"Specialization: {agent.specialization.name}")
                logger.info("Skills:")
                for skill in agent.specialization.skills:
                    logger.info(f"  - {skill}")
                logger.info("Tools:")
                for tool in agent.specialization.tools:
                    logger.info(f"  - {tool}")
                
                # Start training
                training_result = await trainer.train_agent(
                    agent.name,
                    "civil_3d",  # Start with Civil 3D module
                    duration_hours=8
                )
                main_agent_results[agent.name] = {
                    "status": "active",
                    "training": training_result,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
            else:
                logger.warning(f"{agent.name.upper()}: INACTIVE (API key not found)")
                main_agent_results[agent.name] = {
                    "status": "inactive",
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
            
        except Exception as e:
            logger.error(f"Failed to verify {agent.name}: {e}")
            main_agent_results[agent.name] = {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
    
    logger.info("\nVerifying Sub-Agents...")
    logger.info("=" * 50)
    
    sub_agent_results = {}
    for agent in sub_agents:
        try:
            # Verify API key
            api_key = vault_manager.get_secret(agent.api_key_secret)
            agent.active = bool(api_key)
            
            if agent.active:
                logger.info(f"{agent.name.upper()}: ACTIVE")
                logger.info(f"Parent Agent: {agent.parent_agent}")
                logger.info(f"Specialization: {agent.specialization.name}")
                logger.info("Skills:")
                for skill in agent.specialization.skills:
                    logger.info(f"  - {skill}")
                logger.info("Tools:")
                for tool in agent.specialization.tools:
                    logger.info(f"  - {tool}")
                
                # Start training
                training_result = await trainer.train_agent(
                    agent.name,
                    "civil_3d",  # Start with Civil 3D module
                    duration_hours=8
                )
                sub_agent_results[agent.name] = {
                    "status": "active",
                    "training": training_result,
                    "parent_agent": agent.parent_agent,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
            else:
                logger.warning(f"{agent.name.upper()}: INACTIVE (API key not found)")
                sub_agent_results[agent.name] = {
                    "status": "inactive",
                    "parent_agent": agent.parent_agent,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
            
        except Exception as e:
            logger.error(f"Failed to verify {agent.name}: {e}")
            sub_agent_results[agent.name] = {
                "status": "error",
                "error": str(e),
                "parent_agent": agent.parent_agent,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
    
    # Save results
    results = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "main_agents": main_agent_results,
        "sub_agents": sub_agent_results
    }
    
    output_path = Path("agent_verification_results.json")
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"\nResults saved to: {output_path}")
    
    # Save agent hierarchy state
    hierarchy.save_state(Path("agent_hierarchy_state.json"))
    
    return results

async def main():
    print("\nVerifying and Training All Agents...")
    print("=" * 50)
    
    results = await verify_and_train_agents()
    
    # Print summary
    print("\nAgent Status Summary:")
    print("=" * 50)
    
    print("\nMain Agents:")
    for name, result in results["main_agents"].items():
        status = result["status"]
        print(f"* {name.upper()}: {status}")
    
    print("\nSub-Agents:")
    for name, result in results["sub_agents"].items():
        status = result["status"]
        parent = result["parent_agent"]
        print(f"* {name.upper()} ({parent}): {status}")

if __name__ == "__main__":
    asyncio.run(main())