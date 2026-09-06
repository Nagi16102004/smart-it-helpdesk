from datetime import datetime, timedelta

SLA_HOURS = {
    "P1": 2,
    "P2": 4,
    "P3": 8,
    "P4": 24,
}


def calculate_sla_deadline(priority, created_at):
    hours = SLA_HOURS.get(priority, 24)
    return created_at + timedelta(hours=hours)


def get_sla_status(sla_deadline):
    if datetime.utcnow() > sla_deadline:
        return "Breached"
    return "Within SLA"