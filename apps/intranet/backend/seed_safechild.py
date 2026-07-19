"""Seed SafeChild demo data (children, guardians, and their links).

The SafeChild UI has no "add child" screen, so the roster can only be populated
by seeding. Without children there is nothing to drop off, so no pickup PIN is
ever generated and the Verify Child Checkout screen can only ever return
"Invalid or unrecognized verification PIN".

Idempotent: children are matched by name, so re-running updates links rather
than creating duplicates.

Run:  .venv/Scripts/python seed_safechild.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

workspace_libs = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../libs'))
if workspace_libs not in sys.path:
    sys.path.insert(0, workspace_libs)

from app import app
from models import db, Child, Guardian, ChildGuardian, Employee, SundaySchoolClass, ClassTeacher

SCHEMA_NAME = "tenant_org_0d0uiobbi91ziw0v"

# (child name, sunday-school group, [(guardian name, phone, relation, is_primary)])
ROSTER = [
    ("Amani Wanjiru",   "Sunbeams (3-5)",  [("Grace Wanjiru",  "+254712345601", "Mother", True),
                                            ("Peter Wanjiru",  "+254712345602", "Father", False)]),
    ("Baraka Otieno",   "Sunbeams (3-5)",  [("Mercy Otieno",   "+254712345603", "Mother", True)]),
    ("Zawadi Kimani",   "Explorers (6-8)", [("Joseph Kimani",  "+254712345604", "Father", True),
                                            ("Anne Kimani",    "+254712345605", "Mother", False)]),
    ("Neema Achieng",   "Explorers (6-8)", [("Sarah Achieng",  "+254712345606", "Aunt",   True)]),
    ("Imani Mutua",     "Explorers (6-8)", [("David Mutua",    "+254712345607", "Father", True)]),
    ("Tumaini Njeri",   "Navigators (9-12)", [("Lucy Njeri",   "+254712345608", "Mother", True),
                                              ("Samuel Njeri", "+254712345609", "Uncle",  False)]),
    ("Upendo Kariuki",  "Navigators (9-12)", [("Esther Kariuki", "+254712345610", "Mother", True)]),
    ("Baraka Mwangi",   "Navigators (9-12)", [("John Mwangi",  "+254712345611", "Father", True)]),
]


def seed() -> None:
    with app.app_context():
        db.session.execute(db.text(f'SET search_path TO "{SCHEMA_NAME}", public'))
        db.session.commit()

        created_children = updated_children = 0
        created_guardians = created_links = 0

        for child_name, group_name, guardians in ROSTER:
            child = Child.query.filter_by(name=child_name).first()
            if child is None:
                child = Child(name=child_name, group_name=group_name, is_active=True)
                db.session.add(child)
                db.session.flush()
                created_children += 1
            else:
                child.group_name = group_name
                child.is_active = True
                updated_children += 1

            for g_name, phone, relation, is_primary in guardians:
                guardian = Guardian.query.filter_by(name=g_name, phone=phone).first()
                if guardian is None:
                    guardian = Guardian(name=g_name, phone=phone, relation=relation, is_active=True)
                    db.session.add(guardian)
                    db.session.flush()
                    created_guardians += 1

                link = ChildGuardian.query.filter_by(
                    child_id=child.id, guardian_id=guardian.id
                ).first()
                if link is None:
                    db.session.add(ChildGuardian(
                        child_id=child.id,
                        guardian_id=guardian.id,
                        is_primary=is_primary,
                        authorization_status='approved',
                    ))
                    created_links += 1

        db.session.commit()

        # --- Classes and teacher assignment ---
        # Ensure a class row per distinct group, then point children at it. The
        # migration backfills existing rows; this covers children seeded after.
        class_ids: dict[str, int] = {}
        for _, group_name, _ in ROSTER:
            if group_name in class_ids:
                continue
            klass = SundaySchoolClass.query.filter_by(name=group_name).first()
            if klass is None:
                klass = SundaySchoolClass(name=group_name, is_active=True)
                db.session.add(klass)
                db.session.flush()
            class_ids[group_name] = klass.id
        db.session.commit()

        relinked = 0
        for child_name, group_name, _ in ROSTER:
            child = Child.query.filter_by(name=child_name).first()
            if child and child.class_id != class_ids[group_name]:
                child.class_id = class_ids[group_name]
                relinked += 1
        db.session.commit()

        # Assign every teacher to a class, round-robin, so no teacher logs in to
        # an empty roster. Real assignments would come from an admin screen.
        teachers = [e for e in Employee.query.all() if e.role and e.role.name == 'teacher']
        ordered_classes = [class_ids[g] for g in dict.fromkeys(g for _, g, _ in ROSTER)]
        assigned = 0
        for idx, teacher in enumerate(teachers):
            cid = ordered_classes[idx % len(ordered_classes)]
            if not ClassTeacher.query.filter_by(class_id=cid, teacher_id=teacher.id).first():
                db.session.add(ClassTeacher(class_id=cid, teacher_id=teacher.id, is_lead=True))
                assigned += 1
        db.session.commit()

        print(f"classes:   {len(class_ids)} ensured, {relinked} children relinked")
        print(f"teachers:  {len(teachers)} found, {assigned} class assignment(s) created")
        for t in teachers:
            names = [l.sunday_class.name for l in t.class_links]
            print(f"    {t.email} -> {', '.join(names) or 'UNASSIGNED'}")
        print()
        print(f"children:  {created_children} created, {updated_children} updated")
        print(f"guardians: {created_guardians} created")
        print(f"links:     {created_links} created")
        print(f"\ntotals -> children={Child.query.count()} "
              f"guardians={Guardian.query.count()} links={ChildGuardian.query.count()}")


if __name__ == '__main__':
    seed()
