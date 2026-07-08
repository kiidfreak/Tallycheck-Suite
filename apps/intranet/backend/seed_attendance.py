import random
from datetime import datetime, timedelta, date, time
from typing import Any
from __init__ import create_app
from models import db, Employee, AttendanceRecord

def seed_attendance() -> None:
    app = create_app()
    with app.app_context():
        employees = Employee.query.all()
        if not employees:
            print("No employees found. Please register or seed employees first.")
            return

        print(f"Generating 30 days of attendance for {len(employees)} employees...")

        today: date = date.today()
        # Start 30 days ago
        start_date: date = today - timedelta(days=30)

        records_created: int = 0

        for i in range(31): # 0 to 30 days
            current_date: date = start_date + timedelta(days=i)
            
            # Skip weekends to make it realistic
            if current_date.weekday() >= 5:
                continue

            for emp in employees:
                # 10% chance the employee was absent
                if random.random() < 0.10:
                    continue
                
                # Randomize clock in between 07:45 AM and 08:30 AM
                # (08:00 AM is the cutoff for being 'late')
                in_hour: int = 7 if random.random() < 0.6 else 8
                in_minute: int = random.randint(45, 59) if in_hour == 7 else random.randint(0, 30)
                
                clock_in_dt: datetime = datetime.combine(current_date, time(in_hour, in_minute))
                
                # Clock out 8 to 9 hours later
                work_duration: timedelta = timedelta(hours=random.uniform(8.0, 9.5))
                clock_out_dt: datetime = clock_in_dt + work_duration

                record = AttendanceRecord(
                    employee_id=emp.id,
                    clock_in=clock_in_dt,
                    clock_out=clock_out_dt,
                    work_date=current_date,
                    source='web',
                    status='closed'
                )
                db.session.add(record)
                records_created += 1

        db.session.commit()
        print(f"Success! Seeded {records_created} attendance records perfectly.")

if __name__ == "__main__":
    seed_attendance()
