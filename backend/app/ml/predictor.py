import math
from typing import Dict, Any
from app.ml.stub_predictor import assess as stub_assess

def assess(features: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main entry point for assessing battery features.
    Sanitizes features by converting None to float('nan') so the stub predictor's
    NaN-aware guards apply instead of crashing on optional/missing telemetry.
    In Phase 1, delegates to the stub predictor.
    """
    sanitized = {k: (float('nan') if v is None else v) for k, v in features.items()}
    return stub_assess(sanitized)
