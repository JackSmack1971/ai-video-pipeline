from pathlib import Path
import sys

project_root = Path(__file__).resolve().parents[1]
sys.path.append(str(project_root))

try:
    from observability.tracing import Tracing
except ImportError as e:
    raise ImportError(
        f"Failed to import 'observability.tracing': {e}. "
        "Make sure the module exists and the Python path is correctly configured."
    )


def test_tracing_init():
    tracer = Tracing().tracer
    assert tracer is not None
