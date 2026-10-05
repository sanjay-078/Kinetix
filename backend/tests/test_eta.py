import time
import pytest
from app.services.ingestion import calculate_eta

def test_calculate_eta_normal():
    start_time = time.time() - 10.0  # 10 seconds ago
    speed, elapsed, comp_dt = calculate_eta(total=100, scanned=20, start_time=start_time)
    
    assert speed == 2.0  # 20 msgs / 10 sec = 2 msgs/sec
    assert elapsed >= 10.0
    assert comp_dt is not None

def test_calculate_eta_zero_scanned():
    speed, elapsed, comp_dt = calculate_eta(total=100, scanned=0, start_time=time.time())
    assert speed == 0.0
    assert comp_dt is None
