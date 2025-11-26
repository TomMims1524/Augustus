"""
Enhanced Training Script for All ProjectAnalysis AI Agents

This script orchestrates the training of all agents using both fine-tuning and RAG:
- Initializes key management and provider configurations
- Sets up training data and RAG documents
- Conducts training sessions for each agent
- Monitors and reports training progress
"""

import asyncio
import logging
from pathlib import Path
from datetime import datetime
import json
import os
from typing import Dict, List, Any, Optional

from app.keyring.secrets import SecretManager
from app.keyring.providers import ProviderCatalog
from app.keyring.agent_keys import AgentKeyContext
from app.fine_tuning.enhanced_agent_trainer import EnhancedAgentTrainingSystem
from app.rag.enhanced_rag_trainer import EnhancedRAGTrainer, RAGConfig
from app.agents.agent_hierarchy import AgentHierarchy

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def prepare_training_data(data_dir: Path) -> None:
    """Prepares training data directory structure."""
    # Create necessary directories
    (data_dir / "fine_tuning").mkdir(parents=True, exist_ok=True)
    (data_dir / "rag").mkdir(parents=True, exist_ok=True)
    
    # Create placeholder files if they don't exist
    placeholder_files = {
        "fine_tuning/civil_engineering_examples.jsonl": [
            {"input": "Design a stormwater management system", "output": "1. Analyze site conditions\n2. Calculate runoff volumes\n3. Design retention basins\n4. Specify drainage infrastructure\n5. Prepare construction drawings"},
            {"input": "Create a road network layout", "output": "1. Determine traffic patterns\n2. Design road geometry\n3. Plan intersections\n4. Specify pavement design\n5. Include safety features"}
        ],
        "fine_tuning/geotechnical_examples.jsonl": [
            {"input": "Analyze soil stability for foundation", "output": "1. Review boring logs\n2. Classify soil types\n3. Calculate bearing capacity\n4. Assess settlement potential\n5. Recommend foundation type"},
            {"input": "Design slope reinforcement", "output": "1. Evaluate slope geometry\n2. Analyze soil properties\n3. Calculate safety factors\n4. Design reinforcement system\n5. Specify construction sequence"}
        ],
        "rag/civil_engineering_handbook.txt": """
Civil Engineering Design Guidelines

1. Site Development
- Perform thorough site analysis
- Consider environmental impact
- Plan for utilities and infrastructure
- Ensure code compliance
- Optimize site layout

2. Structural Design
- Calculate loads accurately
- Select appropriate materials
- Design for safety and efficiency
- Consider constructability
- Follow building codes

3. Transportation Engineering
- Analyze traffic patterns
- Design safe intersections
- Plan for future growth
- Consider multimodal transport
- Implement traffic control
""",
        "rag/geotechnical_handbook.txt": """
Geotechnical Engineering Principles

1. Soil Mechanics
- Understand soil properties
- Analyze soil behavior
- Consider groundwater effects
- Evaluate stability
- Design soil improvements

2. Foundation Engineering
- Select foundation type
- Calculate bearing capacity
- Assess settlement
- Design deep foundations
- Monitor performance

3. Earth Structures
- Design retaining walls
- Analyze slope stability
- Plan excavation support
- Implement ground improvement
- Monitor construction
"""
    }
    
    for file_path, content in placeholder_files.items():
        full_path = data_dir / file_path
        if not full_path.exists():
            with open(full_path, "w") as f:
                if isinstance(content, list):
                    for item in content:
                        f.write(json.dumps(item) + "\n")
                else:
                    f.write(content)

