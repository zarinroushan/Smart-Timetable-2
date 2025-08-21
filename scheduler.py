# # scheduler.py
# from models import db, Subject, Timetable, Classroom, TeacherAvailability
# from collections import defaultdict

# DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri"]
# SLOTS = ["09:00-10:00", "10:00-11:00", "11:00-12:00", "14:00-15:00", "15:00-16:00"]

# def _teacher_available(teacher_id, day, slot):
#     av = TeacherAvailability.query.filter_by(teacher_id=teacher_id, day=day, time_slot=slot).first()
#     return av is not None

# def generate_timetable():
#     # Clear previous
#     Timetable.query.delete()
#     db.session.commit()

#     subjects = Subject.query.all()
#     rooms = Classroom.query.all()
#     if not subjects or not rooms:
#         return {"error": "Need at least one subject and classroom"}, []

#     # Track taken slots per (teacher/day/slot), (room/day/slot), (group/day/slot)
#     teacher_busy = set()
#     room_busy = set()
#     group_busy = set()

#     # Count how many slots assigned per subject for fairness
#     assigned_counts = defaultdict(int)
#     conflicts = []

#     # Simple heuristic: loop days/slots and try to place each subject until it hits freq_per_week
#     for day in DAYS:
#         for slot in SLOTS:
#             for subj in subjects:
#                 if assigned_counts[subj.id] >= subj.freq_per_week:
#                     continue
#                 t_id = subj.teacher_id
#                 g_id = subj.group_id

#                 # must be available and no clash
#                 if not _teacher_available(t_id, day, slot):
#                     continue
#                 if (t_id, day, slot) in teacher_busy or (g_id, day, slot) in group_busy:
#                     continue

#                 # find a room that is free and has capacity
#                 room_chosen = None
#                 for r in rooms:
#                     if (r.id, day, slot) in room_busy:
#                         continue
#                     # Optional capacity check: assume group size ~ count students in group
#                     group_size = len(subj.group.students)
#                     if r.capacity >= group_size:
#                         room_chosen = r
#                         break

#                 if not room_chosen:
#                     # no room available with capacity — record conflict candidate
#                     conflicts.append(f"No room for {subj.code} {day} {slot}")
#                     continue

#                 # place it
#                 tt = Timetable(day=day, time_slot=slot, subject_id=subj.id,
#                                teacher_id=t_id, classroom_id=room_chosen.id, group_id=g_id)
#                 db.session.add(tt)
#                 teacher_busy.add((t_id, day, slot))
#                 group_busy.add((g_id, day, slot))
#                 room_busy.add((room_chosen.id, day, slot))
#                 assigned_counts[subj.id] += 1

#     db.session.commit()

#     # Find any subjects that didn’t reach desired frequency
#     unmet = [s.code for s in subjects if assigned_counts[s.id] < s.freq_per_week]
#     return {"unmet_subjects": unmet}, conflicts



#INCORRECT MAYBE #
# from models import db, Subject, Timetable, Classroom, TeacherAvailability
# from collections import defaultdict

# DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri"]
# SLOTS = ["09:00-10:00", "10:00-11:00", "11:00-12:00", "14:00-15:00", "15:00-16:00"]

# def _teacher_available(teacher_id, day, slot):
#     av = TeacherAvailability.query.filter_by(
#         teacher_id=teacher_id, day=day, time_slot=slot
#     ).first()
#     return av is not None

# def generate_timetable():
#     # Clear previous timetable
#     Timetable.query.delete()
#     db.session.commit()

#     subjects = Subject.query.all()
#     rooms = Classroom.query.all()
#     if not subjects or not rooms:
#         return {"error": "Need at least one subject and classroom"}, []

#     # Track busy slots
#     teacher_busy = set()
#     room_busy = set()
#     group_busy = set()

#     # Count slots assigned per subject
#     assigned_counts = defaultdict(int)
#     conflicts = []

