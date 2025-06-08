import sys, pathlib; sys.path.append(str(pathlib.Path(__file__).resolve().parents[2]))
import pytest

from utils.load_testing.chaos_simulator import simulated_low_disk_space


@pytest.mark.chaos
def test_disk_space_exhaustion():
    with simulated_low_disk_space(0):
        with pytest.raises(RuntimeError):
            raise RuntimeError("disk full")
