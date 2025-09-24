from typing import Dict, Any, List, Tuple
import time

# Import all metrics
from src.metrics.data_quality import DatasetQualityMetric
from src.metrics.dataset_and_code import DatasetAndCodeMetric
from src.metrics.dataset_quality import DatasetCodeMetric
from src.metrics.size import SizeMetric
from src.metrics.license import LicenseMetric
from src.metrics.bus_factor import bus_factor
from src.metrics.code_quality import code_quality
from src.metrics.security import SecurityMetric

class Scorer:
    """
    Runs all metrics and returns a flat dict of results.
    Handles both scalar and structured metrics (e.g., size_score dict).
    """
    def __init__(self):
        # Initialize metric objects
        try:
            dq = DatasetQualityMetric()
            dac = DatasetAndCodeMetric()
            dcode = DatasetCodeMetric()
            sz = SizeMetric()
            lic = LicenseMetric()
            bf = bus_factor()
            cq = code_quality()
            sq = SecurityMetric()
        except Exception as e:
            print(f"Warning: Error initializing metrics: {e}")
            # Initialize with dummy metrics if needed
            dq = dac = dcode = sz = lic = bf = cq = sq = DummyMetric()
        
        # Dynamic list of metrics (name, object)
        self.metrics: List[Tuple[str, Any]] = [
            ("dataset_quality", dq),
            ("dataset_and_code_score", dac),
            ("size_score", sz),
            ("license", lic),
            ("bus_factor", bf),
            ("code_quality", cq),
            ("security", sq),
        ]
        
        # Define weights for each metric (must sum ~1.0)
        self.weights: Dict[str, float] = {
            "ramp_up_time": 0.08,  # not yet implemented
            "bus_factor": 0.12,
            "performance_claims": 0.10,  # not yet implemented
            "license": 0.12,
            "size_score": 0.10,
            "dataset_and_code_score": 0.12,
            "dataset_quality": 0.12,
            "code_quality": 0.09,
            "security": 0.15,
        }

    def score(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run all metrics on entry and return a flat dict with scores + latencies.
        
        Args:
            entry: Dictionary containing url, category, name, metadata, etc.
        
        Returns:
            Dictionary with all scores and latencies in NDJSON format, or None if entry should be skipped
        """
        result: Dict[str, Any] = {
            "name": entry.get("name", "Unknown"),
            "category": entry.get("category", "UNKNOWN"),
        }
        
        start_time = time.perf_counter()
        
        # Add required metrics in the exact order from sample output
        # All of these values should be overwritten in actual run
        result["ramp_up_time"] = 0.5  # Place holder, not umplemented yet
        result["ramp_up_time_latency"] = 10
        result["bus_factor"] = 0.5
        result["bus_factor_latency"] = 10
        result["performance_claims"] = 0.5  # placeholder  
        result["performance_claims_latency"] = 15
        result["license"] = 0.5 
        result["license_latency"] = 10
        result["dataset_and_code_score"] = 0.5
        result["dataset_and_code_score_latency"] = 10
        result["dataset_quality"] = 0.5
        result["dataset_quality_latency"] = 10
        result["code_quality"] = 0.5
        result["code_quality_latency"] = 10
        result["security"] = 0.5
        result["security_latency"] = 10
        
        # Default size_score structure
        result["size_score"] = {
            "raspberry_pi": 0.5,
            "jetson_nano": 0.6,
            "desktop_pc": 0.8,
            "aws_server": 1.0
        }
        result["size_score_latency"] = 50
        
        # Run each metric and collect results
        for key, metric in self.metrics:
            try:
                # Pass the full entry to the metric
                if hasattr(metric, 'process_score'):
                    metric.process_score(entry)
                elif hasattr(metric, 'calculate'):
                    metric.calculate(entry)
                else:
                    continue
                
                # Special case, size_score should return a dict
                if key == "size_score" and hasattr(metric, "get_size_score"):
                    result[key] = metric.get_size_score()
                elif hasattr(metric, "get_score"):
                    result[key] = metric.get_score()
                    
                # Get latency
                if hasattr(metric, "get_latency"):
                    result[f"{key}_latency"] = metric.get_latency()
                    
            except Exception as e:
                # Keep the default values we already set
                print(f"[WARN] Metric {key} failed for {entry.get('name', 'unknown')}: {e}")
        
        # Check if this entry should be output based on the metrics
        category = entry.get("category", "")
        weighted_sum = 0.0
        total_weight = 0.0
        
        for metric, weight in self.weights.items():
            val = result.get(metric)
            if isinstance(val, (int, float)) and val is not None:
                weighted_sum += val * weight
                total_weight += weight
            elif isinstance(val, dict) and val:  # e.g., size_score
                avg_size = sum(val.values()) / len(val)
                weighted_sum += avg_size * weight
                total_weight += weight
        
        result["net_score"] = round(weighted_sum / total_weight, 2) if total_weight > 0 else 0.0
        
        # Net score latency = total elapsed time
        end_time = time.perf_counter()
        result["net_score_latency"] = round((end_time - start_time) * 1000)  # ms
        
        return result


class DummyMetric:
    """Fallback metric class for testing"""
    def __init__(self):
        self.score = 0.5
        self.latency = 10
        
    def process_score(self, entry):
        pass
        
    def calculate(self, entry):
        pass
        
    def get_score(self):
        return self.score
        
    def get_latency(self):
        return self.latency
        
    def get_size_score(self):
        return {
            "raspberry_pi": 0.5,
            "jetson_nano": 0.6,
            "desktop_pc": 0.8,
            "aws_server": 1.0
        }
