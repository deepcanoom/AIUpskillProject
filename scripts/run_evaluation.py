"""Script to run evaluation on the news filter agent using golden dataset."""

import asyncio
import json
import logging
import sys
from pathlib import Path
from datetime import datetime

# Run from project root
from src.agents.news_filter_agent import NewsFilterAgent
from src.evaluation.evaluator import AgentEvaluator

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def run_evaluation():
    """Run evaluation on golden dataset."""
    
    # Paths
    golden_dataset_path = "data/evaluation/golden_dataset.json"
    results_path = "data/evaluation/evaluation_results.json"
    
    logger.info("Loading golden dataset...")
    evaluator = AgentEvaluator(golden_dataset_path)
    
    logger.info(f"Loaded {len(evaluator.test_cases)} test cases")
    
    # Initialize agent
    logger.info("Initializing news filter agent...")
    agent = NewsFilterAgent()
    
    # Run predictions
    logger.info("Running predictions on test cases...")
    predictions = []
    
    for i, test_case in enumerate(evaluator.test_cases, 1):
        logger.info(f"Processing test case {i}/{len(evaluator.test_cases)}: {test_case['title']}")
        
        # Create article format expected by agent
        article = {
            "title": test_case['title'],
            "summary": test_case['summary'],
            "source": "golden_dataset"
        }
        
        try:
            # Get agent prediction using internal method
            judgment = agent._judge_relevance(article)
            
            predictions.append({
                "id": test_case['id'],
                "predicted_relevant": judgment.get('relevant', False),
                "predicted_score": judgment.get('relevance_score', 0)
            })
            
            logger.info(
                f"  Prediction: relevant={judgment.get('relevant')}, "
                f"score={judgment.get('relevance_score')}"
            )
            
        except Exception as e:
            logger.error(f"Error processing test case {test_case['id']}: {e}")
            # Add default prediction on error
            predictions.append({
                "id": test_case['id'],
                "predicted_relevant": False,
                "predicted_score": 0
            })
    
    # Evaluate predictions
    logger.info("\nEvaluating predictions...")
    metrics, detailed_results = evaluator.evaluate_predictions(predictions)
    
    # Print summary
    evaluator.print_summary(metrics)
    
    # Print detailed errors
    print("INCORRECT PREDICTIONS:")
    print("-" * 80)
    for result in detailed_results:
        if not result['correct']:
            print(f"❌ Test {result['id']}: {result['title']}")
            print(f"   Expected: relevant={result['expected_relevant']}, score={result['expected_score']}")
            print(f"   Predicted: relevant={result['predicted_relevant']}, score={result['predicted_score']}")
            print(f"   Reason: {result['reason']}")
            print()
    
    # Save results
    logger.info(f"Saving results to {results_path}...")
    evaluator.save_results(metrics, detailed_results, results_path)
    
    # Save timestamped results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    timestamped_path = f"data/evaluation/evaluation_results_{timestamp}.json"
    evaluator.save_results(metrics, detailed_results, timestamped_path)
    
    logger.info("✅ Evaluation complete!")
    
    return metrics


if __name__ == "__main__":
    asyncio.run(run_evaluation())
