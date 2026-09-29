import sys
import os
import json

# Add parent dir to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import SessionLocal
from app.routers.eval import run_evaluation_benchmark

def main():
    print("=" * 60)
    print(" INCIDENT MEMORY AGENT - EVALUATION HARNESS BENCHMARK")
    print("=" * 60)
    
    db = SessionLocal()
    try:
        metrics = run_evaluation_benchmark(db)
        print(f"\nSample Size: {metrics['sample_size']} held-out incidents")
        print(f"Memory Provider: {metrics['provider']}\n")
        
        print(f"{'METRIC':<35} | {'MEMORY OFF':<15} | {'MEMORY ON':<15}")
        print("-" * 70)
        print(f"{'Top-1 Root Cause Match Rate':<35} | {metrics['memory_off']['top1_root_cause_match_pct']:<14}% | {metrics['memory_on']['top1_root_cause_match_pct']:<14}%")
        print(f"{'Correct Fix Inclusion Rate':<35} | {metrics['memory_off']['correct_fix_inclusion_pct']:<14}% | {metrics['memory_on']['correct_fix_inclusion_pct']:<14}%")
        print(f"{'Recall@k Relevant Memories':<35} | {metrics['memory_off']['recall_at_k_pct']:<14}% | {metrics['memory_on']['recall_at_k_pct']:<14}%")
        print("=" * 70)
        
        print("\nDETAILED INCIDENT RESULTS:")
        for item in metrics["detailed_results"]:
            print(f" - [{item['incident_id']}] {item['title']}")
            print(f"   Ground Truth: {item['ground_truth_category']}")
            print(f"   Memory OFF  -> Match: {item['memory_off']['top1_match']}, Fix: {item['memory_off']['fix_included']}")
            print(f"   Memory ON   -> Match: {item['memory_on']['top1_match']}, Fix: {item['memory_on']['fix_included']}, Recalled: {item['memory_on']['recalled_count']}")
            
    finally:
        db.close()

if __name__ == "__main__":
    main()