async def train_agent(
    agent_id: str,
    agent_key_context: AgentKeyContext,
    data_dir: Path,
    training_modules: List[str]
) -> Dict[str, Any]:
    """
    Trains a single agent using both fine-tuning and RAG.
    
    Args:
        agent_id: ID of the agent to train
        agent_key_context: Key context for the agent
        data_dir: Directory containing training data
        training_modules: List of modules to train on
        
    Returns:
        Training results
    """
    logger.info(f"Starting training for agent: {agent_id}")
    
    # Initialize training systems
    training_system = EnhancedAgentTrainingSystem(
        agent_id=agent_id,
        agent_key_context=agent_key_context,
        data_dir=data_dir
    )
    
    rag_trainer = EnhancedRAGTrainer(
        agent_id=agent_id,
        agent_key_context=agent_key_context,
        rag_config=RAGConfig(
            chunk_size=1000,
            chunk_overlap=200
        ),
        data_dir=data_dir / "rag"
    )
    
    results = {
        "agent_id": agent_id,
        "start_time": datetime.now().isoformat(),
        "modules": {}
    }
    
    try:
        # Process RAG documents
        doc_ids = []
        for doc_file in (data_dir / "rag").glob("*.txt"):
            doc_id = await rag_trainer.process_document(
                doc_file,
                metadata={"agent_id": agent_id}
            )
            doc_ids.append(doc_id)
        
        # Train each module
        for module in training_modules:
            logger.info(f"Training module '{module}' for agent {agent_id}")
            
            # Prepare fine-tuning data
            training_data = await training_system.prepare_training_data(
                module,
                [str(p) for p in (data_dir / "fine_tuning").glob("*.jsonl")]
            )
            
            # Get RAG context
            rag_context = await rag_trainer.get_training_context(
                topic=module,
                filters={"agent_id": agent_id}
            )
            
            # Conduct training
            module_results = await training_system.train_module(
                module_name=module,
                training_data=training_data,
                fine_tune=True,
                use_rag=True
            )
            
            results["modules"][module] = {
                "fine_tuning_results": module_results.get("fine_tuning_results"),
                "rag_results": module_results.get("rag_results"),
                "rag_context_used": rag_context.get("success", False)
            }
    
    except Exception as e:
        logger.error(f"Error training agent {agent_id}: {e}")
        results["error"] = str(e)
    
    results["end_time"] = datetime.now().isoformat()
    results["status"] = "completed" if "error" not in results else "failed"
    
    return results

async def main():
    # Initialize Key Vault
    vault_name = os.getenv("KEYVAULT_NAME", "projectanalysis2")
    
    secret_manager = SecretManager(vault_name=vault_name)
    
    # Initialize provider catalog and agent key context
    provider_catalog = ProviderCatalog.from_yaml("config/providers.yaml", secret_manager)
    agent_key_context = AgentKeyContext(provider_catalog, secret_manager)
    
    # Initialize agent hierarchy
    hierarchy = AgentHierarchy()
    
    # Prepare training data
    data_dir = Path("data/training")
    await prepare_training_data(data_dir)
    
    print("\nStarting Enhanced Training for All Agents...")
    print("==================================================")
    
    # Get all agents
    all_agents = hierarchy.get_all_agents()
    training_results = {}
    
    # Define training modules for each agent type
    training_modules = {
        "civil_engineering": [
            "autocad_basics",
            "civil_3d",
            "site_planning",
            "infrastructure_design"
        ],
        "geotechnical": [
            "soil_mechanics",
            "foundation_design",
            "slope_stability",
            "ground_improvement"
        ],
        "default": [
            "basic_skills",
            "advanced_techniques",
            "best_practices",
            "industry_standards"
        ]
    }
    
    # Train each agent
    for agent in all_agents:
        print(f"\nTraining agent: {agent.name.upper()}")
        
        # Determine which modules to use
        if "civil" in agent.name:
            modules = training_modules["civil_engineering"]
        elif "geo" in agent.name:
            modules = training_modules["geotechnical"]
        else:
            modules = training_modules["default"]
        
        # Train the agent
        results = await train_agent(
            agent_id=agent.name,
            agent_key_context=agent_key_context,
            data_dir=data_dir,
            training_modules=modules
        )
        
        training_results[agent.name] = results
        
        # Print progress
        status = results.get("status", "unknown")
        print(f"Status: {status}")
        if "error" in results:
            print(f"Error: {results['error']}")
        else:
            for module, module_results in results["modules"].items():
                fine_tuning_score = module_results.get("fine_tuning_results", {}).get("best_score", 0)
                rag_score = module_results.get("rag_results", {}).get("proficiency", 0)
                print(f"Module '{module}':")
                print(f"  - Fine-tuning score: {fine_tuning_score:.2f}")
                print(f"  - RAG proficiency: {rag_score:.2f}")
    
    # Save results
    results_file = Path("training_results_enhanced.json")
    with open(results_file, "w") as f:
        json.dump(training_results, f, indent=2)
    
    print(f"\nTraining results saved to: {results_file}")
    
    # Print summary
    print("\nTraining Summary:")
    print("==================================================")
    completed = sum(1 for r in training_results.values() if r.get("status") == "completed")
    failed = sum(1 for r in training_results.values() if r.get("status") == "failed")
    print(f"Total agents: {len(training_results)}")
    print(f"Completed successfully: {completed}")
    print(f"Failed: {failed}")

if __name__ == "__main__":
    asyncio.run(main())
