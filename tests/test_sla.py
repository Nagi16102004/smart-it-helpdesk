import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from datetime import datetime, timedelta
from utils.sla import calculate_sla_deadline, get_sla_status


def test_p1_deadline_is_2_hours_later():
    created_at = datetime(2026, 1, 1, 10, 0, 0)
    deadline = calculate_sla_deadline("P1", created_at)
    assert deadline == created_at + timedelta(hours=2)


def test_p4_deadline_is_24_hours_later():
    created_at = datetime(2026, 1, 1, 10, 0, 0)
    deadline = calculate_sla_deadline("P4", created_at)
    assert deadline == created_at + timedelta(hours=24)


def test_sla_status_breached_when_deadline_in_past():
    past_deadline = datetime.utcnow() - timedelta(hours=1)
    assert get_sla_status(past_deadline) == "Breached"


def test_sla_status_within_when_deadline_in_future():
    future_deadline = datetime.utcnow() + timedelta(hours=1)
    assert get_sla_status(future_deadline) == "Within SLA"