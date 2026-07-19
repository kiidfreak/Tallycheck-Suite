"""Clock-in reminder job runner.

Runs as a separate process from the web app. On each tick it walks every active
tenant and, for tenants with reminders enabled, finds employees who:

  - are approved and active,
  - have not clocked in today, and
  - are inside the reminder window (cutoff minus reminder_minutes_before_cutoff),

then emits one reminder per employee per day.

Run it with:  python -m jobs.reminder_job            (loop, default 5-min tick)
              python -m jobs.reminder_job --once     (single pass, for cron)
              python -m jobs.reminder_job --dry-run  (log only, send nothing)

Times are naive local (Africa/Nairobi, UTC+3, no DST) to match how shift hours
are stored elsewhere in this codebase — see the 24-hour note on Employee in
models.py.
"""
import argparse
import logging
import os
import sys
import time as time_module
from datetime import datetime, timedelta
from typing import Any, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_libs = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../libs'))
if _libs not in sys.path:
    sys.path.insert(0, _libs)

from app import app
from models import db, Employee, AttendanceRecord, OrgSettings, Organization

logger = logging.getLogger("reminder_job")

DEFAULT_TICK_SECONDS = 300

# Employees already reminded today, keyed by (schema, employee_id, date). Held in
# memory, so a restart can re-send a reminder for the current day. Move this to a
# reminders table if at-most-once delivery becomes a requirement.
_sent: set[tuple[str, str, Any]] = set()


def send_reminder(employee: Employee, cutoff_hour: int, dry_run: bool) -> None:
    """Deliver one reminder. Logging is the only channel wired up so far.

    Swap this body for the real transport (email/push/in-app) — the scheduling
    logic around it does not change.
    """
    msg = (
        f"[reminder] {employee.email} has not clocked in; "
        f"window closes at {cutoff_hour:02d}:00"
    )
    if dry_run:
        logger.info("DRY-RUN would send: %s", msg)
    else:
        logger.info(msg)


def due_employees(now: datetime, window_minutes: int) -> list[tuple[Employee, int]]:
    """Employees inside their reminder window who have not clocked in today."""
    today = now.date()

    clocked_in_ids = {
        row.employee_id
        for row in AttendanceRecord.query.with_entities(AttendanceRecord.employee_id)
        .filter(AttendanceRecord.work_date == today)
        .all()
    }

    due: list[tuple[Employee, int]] = []
    for employee in Employee.query.filter_by(is_approved=True, is_active=True).all():
        if employee.id in clocked_in_ids:
            continue

        cutoff_hour = employee.shift_cutoff_hour
        cutoff_at = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(hours=cutoff_hour)
        remind_from = cutoff_at - timedelta(minutes=window_minutes)

        # Inside the window and not yet past the cutoff — once the cutoff passes
        # a reminder is pointless, clock-in is already refused.
        if remind_from <= now < cutoff_at:
            due.append((employee, cutoff_hour))

    return due


def run_for_tenant(schema_name: str, now: datetime, dry_run: bool) -> int:
    """Process one tenant schema. Returns the number of reminders sent."""
    db.session.execute(db.text(f'SET search_path TO "{schema_name}", public'))

    settings = OrgSettings.get()
    if not settings.reminder_enabled:
        return 0

    sent = 0
    for employee, cutoff_hour in due_employees(now, settings.reminder_minutes_before_cutoff):
        key = (schema_name, str(employee.id), now.date())
        if key in _sent:
            continue
        send_reminder(employee, cutoff_hour, dry_run)
        if not dry_run:
            _sent.add(key)
        sent += 1

    return sent


def tick(dry_run: bool = False) -> int:
    """One pass across every active tenant. Returns total reminders sent."""
    now = datetime.now()
    total = 0

    with app.app_context():
        db.session.execute(db.text("SET search_path TO public"))
        tenants = Organization.query.filter_by(is_active=True).all()

        for org in tenants:
            try:
                total += run_for_tenant(org.schema_name, now, dry_run)
            except Exception:
                # One broken tenant must not stop the others.
                logger.exception("reminder pass failed for tenant %s", org.schema_name)
                db.session.rollback()

        db.session.remove()

    return total


def main() -> None:
    parser = argparse.ArgumentParser(description="Clock-in reminder job runner")
    parser.add_argument("--once", action="store_true", help="run a single pass and exit")
    parser.add_argument("--dry-run", action="store_true", help="log reminders without sending or recording them")
    parser.add_argument("--interval", type=int, default=DEFAULT_TICK_SECONDS, help="seconds between passes")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    if args.once:
        count = tick(dry_run=args.dry_run)
        logger.info("single pass complete - %d reminder(s)", count)
        return

    logger.info("reminder job started (interval=%ss, dry_run=%s)", args.interval, args.dry_run)
    while True:
        try:
            count = tick(dry_run=args.dry_run)
            if count:
                logger.info("sent %d reminder(s)", count)
        except Exception:
            logger.exception("reminder tick failed")
        time_module.sleep(args.interval)


if __name__ == "__main__":
    main()
