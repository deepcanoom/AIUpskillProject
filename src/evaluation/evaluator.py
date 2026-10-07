"""Evaluator for testing agent performance against golden dataset."""

import asyncio
import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class EvaluationMetrics:
    """Metrics for evaluation results."""
    
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    mean_score_error: float
    correct_predictions: int
    total_predictions: int
    
    def to_dict(self) -> Dict:
        """Convert metrics to dictionary."""
        return {
            "accuracy": round(self.accuracy, 3),
            "precision": round(self.precision, 3),
            "recall": round(self.recall, 3),
            "f1_score": round(self.f1_score, 3),
            "mean_score_error": round(self.mean_score_error, 2),
            "correct_predictions": self.correct_predictions,
            "total_predictions": self.total_predictions
        }


class AgentEvaluator:
    """Evaluates agent performance against golden dataset."""
    
    def __init__(self, golden_dataset_path: str):
        """Initialize evaluator with golden dataset.
        
        Args:
            golden_dataset_path: Path to golden dataset JSON file
        """
        self.dataset_path = Path(golden_dataset_path)
        self.test_cases = self._load_dataset()
        
    def _load_dataset(self) -> List[Dict]:
        """Load golden dataset from file."""
        try:
            with open(self.dataset_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('test_cases', [])
        except Exception as e:
            logger.error(f"Failed to load golden dataset: {e}")
            raise
    
    def evaluate_predictions(
        self,
        predictions: List[Dict]
    ) -> Tuple[EvaluationMetrics, List[Dict]]:
        """Evaluate predictions against golden dataset.
        
        Args:
            predictions: List of prediction dictionaries with keys:
                - id: test case id
                - predicted_relevant: boolean
                - predicted_score: int (0-10)
                
        Returns:
            Tuple of (metrics, detailed_results)
        """
        if len(predictions) != len(self.test_cases):
            logger.warning(
                f"Prediction count ({len(predictions)}) doesn't match "
                f"test case count ({len(self.test_cases)})"
            )
        
        # Match predictions to test cases
        pred_map = {p['id']: p for p in predictions}
        
        # Calculate metrics
        true_positives = 0
        false_positives = 0
        true_negatives = 0
        false_negatives = 0
        score_errors = []
        detailed_results = []
        
        for test_case in self.test_cases:
            test_id = test_case['id']
            expected_relevant = test_case['expected_relevant']
            expected_score = test_case['expected_score']
            
            if test_id not in pred_map:
                logger.warning(f"Missing prediction for test case {test_id}")
                continue
            
            pred = pred_map[test_id]
            predicted_relevant = pred.get('predicted_relevant', False)
            predicted_score = pred.get('predicted_score', 0)
            
            # Classification metrics
            if expected_relevant and predicted_relevant:
                true_positives += 1
            elif not expected_relevant and predicted_relevant:
                false_positives += 1
            elif not expected_relevant and not predicted_relevant:
                true_negatives += 1
            elif expected_relevant and not predicted_relevant:
                false_negatives += 1
            
            # Score error
            score_error = abs(expected_score - predicted_score)
            score_errors.append(score_error)
            
            # Detailed result
            detailed_results.append({
                "id": test_id,
                "title": test_case['title'],
                "expected_relevant": expected_relevant,
                "predicted_relevant": predicted_relevant,
                "expected_score": expected_score,
                "predicted_score": predicted_score,
                "score_error": score_error,
                "correct": expected_relevant == predicted_relevant,
                "reason": test_case['reason']
            })
        
        # Calculate metrics
        total = len(detailed_results)
        correct = sum(1 for r in detailed_results if r['correct'])
        
        accuracy = correct / total if total > 0 else 0
        
        # Precision: TP / (TP + FP)
        precision = (
            true_positives / (true_positives + false_positives)
            if (true_positives + false_positives) > 0 else 0
        )
        
        # Recall: TP / (TP + FN)
        recall = (
            true_positives / (true_positives + false_negatives)
            if (true_positives + false_negatives) > 0 else 0
        )
        
        # F1 Score: 2 * (Precision * Recall) / (Precision + Recall)
        f1_score = (
            2 * (precision * recall) / (precision + recall)
            if (precision + recall) > 0 else 0
        )
        
        # Mean score error
        mean_score_error = (
            sum(score_errors) / len(score_errors)
            if score_errors else 0
        )
        
        metrics = EvaluationMetrics(
            accuracy=accuracy,
            precision=precision,
            recall=recall,
            f1_score=f1_score,
            mean_score_error=mean_score_error,
            correct_predictions=correct,
            total_predictions=total
        )
        
        return metrics, detailed_results
    
    def save_results(
        self,
        metrics: EvaluationMetrics,
        detailed_results: List[Dict],
        output_path: str
    ):
        """Save evaluation results to file.
        
        Args:
            metrics: Evaluation metrics
            detailed_results: Detailed results for each test case
            output_path: Path to save results
        """
        results = {
            "metrics": metrics.to_dict(),
            "detailed_results": detailed_results
        }
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Evaluation results saved to {output_path}")
    
    def print_summary(self, metrics: EvaluationMetrics):
        """Print evaluation summary to console."""
        print("\n" + "="*50)
        print("EVALUATION SUMMARY")
        print("="*50)
        print(f"Accuracy:          {metrics.accuracy:.1%}")
        print(f"Precision:         {metrics.precision:.1%}")
        print(f"Recall:            {metrics.recall:.1%}")
        print(f"F1 Score:          {metrics.f1_score:.1%}")
        print(f"Mean Score Error:  {metrics.mean_score_error:.2f}")
        print(f"Correct:           {metrics.correct_predictions}/{metrics.total_predictions}")
        print("="*50 + "\n")


class FilterEvaluator:
    """
    Evaluates news filtering agent.

    Measures:
    - Accuracy (correct classification)
    - Precision (% of relevant that are actually relevant)
    - Recall (% of actual relevant found)
    """

    def __init__(self, golden_dataset_path: str):
        # Imported lazily so that loading this module does not require
        # the LLM stack (litellm) when only AgentEvaluator is needed.
        from src.agents.news_filter_agent import NewsFilterAgent

        self.golden_dataset_path = Path(golden_dataset_path)
        self.agent = NewsFilterAgent()
        self.relevance_threshold = 6

    async def evaluate(self) -> Dict:
        """Run evaluation on golden dataset."""
        # Load golden dataset
        with open(self.golden_dataset_path, encoding="utf-8") as f:
            dataset = json.load(f)

        test_cases = dataset['test_cases']
        print(f"[DATA] Evaluating on {len(test_cases)} test cases...")

        results = []

        for test_case in test_cases:
            print(f"   [{test_case['id']}/{len(test_cases)}] {test_case['title'][:50]}...")

            # Run agent
            judgment = self.agent._judge_relevance({
                'title': test_case['title'],
         'summary': test_case['summary']
            })

            # Check prediction
            predicted_relevant = (
                judgment['relevant'] and
                judgment['relevance_score'] >= self.relevance_threshold
            )
            expected_relevant = test_case['expected_relevant']

            correct = predicted_relevant == expected_relevant

            results.append({
                'test_case_id': test_case['id'],
                'title': test_case['title'],
                'expected': expected_relevant,
         'predicted': predicted_relevant,
                'correct': correct,
                'score': judgment['relevance_score'],
                'reasoning': judgment['reasoning']
            })

            status = "[OK]" if correct else "[FAIL]"
            print(f"      {status} Expected: {expected_relevant}, Predicted: {predicted_relevant}")

        # Calculate metrics
        metrics = self._calculate_metrics(results)

        return {
            'results': results,
            'metrics': metrics,
            'test_cases': len(test_cases)
        }

    def _calculate_metrics(self, results: List[Dict]) -> Dict:
        """Calculate evaluation metrics."""
        # Accuracy
        correct = sum(1 for r in results if r['correct'])
        accuracy = correct / len(results) if results else 0

        # Precision, Recall, F1
        true_positives = sum(
            1 for r in results
            if r['expected'] and r['predicted']
        )
        false_positives = sum(
            1 for r in results
            if not r['expected'] and r['predicted']
        )
        false_negatives = sum(
            1 for r in results
            if r['expected'] and not r['predicted']
        )

        precision = (
            true_positives / (true_positives + false_positives)
            if (true_positives + false_positives) > 0
            else 0
        )

        recall = (
            true_positives / (true_positives + false_negatives)
            if (true_positives + false_negatives) > 0
            else 0
        )

        f1 = (
            2 * (precision * recall) / (precision + recall)
            if (precision + recall) > 0
            else 0
        )

        return {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'correct': correct,
            'total': len(results)
        }

    async def save_report(self, evaluation: Dict, output_path: str):
        """Save evaluation report."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding="utf-8") as f:
            f.write("# News Filter Agent - Evaluation Report\n\n")

            # Metrics
            metrics = evaluation['metrics']
            f.write("## Overall Metrics\n\n")
            f.write(f"- **Accuracy:** {metrics['accuracy']:.1%}\n")
            f.write(f"- **Precision:** {metrics['precision']:.1%}\n")
            f.write(f"- **Recall:** {metrics['recall']:.1%}\n")
            f.write(f"- **F1 Score:** {metrics['f1_score']:.3f}\n")
            f.write(f"- **Test Cases:** {metrics['correct']}/{metrics['total']} correct\n\n")

            # Results
            f.write("## Test Results\n\n")

            for result in evaluation['results']:
                status = "PASS" if result['correct'] else "FAIL"
                f.write(f"### [{result['test_case_id']}] {status}\n\n")
                f.write(f"**Title:** {result['title']}\n\n")
                f.write(f"- Expected: {'Relevant' if result['expected'] else 'Not Relevant'}\n")
                f.write(
             f"- Predicted: {'Relevant' if result['predicted'] else 'Not Relevant'} "
             f"(score: {result['score']})\n"
         )
                f.write(f"- Reasoning: {result['reasoning']}\n\n")
                f.write("---\n\n")

        print(f"[SAVE] Evaluation report saved to {output_path}")


# Run evaluation
async def run_evaluation():
    """Run evaluation and save report."""
    print("=" * 60)
    print("  News Filter Agent Evaluation")
    print("=" * 60)

    evaluator = FilterEvaluator("data/evaluation/golden_dataset.json")
    evaluation = await evaluator.evaluate()

    print("\n[DATA] Results:")
    print(f"   Accuracy:  {evaluation['metrics']['accuracy']:.1%}")
    print(f"   Precision: {evaluation['metrics']['precision']:.1%}")
    print(f"   Recall:    {evaluation['metrics']['recall']:.1%}")
    print(f"   F1 Score:  {evaluation['metrics']['f1_score']:.3f}")

    await evaluator.save_report(evaluation, "data/evaluation/evaluation_report.md")

    print("\n[OK] Evaluation complete!")
    print("   Report: data/evaluation/evaluation_report.md")


if __name__ == "__main__":
    # Allow `python src/evaluation/evaluator.py` from the project root.
    # Running a file directly puts its own folder on sys.path, not the
    # project root, so `import src.*` would fail without this.
    import sys

    _PROJECT_ROOT = Path(__file__).resolve().parents[2]
    if str(_PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(_PROJECT_ROOT))

    asyncio.run(run_evaluation())