#     for day in DAYS:
#         for slot in SLOTS:
#             for subj in subjects:
#                 if assigned_counts[subj.id] >= subj.freq_per_week:
#                     continue

#                 t_id = subj.teacher_id
#                 g_id = subj.group_id

#                 # Skip if teacher not available or clashes exist
#                 if not _teacher_available(t_id, day, slot):
#                     continue
#                 if (t_id, day, slot) in teacher_busy or (g_id, day, slot) in group_busy:
#                     continue

#                 # Determine group size safely
#                 group_size = 1  # default
#                 if hasattr(subj, 'group') and subj.group is not None:
#                     try:
#                         group_size = len(subj.group.students)
#                     except Exception:
#                         group_size = 1

#                 # Find a suitable room
#                 room_chosen = None
#                 for r in rooms:
#                     if (r.id, day, slot) in room_busy:
#                         continue
#                     if r.capacity >= group_size:
#                         room_chosen = r
#                         break

#                 if not room_chosen:
#                     conflicts.append(f"No room for {subj.code} {subj.name} on {day} {slot}")
#                     continue

#                 # Place timetable entry
#                 tt = Timetable(
#                     day=day,
#                     time_slot=slot,
#                     subject_id=subj.id,
#                     teacher_id=t_id,
#                     classroom_id=room_chosen.id,
#                     group_id=g_id
#                 )
#                 db.session.add(tt)
#                 teacher_busy.add((t_id, day, slot))
#                 group_busy.add((g_id, day, slot))
#                 room_busy.add((room_chosen.id, day, slot))
#                 assigned_counts[subj.id] += 1

#     db.session.commit()

#     unmet = [s.code for s in subjects if assigned_counts[s.id] < s.freq_per_week]

#     return {"unmet_subjects": unmet}, conflicts
# INCORRECT MAYBE #





#     WITHOUT ROOM AVAIBILITY     #
# from models import db, Subject, Timetable, Classroom, TeacherAvailability
# from collections import defaultdict
# import itertools

# DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri"]
# SLOTS = ["09:00-10:00", "10:00-11:00", "11:00-12:00", "14:00-15:00", "15:00-16:00"]

# def _teacher_available(teacher_id, day, slot):
#     return TeacherAvailability.query.filter_by(
#         teacher_id=teacher_id, day=day, time_slot=slot
#     ).first() is not None

# def generate_timetable():
    # Clear old timetable
    # Timetable.query.delete()
    # db.session.commit()

    # subjects = Subject.query.all()
    # rooms = Classroom.query.all()
    # if not subjects or not rooms:
    #     return {"error": "Need at least one subject and classroom"}, []

    # Busy trackers
    # teacher_busy = set()
    # room_busy = set()
    # group_busy = set()

    # Track how many classes assigned per subject
    # assigned_counts = defaultdict(int)
    # conflicts = []

    # Use round-robin room assignment instead of always picking the first
    # room_cycle = itertools.cycle(rooms)

    # for day in DAYS:
    #     for slot in SLOTS:
    #         for subj in subjects:
    #             if assigned_counts[subj.id] >= subj.freq_per_week:
    #                 continue

    #             t_id = subj.teacher_id
    #             g_id = subj.group_id

                # ✅ teacher availability and clash checks
                # if not _teacher_available(t_id, day, slot):
                #     continue
                # if (t_id, day, slot) in teacher_busy:
                #     continue
                # if (g_id, day, slot) in group_busy:
                #     continue

                # ✅ group size
                # group_size = 1
                # if hasattr(subj, "group") and subj.group is not None:
                #     try:
                #         group_size = len(subj.group.students)
                #     except Exception:
                #         group_size = 1

                # ✅ pick a room (rotating through rooms, not always first one)
                # room_chosen = None
                # for _ in range(len(rooms)):
                #     candidate = next(room_cycle)
                #     if (candidate.id, day, slot) in room_busy:
                #         continue
                #     if candidate.capacity >= group_size:
                #         room_chosen = candidate
                #         break

                # if not room_chosen:
                #     conflicts.append(f"No room for {subj.code} ({day} {slot})")
                #     continue

                # ✅ place timetable entry
    #             tt = Timetable(
    #                 day=day,
    #                 time_slot=slot,
    #                 subject_id=subj.id,
    #                 teacher_id=t_id,
    #                 classroom_id=room_chosen.id,
    #                 group_id=g_id,
    #             )
    #             db.session.add(tt)

    #             teacher_busy.add((t_id, day, slot))
    #             group_busy.add((g_id, day, slot))
    #             room_busy.add((room_chosen.id, day, slot))
    #             assigned_counts[subj.id] += 1

    # db.session.commit()

    # ✅ collect unmet subjects
    # unmet = [s.code for s in subjects if assigned_counts[s.id] < s.freq_per_week]

    # return {"unmet_subjects": unmet}, conflicts
