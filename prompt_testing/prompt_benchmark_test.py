import time
import json
import requests

class PromptBenchmark:
    """
    Minimal stub for Enricher/Scorer/Classifier tests.
    Simulates API responses so tests run without errors.
    """
    def __init__(self, model="mistral:7b-q4_k_m", debug=True):
        self.model = model
        self.debug = debug

    def call_api(self, prompt):
        """
        Simulate an API call to the LLM.
        Returns a JSON with 4 dummy components for testing.
        """
        import time, random, json
        time.sleep(0.01)  # simulate small delay

        # Simulated components
        response = [
            {"name": "Component A", "cost_share": 0.25, "function": "Function A", "subsystem": "Chassis"},
            {"name": "Component B", "cost_share": 0.25, "function": "Function B", "subsystem": "Electronics"},
            {"name": "Component C", "cost_share": 0.25, "function": "Function C", "subsystem": "Powertrain"},
            {"name": "Component D", "cost_share": 0.25, "function": "Function D", "subsystem": "Suspension"},
        ]

        return {
            "success": True,
            "response": json.dumps(response),
            "time": random.uniform(0.01, 0.05),
            "tokens": random.randint(10, 50),
            "tokens_per_sec": random.uniform(100, 500)
        }
    def calculate_summary(self, tests):
        """Minimal summary calculation"""
        total = len(tests)
        valid = sum(1 for t in tests if t.get('valid'))
        success_rate = valid / total if total else 0
        avg_time = sum(t.get('time', 0) for t in tests) / total if total else 0
        return {
            'total_tests': total,
            'valid_tests': valid,
            'success_rate': success_rate,
            'avg_time_sec': avg_time
        }

    def print_summary(self, label, summary):
        """Minimal summary printing"""
        print(f"{label} Summary:")
        for k, v in summary.items():
            if isinstance(v, float):
                print(f"  {k}: {v:.2f}")
            else:
                print(f"  {k}: {v}")


    def save_results(self, results, filename=None):
        """Save results to a JSON file"""
        if not filename:
            import time
            filename = f"results_{int(time.time())}.json"
        with open(filename, "w") as f:
            json.dump(results, f, indent=2)
        print(f"\nSaved results to {filename}")

