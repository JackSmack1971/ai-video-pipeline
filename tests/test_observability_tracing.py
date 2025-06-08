from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parents[1]))

from observability.tracing import Tracing


def test_tracing_init():
    tracer = Tracing().tracer
    assert tracer is not None