#     WITHOUT ROOM AVAIBILITY     #






from models import db, Subject, Timetable, Classroom, TeacherAvailability
from collections import defaultdict
import itertools

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri"]
SLOTS = ["09:00-10:00", "10:00-11:00", "11:00-12:00", "14:00-15:00", "15:00-16:00"]

def _teacher_available(teacher_id, day, slot):
    """Check if a teacher is available at a given day/slot."""
    return TeacherAvailability.query.filter_by(
        teacher_id=teacher_id, day=day, time_slot=slot
    ).first() is not None

def generate_timetable():
    # Clear old timetable
    Timetable.query.delete()
    db.session.commit()

    subjects = Subject.query.all()
    rooms = Classroom.query.all()
    if not subjects or not rooms:
        return {"error": "Need at least one subject and classroom"}, []

    # Busy trackers
    teacher_busy = set()
    room_busy = set()
    group_busy = set()

    # Track how many classes assigned per subject
    assigned_counts = defaultdict(int)
    conflicts = []

    # Round-robin room assignment for fairness
    room_cycle = itertools.cycle(rooms)

    for day in DAYS:
        for slot in SLOTS:
            for subj in subjects:
                if assigned_counts[subj.id] >= subj.freq_per_week:
                    continue

                t_id = subj.teacher_id
                g_id = subj.group_id

                # ✅ teacher availability + clashes
                if not _teacher_available(t_id, day, slot):
                    continue
                if (t_id, day, slot) in teacher_busy:
                    continue
                if (g_id, day, slot) in group_busy:
                    continue

                # ✅ group size (fallback = 1)
                group_size = 1
                if hasattr(subj, "group") and subj.group is not None:
                    try:
                        group_size = len(subj.group.students)
                    except Exception:
                        group_size = 1

                # ✅ pick a free room (capacity check + time clash check)
                room_chosen = None
                for _ in range(len(rooms)):
                    candidate = next(room_cycle)

                    # Room busy at this slot?
                    if (candidate.id, day, slot) in room_busy:
                        continue

                    # Capacity check
                    if candidate.capacity >= group_size:
                        room_chosen = candidate
                        break

                if not room_chosen:
                    conflicts.append(
                        f"No available room (capacity/occupied) for {subj.code} on {day} {slot}"
                    )
                    continue

                # ✅ create timetable entry
                tt = Timetable(
                    day=day,
                    time_slot=slot,
                    subject_id=subj.id,
                    teacher_id=t_id,
                    classroom_id=room_chosen.id,
                    group_id=g_id,
                )
                db.session.add(tt)

                # Mark as busy
                teacher_busy.add((t_id, day, slot))
                group_busy.add((g_id, day, slot))
                room_busy.add((room_chosen.id, day, slot))
                assigned_counts[subj.id] += 1

    db.session.commit()

    # ✅ unmet subjects summary
    unmet = [s.code for s in subjects if assigned_counts[s.id] < s.freq_per_week]

    return {"unmet_subjects": unmet}, conflicts
