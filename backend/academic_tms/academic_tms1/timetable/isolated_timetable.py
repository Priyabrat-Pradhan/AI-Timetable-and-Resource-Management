"""Timetable demo/generation store isolated from the configured MySQL database."""
import json
import sqlite3
import re
from pathlib import Path

from django.conf import settings


DB_PATH = Path(settings.BASE_DIR) / "ai_timetable_data.sqlite3"
MINING_REFERENCE_COHORT = ("Mining Engineering", "4th Year", "7th Semester")
MINING_LEGACY_CODES = {"ME401", "ME402", "ME403", "ME404", "MN054", "MN056"}
DAYS = ["MON", "TUE", "WED", "THU", "FRI", "SAT"]
DAY_NAMES = {"MON": "Monday", "TUE": "Tuesday", "WED": "Wednesday", "THU": "Thursday", "FRI": "Friday", "SAT": "Saturday"}
SLOTS = [0, 1, 2, 3, 5, 6, 7]
DAY_SLOTS = {day: SLOTS for day in DAYS[:-1]}
DAY_SLOTS[DAYS[-1]] = [0, 1, 2, 3]  # Saturday remains a morning class day.
SLOT_ORDER = {slot: index for index, slot in enumerate(SLOTS)}


def _sample_catalog(department, year, semester, room_inventory=None):
    """Build a branch-relevant sample curriculum without changing saved records."""
    fixed_meetings = {}
    if department == "Computer Science and Engineering" and year == "3rd Year" and semester == "5th Semester":
        subjects = [
            ("CSPC3001", "Theory of Computation", "Liza Rani Behera", "liza.rani@gcek.ac.in", "Theory", "302 Block-II", 3),
            ("CSPC3002", "Operating System", "Srikant Kumar Barik", "srikant.barik@gcek.ac.in", "Theory", "302 Block-II", 3),
            ("CSPC2007", "Computer Networks", "Santoshi Sahoo", "santoshi.sahoo@gcek.ac.in", "Theory", "302 Block-II", 3),
            ("CSPC3003", "Artificial Intelligence & Machine Learning", "Mukesh Bathre", "mukesh.bathre@gcek.ac.in", "Theory", "302 Block-II", 3),
            ("HSHS3003", "Professional Ethics", "Pritam Das", "pritam.das@gcek.ac.in", "Theory", "302 Block-II", 3),
            ("MCSM3001", "Environmental Engineering", "Srikanth Kumar Patra", "srikanth.patra@gcek.ac.in", "Theory", "302 Block-II", 3),
            ("CSPS3201", "Seminar on SIRE-I", "Rajesh Kumar Tripathy", "rajesh.tripathy@gcek.ac.in", "Seminar", "Seminar Hall", 1),
            ("CSPC3001-LAB", "TOC Lab", "Liza Rani Behera", "liza.rani@gcek.ac.in", "Lab", "B3 Lab", 2),
            ("CSPC3002-LAB", "OS Lab", "Srikant Kumar Barik", "srikant.barik@gcek.ac.in", "Lab", "B4 Lab", 2),
            ("CSPC2007-LAB", "CN Lab", "Santoshi Sahoo", "santoshi.sahoo@gcek.ac.in", "Lab", "B2 Lab", 2),
        ]
    elif department == "Computer Science and Engineering" and year == "4th Year" and semester == "7th Semester":
        subjects = [
            ("CSPE4002", "Software Project Management", "Sasmita Pani", "sasmita.pani@gcek.ac.in", "Theory", "303 Block-II", 2),
            ("EEPE3005", "Renewable Energy Sources", "Yogesh Kumar Nayak", "yogesh.nayak@gcek.ac.in", "Theory", "303 Block-II", 2),
            ("HSOE4001", "Marketing Management", "Soumitra Das", "soumitra.das@gcek.ac.in", "Theory", "303 Block-II", 2),
            ("PCAC4001", "Applied Data Science", "Rajesh Kumar Tripathy", "rajesh.tripathy@gcek.ac.in", "Theory", "303 Block-II", 2),
            ("CSPS4201", "Seminar on SIRE-II", "Sasmita Pani", "sasmita.pani@gcek.ac.in", "Seminar", "Seminar Hall", 1),
            ("CSPS4202", "Project for Product Development - II", "Rajesh Kumar Tripathy", "rajesh.tripathy@gcek.ac.in", "Project", "Project Lab-02", 1),
            ("CSPE4003", "Cloud Computing", "Sasmita Pani", "sasmita.pani@gcek.ac.in", "Theory", "303 Block-II", 3),
            ("CSPE4004", "Information Security", "Mukesh Bathre", "mukesh.bathre@gcek.ac.in", "Theory", "303 Block-II", 3),
        ]
    elif department == "Mining Engineering" and year == "4th Year" and semester == "7th Semester":
        room = "Room No. 213, Block-III"
        subjects = [
            ("MIPE4001", "Mine Safety Engineering", "Dr. Soumya Ranjan Mallik", "soumyaranjan.mallik@local.invalid", "Theory", room, 3),
            ("EEPE3005", "Renewable Energy Sources", "Dr. Suman Kalyan Das", "suman.kalyan.das@local.invalid", "Theory", room, 3),
            ("HSOE4001", "Marketing Management", "BS&H Department", "bsh.department@local.invalid", "Theory", room, 3),
            ("PCAC4007", "Applied Deep Learning", "Mrs. Sasmita Pani", "sasmita.pani@gcek.ac.in", "Theory", room, 3),
            ("MIPS4201", "Seminar on SIRE - II", "ALL FACULTIES", "all-faculties-mining-4-7@local.invalid", "Seminar", room, 2),
            ("MIPS4202", "Project for Product Development - II", "ALL FACULTIES", "all-faculties-mining-4-7@local.invalid", "Project", room, 2),
        ]
        fixed_meetings = {
            "MIPE4001": [{"day": "MON", "start": 1}, {"day": "TUE", "start": 2}, {"day": "FRI", "start": 1}],
            "EEPE3005": [{"day": "MON", "start": 3}, {"day": "TUE", "start": 1}, {"day": "WED", "start": 2}],
            "HSOE4001": [{"day": "TUE", "start": 3}, {"day": "WED", "start": 3}, {"day": "THU", "start": 2}],
            "PCAC4007": [{"day": "MON", "start": 2}, {"day": "THU", "start": 3}, {"day": "FRI", "start": 2}],
            "MIPS4201": [{"day": "MON", "start": 5}, {"day": "TUE", "start": 5}],
            "MIPS4202": [{"day": "WED", "start": 5}, {"day": "THU", "start": 5}],
        }
    else:
        department_prefix = {
            "Computer Science and Engineering": "CSPC",
            "Mining Engineering": "MN",
            "Electrical Engineering": "EE",
            "Mechanical Engineering": "ME",
            "Civil Engineering": "CE",
        }.get(department, "DEPT")
        curricula = {
            "Computer Science and Engineering": {
                "1st Year": ["Engineering Mathematics", "Engineering Physics", "Engineering Chemistry", "Programming in C", "Basic Electrical Engineering", "Engineering Graphics"],
                "2nd Year": ["Discrete Mathematics", "Data Structures and Algorithms", "Object Oriented Programming", "Digital Logic Design", "Computer Organization", "Software Engineering"],
                "3rd Year": ["Theory of Computation", "Operating Systems", "Computer Networks", "Artificial Intelligence and Machine Learning", "Database Management Systems", "Professional Ethics"],
                "4th Year": ["Software Project Management", "Applied Data Science", "Cloud Computing", "Information Security", "Distributed Systems", "Professional Ethics"],
            },
            "Mining Engineering": {
                "1st Year": ["Engineering Mathematics", "Engineering Physics", "Engineering Chemistry", "Introduction to Mining Engineering", "Engineering Geology", "Mine Surveying"],
                "2nd Year": ["Mining Geology", "Mine Surveying", "Mining Methods", "Rock Mechanics", "Mine Ventilation", "Professional Ethics"],
                "3rd Year": ["Underground Mining", "Surface Mining", "Mine Ventilation and Climate", "Mining Machinery", "Mining Geomechanics", "Professional Ethics"],
                "4th Year": ["Mine Planning and Design", "Mine Economics", "Mine Ventilation and Climate", "Mining Machinery Design", "Mining Geology", "Professional Ethics"],
            },
            "Electrical Engineering": {
                "1st Year": ["Engineering Mathematics", "Engineering Physics", "Engineering Chemistry", "Basic Electrical Engineering", "Electrical Workshop", "Engineering Graphics"],
                "2nd Year": ["Electrical Circuit Analysis", "Electrical Machines I", "Network Theory", "Electrical Measurements", "Electromagnetic Fields", "Professional Ethics"],
                "3rd Year": ["Electrical Machines II", "Power Systems I", "Control Systems", "Power Electronics", "Electrical Drives", "Professional Ethics"],
                "4th Year": ["Power System Protection", "High Voltage Engineering", "Renewable Energy Systems", "Electric Vehicle Technology", "Smart Grid Engineering", "Professional Ethics"],
            },
            "Mechanical Engineering": {
                "1st Year": ["Engineering Mathematics", "Engineering Physics", "Engineering Chemistry", "Engineering Mechanics", "Workshop Technology", "Engineering Graphics"],
                "2nd Year": ["Strength of Materials", "Engineering Thermodynamics", "Fluid Mechanics", "Manufacturing Technology", "Material Science", "Professional Ethics"],
                "3rd Year": ["Heat Transfer", "Machine Design", "Internal Combustion Engines", "Industrial Engineering", "Dynamics of Machinery", "Professional Ethics"],
                "4th Year": ["Refrigeration and Air Conditioning", "Finite Element Methods", "Advanced Manufacturing", "Automobile Engineering", "Operations Research", "Professional Ethics"],
            },
            "Civil Engineering": {
                "1st Year": ["Engineering Mathematics", "Engineering Physics", "Engineering Chemistry", "Engineering Mechanics", "Surveying", "Engineering Graphics"],
                "2nd Year": ["Structural Analysis", "Building Materials", "Fluid Mechanics", "Geotechnical Engineering", "Transportation Engineering", "Professional Ethics"],
                "3rd Year": ["Reinforced Concrete Design", "Hydrology and Water Resources", "Foundation Engineering", "Highway Engineering", "Environmental Engineering", "Professional Ethics"],
                "4th Year": ["Advanced Structural Design", "Construction Planning and Management", "Earthquake Engineering", "Water and Wastewater Engineering", "Bridge Engineering", "Professional Ethics"],
            },
        }
        names = list(curricula.get(department, curricula["Computer Science and Engineering"])[year])
        year_no = int(year[0])
        semester_no = int(re.sub(r"\D", "", semester.split()[0]))
        dataset_tag = f"{department_prefix.lower()}.{year_no}.{semester_no}"
        roman = {1: "I", 2: "II", 3: "III", 4: "IV"}[year_no]
        names[0] = names[0] + (f" {roman}" if names[0] == "Engineering Mathematics" else "")

        # Two instructors are genuinely shared across the five branches for
        # matching year/semester cohorts. Their workload remains within limits.
        shared_math_email = f"shared-mathematics-y{year_no}-s{semester_no}@gcek.ac.in"
        shared_ethics_email = f"shared-ethics-y{year_no}-s{semester_no}@gcek.ac.in"
        teachers = [
            ("Dr. Nandita Rao", shared_math_email),
            ("Dr. Arjun Mohanty", f"{department_prefix.lower()}.faculty.1.y{year_no}.s{semester_no}@gcek.ac.in"),
            ("Dr. Meera Sahu", f"{department_prefix.lower()}.faculty.2.y{year_no}.s{semester_no}@gcek.ac.in"),
            ("Dr. Kiran Mohanty", f"{department_prefix.lower()}.faculty.3.y{year_no}.s{semester_no}@gcek.ac.in"),
            ("Dr. Rahul Pradhan", f"{department_prefix.lower()}.faculty.4.y{year_no}.s{semester_no}@gcek.ac.in"),
            ("Pritam Das", shared_ethics_email),
        ]
        if year_no == 3 and semester_no == 5:
            teachers[5] = ("Pritam Das", "pritam.das@gcek.ac.in")

        inventory = room_inventory or []
        reserved_rooms = {"302 block-ii", "303 block-ii", "room no. 213, block-iii"}
        classrooms = [room for room in inventory if room["room_type"].casefold() in {"classroom", "lecture hall", "seminar room"} and room["capacity"] >= 30 and room["name"].casefold() not in reserved_rooms]
        laboratories = [room for room in inventory if room["room_type"].casefold() in {"lab", "laboratory", "computer lab"} and room["capacity"] >= 30]
        if not classrooms:
            classrooms = [{"name": f"Demo Classroom {i:02d}", "room_type": "Classroom", "capacity": 60} for i in range(1, 33)]
        if not laboratories:
            laboratories = [{"name": f"Demo Laboratory {i:02d}", "room_type": "Laboratory", "capacity": 40} for i in range(1, 4)]
        department_order = ["Computer Science and Engineering", "Civil Engineering", "Electrical Engineering", "Mechanical Engineering", "Mining Engineering"]
        group_ordinal = department_order.index(department) * 8 + semester_no - 1
        theory_rooms = classrooms[:max(1, len(classrooms) * 3 // 4)]
        activity_rooms = classrooms[len(theory_rooms):] or classrooms
        lab_room_index = group_ordinal % len(laboratories)
        subjects = []
        for index, name in enumerate(names, 1):
            teacher_name, email = teachers[index - 1]
            room = theory_rooms[(group_ordinal * 7 + index - 1) % len(theory_rooms)]
            subjects.append((f"{department_prefix}{year_no}{semester_no:02d}{index:02d}", name, teacher_name, email, "Theory", room["name"], 3))
        lab_teacher = ("Dr. Anil Das", f"{department_prefix.lower()}.lab.y{year_no}.s{semester_no}@gcek.ac.in")
        lab_room = laboratories[lab_room_index]
        subjects.extend([
            (f"{department_prefix}{year_no}{semester_no:02d}L1", f"{department} Practical Laboratory", lab_teacher[0], lab_teacher[1], "Lab", lab_room["name"], 1),
            (f"{department_prefix}{year_no}{semester_no:02d}S1", f"{department} Technical Seminar", "Dr. Sasmita Pani", f"{department_prefix.lower()}.seminar.y{year_no}.s{semester_no}@gcek.ac.in", "Seminar", activity_rooms[(group_ordinal * 2) % len(activity_rooms)]["name"], 1),
            (f"{department_prefix}{year_no}{semester_no:02d}P1", f"{department} Design Project", "Dr. Rajesh Tripathy", f"{department_prefix.lower()}.project.y{year_no}.s{semester_no}@gcek.ac.in", "Project", activity_rooms[(group_ordinal * 2 + 1) % len(activity_rooms)]["name"], 1),
        ])
    sample_days = "Monday,Tuesday,Wednesday,Thursday,Friday,Saturday"
    items = []
    for code, name, faculty_name, email, subject_type, assigned_room, weekly_sessions in subjects:
        display_email = email if email.endswith("@gcek.ac.in") else ""
        faculty_id = email if display_email else "Not provided"
        items.append({
            "code": code,
            "name": name,
            "facultyName": faculty_name,
            "email": email,
            "displayEmail": display_email,
            "facultyId": faculty_id,
            "type": subject_type,
            "room": assigned_room,
            "weeklySessions": weekly_sessions,
            "teacherAvailableDays": sample_days,
            **({"fixedSessions": fixed_meetings[code]} if code in fixed_meetings else {}),
        })
    return items


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("CREATE TABLE IF NOT EXISTS generated_timetables (id INTEGER PRIMARY KEY AUTOINCREMENT, department TEXT NOT NULL, year TEXT NOT NULL, semester TEXT NOT NULL, status TEXT NOT NULL, timetable_json TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)")
    conn.execute("CREATE TABLE IF NOT EXISTS sample_subjects (id INTEGER PRIMARY KEY AUTOINCREMENT, department TEXT NOT NULL, year TEXT NOT NULL, semester TEXT NOT NULL, code TEXT NOT NULL, subject_json TEXT NOT NULL, UNIQUE(department, year, semester, code))")
    conn.execute("CREATE TABLE IF NOT EXISTS scheduling_teachers (email TEXT PRIMARY KEY, name TEXT NOT NULL, max_weekly_hours INTEGER NOT NULL DEFAULT 20, available_days TEXT NOT NULL DEFAULT 'Monday,Tuesday,Wednesday,Thursday,Friday,Saturday', status TEXT NOT NULL DEFAULT 'Active')")
    conn.execute("CREATE TABLE IF NOT EXISTS scheduling_rooms (name TEXT PRIMARY KEY, room_type TEXT NOT NULL DEFAULT 'Classroom', capacity INTEGER NOT NULL DEFAULT 30, availability TEXT NOT NULL DEFAULT 'Available')")
    conn.execute("CREATE TABLE IF NOT EXISTS scheduling_subjects (id INTEGER PRIMARY KEY AUTOINCREMENT, department TEXT NOT NULL, year TEXT NOT NULL, semester TEXT NOT NULL, code TEXT NOT NULL, name TEXT NOT NULL, credits INTEGER NOT NULL DEFAULT 3, weekly_sessions INTEGER NOT NULL DEFAULT 3, subject_type TEXT NOT NULL DEFAULT 'Theory', teacher_email TEXT NOT NULL, room_name TEXT NOT NULL, expected_students INTEGER NOT NULL DEFAULT 30, active INTEGER NOT NULL DEFAULT 1, UNIQUE(department, year, semester, code), FOREIGN KEY(teacher_email) REFERENCES scheduling_teachers(email), FOREIGN KEY(room_name) REFERENCES scheduling_rooms(name))")
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _connect_readonly():
    database_uri = f"{DB_PATH.resolve().as_uri()}?mode=ro"
    conn = sqlite3.connect(database_uri, uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def list_subjects():
    records = {}
    authoritative_mining_cohort = MINING_REFERENCE_COHORT
    with _connect_readonly() as conn:
        for row in conn.execute("SELECT department, year, semester, code, subject_json FROM sample_subjects"):
            if (row["department"], row["year"], row["semester"]) == authoritative_mining_cohort:
                continue
            item = json.loads(row["subject_json"])
            item.update(department=row["department"], year=row["year"], semester=row["semester"], credits=item.get("credits", 3), active=True, isSample=True)
            item["weeklySessions"] = item.get("weeklySessions", 3)
            item["teacherName"] = item.get("facultyName", "")
            item["teacherEmail"] = item.get("email", "")
            item["roomType"] = "Laboratory" if item.get("type") == "Lab" else ("Seminar Room" if item.get("type") == "Seminar" else "Classroom")
            item["roomCapacity"] = 100 if item["roomType"] == "Seminar Room" else 40 if item["roomType"] == "Laboratory" else 60
            item["expectedStudents"] = 30
            records[(row["department"], row["year"], row["semester"], row["code"])] = item
        for row in conn.execute("SELECT * FROM scheduling_subjects WHERE active=1"):
            row_cohort = (row["department"], row["year"], row["semester"])
            if row_cohort == authoritative_mining_cohort and row["code"].upper() in MINING_LEGACY_CODES:
                continue
            teacher = conn.execute("SELECT * FROM scheduling_teachers WHERE email=?", (row["teacher_email"],)).fetchone()
            room = conn.execute("SELECT * FROM scheduling_rooms WHERE name=?", (row["room_name"],)).fetchone()
            records[(row["department"], row["year"], row["semester"], row["code"])] = {
                "id": row["id"], "code": row["code"], "name": row["name"], "credits": str(row["credits"]),
                "department": row["department"], "year": row["year"], "semester": row["semester"],
                "weeklySessions": row["weekly_sessions"], "type": row["subject_type"],
                "facultyId": row["teacher_email"], "facultyName": teacher["name"], "teacherName": teacher["name"],
                "email": row["teacher_email"], "teacherEmail": row["teacher_email"], "teacherMaxWeeklyHours": teacher["max_weekly_hours"],
                "teacherAvailableDays": teacher["available_days"], "room": room["name"], "roomType": room["room_type"],
                "roomCapacity": room["capacity"], "expectedStudents": row["expected_students"], "active": True, "isSample": False,
            }
    for subject in _sample_catalog(*authoritative_mining_cohort):
        subject_type = subject["type"]
        item = {
            **subject,
            "department": authoritative_mining_cohort[0],
            "year": authoritative_mining_cohort[1],
            "semester": authoritative_mining_cohort[2],
            "credits": "6" if subject_type in {"Seminar", "Project"} else "3",
            "active": True,
            "isSample": True,
            "teacherName": subject["facultyName"],
            "teacherEmail": subject.get("displayEmail", ""),
            "roomType": "Seminar Room" if subject_type == "Seminar" else "Classroom",
            "roomCapacity": 100 if subject_type in {"Seminar", "Project"} else 60,
            "expectedStudents": 30,
        }
        records.setdefault((*authoritative_mining_cohort, subject["code"]), item)
    return list(records.values())


def _merge_sample_subjects(samples, saved_subjects):
    """Keep stored subjects and replace matching examples without duplicating them."""
    merged = list(samples)
    for saved in saved_subjects:
        match_index = next((i for i, item in enumerate(merged) if item["code"].casefold() == saved["code"].casefold()), None)
        if match_index is None:
            saved_tokens = set(re.findall(r"[a-z0-9]+", saved["name"].casefold()))
            aliases = {"equipment": "machinery", "geology": "geology", "mine": "mining"}
            saved_tokens = {aliases.get(token, token) for token in saved_tokens}
            for index, item in enumerate(merged):
                item_tokens = {aliases.get(token, token) for token in re.findall(r"[a-z0-9]+", item["name"].casefold())}
                if saved_tokens and len(saved_tokens & item_tokens) / min(len(saved_tokens), len(item_tokens)) >= 0.67:
                    match_index = index
                    break
        if match_index is None:
            merged.append(saved)
        else:
            merged[match_index] = saved
    return merged


def _merge_subjects_by_code(samples, saved_subjects):
    """Use saved Subject-section entries for matching codes and append new ones."""
    saved_by_code = {item["code"].casefold(): item for item in saved_subjects}
    merged = []
    for sample in samples:
        saved = saved_by_code.pop(sample["code"].casefold(), None)
        if saved is None:
            merged.append(sample)
            continue
        if sample.get("fixedSessions") and saved.get("type") == sample.get("type") and saved.get("weeklySessions") == sample.get("weeklySessions"):
            saved["fixedSessions"] = sample["fixedSessions"]
        merged.append(saved)
    merged.extend(saved_by_code.values())
    return merged


def save_subject(data, subject_id=None):
    department, year, semester = (str(data.get(key, "")).strip() for key in ("department", "year", "semester"))
    code = str(data.get("code", "")).strip().upper()
    name = str(data.get("name", "")).strip()
    teacher_name = str(data.get("teacherName", "")).strip()
    teacher_email = str(data.get("teacherEmail", "")).strip().lower()
    room_name = str(data.get("room", "")).strip()
    if not all((department, year, semester, code, name, teacher_name, teacher_email, room_name)):
        raise ValueError("Subject, branch, year, semester, faculty name/email, and room are required.")
    try:
        credits = int(data.get("credits", 3))
        weekly = int(data.get("weeklySessions", 3))
        max_hours = int(data.get("teacherMaxWeeklyHours", 20))
        capacity = int(data.get("roomCapacity", 30))
        expected = int(data.get("expectedStudents", 30))
    except (TypeError, ValueError):
        raise ValueError("Credits, weekly sessions, hours, and capacities must be whole numbers.")
    if not (1 <= credits <= 10 and 1 <= weekly <= 10 and 1 <= max_hours <= 60 and 1 <= capacity <= 1000 and 1 <= expected <= 1000):
        raise ValueError("Credits, sessions, workload, and capacities are outside the allowed range.")
    available_days = str(data.get("teacherAvailableDays", "Monday,Tuesday,Wednesday,Thursday,Friday,Saturday"))
    subject_type = str(data.get("type", "Theory"))
    room_type = str(data.get("roomType", "Classroom"))
    with _connect() as conn:
        conn.execute("INSERT INTO scheduling_teachers(email,name,max_weekly_hours,available_days,status) VALUES(?,?,?,?, 'Active') ON CONFLICT(email) DO UPDATE SET name=excluded.name,max_weekly_hours=excluded.max_weekly_hours,available_days=excluded.available_days,status='Active'", (teacher_email, teacher_name, max_hours, available_days))
        conn.execute("INSERT INTO scheduling_rooms(name,room_type,capacity,availability) VALUES(?,?,?,'Available') ON CONFLICT(name) DO UPDATE SET room_type=excluded.room_type,capacity=excluded.capacity,availability='Available'", (room_name, room_type, capacity))
        if subject_id:
            cursor = conn.execute("UPDATE scheduling_subjects SET department=?,year=?,semester=?,name=?,credits=?,weekly_sessions=?,subject_type=?,teacher_email=?,room_name=?,expected_students=?,active=1 WHERE id=?", (department, year, semester, name, credits, weekly, subject_type, teacher_email, room_name, expected, subject_id))
            if not cursor.rowcount:
                raise ValueError("Subject record not found.")
            record_id = subject_id
        else:
            cursor = conn.execute("INSERT INTO scheduling_subjects(department,year,semester,code,name,credits,weekly_sessions,subject_type,teacher_email,room_name,expected_students) VALUES(?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(department,year,semester,code) DO UPDATE SET name=excluded.name,credits=excluded.credits,weekly_sessions=excluded.weekly_sessions,subject_type=excluded.subject_type,teacher_email=excluded.teacher_email,room_name=excluded.room_name,expected_students=excluded.expected_students,active=1", (department, year, semester, code, name, credits, weekly, subject_type, teacher_email, room_name, expected))
            record_id = conn.execute("SELECT id FROM scheduling_subjects WHERE department=? AND year=? AND semester=? AND code=?", (department, year, semester, code)).fetchone()["id"]
    return next(item for item in list_subjects() if item.get("id") == record_id)


def archive_subject(subject_id):
    with _connect() as conn:
        cursor = conn.execute("UPDATE scheduling_subjects SET active=0 WHERE id=?", (subject_id,))
        return cursor.rowcount > 0


def catalog(department, year, semester):
    result = []
    with _connect() as conn:
        rows = conn.execute("SELECT * FROM scheduling_subjects WHERE department=? AND year=? AND semester=? AND active=1 ORDER BY code", (department, year, semester)).fetchall()
        room_inventory = [dict(name=row["name"], room_type=row["room_type"], capacity=row["capacity"]) for row in conn.execute("SELECT name,room_type,capacity FROM scheduling_rooms WHERE availability='Available' ORDER BY name")]
        if rows:
            for row in rows:
                teacher = conn.execute("SELECT * FROM scheduling_teachers WHERE email=? AND status='Active'", (row["teacher_email"],)).fetchone()
                room = conn.execute("SELECT * FROM scheduling_rooms WHERE name=? AND availability='Available'", (row["room_name"],)).fetchone()
                if teacher and room:
                    result.append({"code": row["code"], "name": row["name"], "facultyName": teacher["name"], "email": teacher["email"], "facultyId": teacher["email"], "teacherMaxWeeklyHours": teacher["max_weekly_hours"], "teacherAvailableDays": teacher["available_days"], "type": row["subject_type"], "room": room["name"], "roomType": room["room_type"], "roomCapacity": room["capacity"], "expectedStudents": row["expected_students"], "weeklySessions": row["weekly_sessions"], "credits": row["credits"]})
    if department == "Mining Engineering" and year == "4th Year" and semester == "7th Semester":
        # Use the image timetable as defaults, but pass current Subject-section
        # records to the generator and retain newly added subjects.
        current_saved = [item for item in result if item["code"].upper() not in MINING_LEGACY_CODES]
        items = _merge_subjects_by_code(_sample_catalog(department, year, semester, room_inventory), current_saved)
    elif rows and department != "Computer Science and Engineering":
        items = _merge_sample_subjects(_sample_catalog(department, year, semester, room_inventory), result)
    elif rows:
        overrides = {item["code"]: item for item in result}
        items = [overrides.pop(item["code"], item) for item in _sample_catalog(department, year, semester, room_inventory)]
        items.extend(overrides.values())
    else:
        items = _sample_catalog(department, year, semester, room_inventory)
    for item in items:
        item.setdefault("teacherMaxWeeklyHours", 18)
        item.setdefault("teacherAvailableDays", "Monday,Tuesday,Wednesday,Thursday,Friday,Saturday")
        item.setdefault("roomType", "Laboratory" if item["type"] == "Lab" else "Seminar Room" if item["type"] == "Seminar" else "Classroom")
        item.setdefault("roomCapacity", 100 if item["type"] == "Seminar" else 40 if item["type"] == "Lab" else 60)
        item.setdefault("expectedStudents", 30)
    return items


def seed_all_catalogs():
    """Persist supplied CSE curricula and demo records for every UI selection."""
    departments = [
        "Computer Science and Engineering", "Mining Engineering",
        "Electrical Engineering", "Mechanical Engineering", "Civil Engineering",
    ]
    semester_by_year = {
        "1st Year": ("1st Semester", "2nd Semester"),
        "2nd Year": ("3rd Semester", "4th Semester"),
        "3rd Year": ("5th Semester", "6th Semester"),
        "4th Year": ("7th Semester", "8th Semester"),
    }
    records = []
    teacher_rows, room_rows = {}, {}
    with _connect() as conn:
        room_inventory = [dict(name=row["name"], room_type=row["room_type"], capacity=row["capacity"]) for row in conn.execute("SELECT name,room_type,capacity FROM scheduling_rooms WHERE availability='Available' ORDER BY name")]
    for department in departments:
        for year, semesters in semester_by_year.items():
            for semester in semesters:
                for subject in _sample_catalog(department, year, semester, room_inventory):
                    subject.update(
                        teacherMaxWeeklyHours=18,
                        teacherAvailableDays="Monday,Tuesday,Wednesday,Thursday,Friday,Saturday",
                        roomType="Laboratory" if subject["type"] == "Lab" else "Seminar Room" if subject["type"] == "Seminar" else "Classroom",
                        roomCapacity=100 if subject["type"] == "Seminar" else 40 if subject["type"] == "Lab" else 60,
                        expectedStudents=30,
                    )
                    records.append((department, year, semester, subject["code"], json.dumps(subject)))
                    teacher_rows[subject["email"].casefold()] = (subject["email"].casefold(), subject["facultyName"], int(subject.get("teacherMaxWeeklyHours", 18)), subject.get("teacherAvailableDays", "Monday,Tuesday,Wednesday,Thursday,Friday,Saturday"))
                    room_rows[subject["room"].casefold()] = (subject["room"], subject.get("roomType", "Classroom"), int(subject.get("roomCapacity", 60)))
    with _connect() as conn:
        conn.executemany(
            "INSERT OR IGNORE INTO sample_subjects (department, year, semester, code, subject_json) VALUES (?, ?, ?, ?, ?)",
            records,
        )
        conn.executemany("INSERT OR IGNORE INTO scheduling_teachers(email,name,max_weekly_hours,available_days) VALUES(?,?,?,?)", teacher_rows.values())
        conn.executemany("INSERT OR IGNORE INTO scheduling_rooms(name,room_type,capacity) VALUES(?,?,?)", room_rows.values())
    return len(records)


def _published_reservations(exclude_key, extra_schedules=(), ignored_draft_keys=()):
    teacher_busy, room_busy = set(), set()
    cohort_teacher_load = {}
    with _connect() as conn:
        rows = conn.execute("SELECT department,year,semester,status,timetable_json FROM generated_timetables WHERE status IN ('Published','Draft') ORDER BY id DESC").fetchall()
    schedules = [json.loads(row["timetable_json"]) for row in rows]
    row_metadata = [(row["department"], row["year"], row["semester"], row["status"]) for row in rows]
    schedules.extend(extra_schedules)
    row_metadata.extend((schedule["department"], schedule["year"], schedule["semester"], "Pending") for schedule in extra_schedules)
    ignored_draft_keys = set(ignored_draft_keys)
    for schedule, metadata in zip(schedules, row_metadata):
        key = (schedule["department"], schedule["year"], schedule["semester"])
        if key == exclude_key or (metadata[3] == "Draft" and key in ignored_draft_keys):
            continue
        subjects = {item["code"]: item for item in schedule.get("subjectDetails", [])}
        schedule_teacher_load = {}
        for session in schedule.get("sessions", []):
            subject = subjects.get(session["code"], {})
            email = subject.get("email", "").casefold()
            room = subject.get("room", "").casefold()
            for slot in range(session["start"], session["start"] + session["span"]):
                if email: teacher_busy.add((email, session["day"], slot))
                if room: room_busy.add((room, session["day"], slot))
            if email: schedule_teacher_load[email] = schedule_teacher_load.get(email, 0) + session["span"]
        for email, hours in schedule_teacher_load.items():
            cohort_teacher_load[(key, email)] = max(cohort_teacher_load.get((key, email), 0), hours)
    teacher_load = {}
    for (_, email), hours in cohort_teacher_load.items():
        teacher_load[email] = teacher_load.get(email, 0) + hours
    return teacher_busy, room_busy, teacher_load


def _build_days(sessions, tutorial_saturday=False):
    days = []
    for day in DAYS:
        cells = {slot: {"start": slot, "span": 1, "label": "X", "empty": True} for slot in SLOTS}
        for session in sessions:
            if session["day"] == day:
                cells[session["start"]] = {"start": session["start"], "span": session["span"], "code": session["code"]}
                for slot in range(session["start"] + 1, session["start"] + session["span"]):
                    cells[slot] = {"start": slot, "span": 0, "label": "", "empty": True}
        if day == "SAT" and tutorial_saturday:
            cells[0] = {"start": 0, "span": 4, "label": "Tutorial/Extra Classes/Academic Activities", "empty": False}
            for slot in (1, 2, 3):
                cells[slot] = {"start": slot, "span": 0, "label": "", "empty": True}
        days.append({"day": day, "beforeLunch": [cells[s] for s in range(4) if cells[s]["span"] > 0], "afterLunch": [cells[s] for s in (5, 6, 7) if cells[s]["span"] > 0]})
    return days


def generate(department, year, semester, reserve_schedules=(), ignored_draft_keys=(), placement_seed=0):
    subjects = catalog(department, year, semester)
    # Place the most restricted, longest sessions first. Among valid placements,
    # prefer full-day coverage, compact blocks, balanced daily loads and early starts.
    occupied_teachers, occupied_rooms, teacher_load = _published_reservations((department, year, semester), reserve_schedules, ignored_draft_keys)
    occupied_cohort = set()
    teacher_max_hours, teacher_days = {}, {}
    for subject in subjects:
        email = subject["email"].casefold()
        maximum = int(subject.get("teacherMaxWeeklyHours", 18))
        available = {day.strip().casefold() for day in subject.get("teacherAvailableDays", "Monday,Tuesday,Wednesday,Thursday,Friday,Saturday").split(",") if day.strip()}
        teacher_max_hours[email] = min(teacher_max_hours.get(email, maximum), maximum)
        teacher_days[email] = teacher_days[email] & available if email in teacher_days else available
    requests = [(subject, idx) for subject in subjects for idx in range(subject["weeklySessions"])]

    def session_span(subject):
        return 2 if subject["type"] == "Lab" else (3 if subject["type"] in ("Seminar", "Project") else 1)

    total_periods = sum(session_span(subject) for subject, _ in requests)
    # Spread each curriculum in proportion to the available periods per day.
    # Saturday has fewer periods, so its target load is intentionally lighter.
    target_days = min(len(DAYS), max(1, (total_periods + 5) // 6))
    target_capacity = sum(len(DAY_SLOTS[day]) for day in DAYS[:target_days])
    target_daily_load = {
        day: total_periods * len(DAY_SLOTS[day]) / target_capacity if day in DAYS[:target_days] else 0
        for day in DAYS
    }
    requests.sort(key=lambda pair: (
        -int(bool(pair[0].get("fixedSessions"))),
        -session_span(pair[0]),
        len(teacher_days.get(pair[0]["email"].casefold(), set())),
        -pair[0]["weeklySessions"],
        pair[0]["code"],
        pair[1],
    ))

    sessions = []
    day_slots = {day: set() for day in DAYS}
    active_days = set()
    same_subject_day = {}
    teacher_day_load = {}
    for subject, occurrence in requests:
        span = session_span(subject)
        teacher_key = subject["email"].casefold()
        room_key = subject["room"].casefold()
        room_type = subject.get("roomType", "Classroom").casefold()
        compatible_room = subject.get("expectedStudents", 0) <= subject.get("roomCapacity", 9999)
        compatible_room = compatible_room and (subject["type"] != "Lab" or room_type in {"laboratory", "lab", "computer lab"})
        compatible_room = compatible_room and (subject["type"] != "Seminar" or room_type in {"seminar room", "lecture hall", "classroom"})
        fixed_sessions = subject.get("fixedSessions") or []
        if fixed_sessions:
            fixed = fixed_sessions[occurrence] if occurrence < len(fixed_sessions) else {}
            fixed_day, fixed_start = fixed.get("day"), fixed.get("start")
            candidates = [(fixed_day, fixed_start)] if (
                compatible_room
                and fixed_day in DAY_SLOTS
                and fixed_start in DAY_SLOTS[fixed_day]
                and DAY_NAMES[fixed_day].casefold() in teacher_days.get(teacher_key, set())
                and all(slot in DAY_SLOTS[fixed_day] for slot in range(fixed_start, fixed_start + span))
            ) else []
        else:
            candidates = [
                (day, start)
                for day in DAYS
                if DAY_NAMES[day].casefold() in teacher_days.get(teacher_key, set())
                for start in DAY_SLOTS[day]
                if all(slot in DAY_SLOTS[day] for slot in range(start, start + span))
            ] if compatible_room else []
        valid = []
        for day, start in candidates:
            slot_keys = [(day, s) for s in range(start, start + span)]
            if teacher_load.get(teacher_key, 0) + span > teacher_max_hours.get(teacher_key, 18):
                continue
            if any((teacher_key, d, s) in occupied_teachers or (room_key, d, s) in occupied_rooms or (d, s) in occupied_cohort for d, s in slot_keys):
                continue
            projected_slots = day_slots[day] | {slot for _, slot in slot_keys}
            positions = [SLOT_ORDER[slot] for slot in projected_slots]
            gaps = max(positions) - min(positions) + 1 - len(positions)
            opens_day = day not in active_days and len(active_days) < target_days
            projected_load = len(projected_slots)
            tie_break = (
                sum(ord(ch) for ch in subject["code"]) * 17
                + occurrence * 23
                + placement_seed * 31
                + DAYS.index(day) * 7
                + SLOT_ORDER[start] * 13
            ) % 97
            score = (
                gaps,
                same_subject_day.get((subject["code"], day), 0),
                (projected_load - target_daily_load[day]) ** 2,
                0 if opens_day else 1,
                teacher_day_load.get((teacher_key, day), 0),
                min(positions),
                max(positions),
                tie_break,
                DAYS.index(day),
                start,
            )
            valid.append((score, day, start, slot_keys))
        if not valid:
            reason = "room capacity/type" if not compatible_room else "teacher availability, workload, or teacher/room timetable conflict"
            raise ValueError(
                f"Could not schedule {subject['code']} ({subject['name']}) for {department}, {year}, {semester}: "
                f"{reason}; faculty {teacher_key} has {teacher_load.get(teacher_key, 0)}/{teacher_max_hours.get(teacher_key, 18)} periods, "
                f"assigned room {room_key}, and {len(candidates)} candidate starts."
            )
        _, day, start, slot_keys = min(valid, key=lambda item: item[0])
        for d, slot in slot_keys:
            occupied_teachers.add((teacher_key, d, slot))
            occupied_rooms.add((room_key, d, slot))
            occupied_cohort.add((d, slot))
            day_slots[d].add(slot)
        active_days.add(day)
        teacher_load[teacher_key] = teacher_load.get(teacher_key, 0) + span
        teacher_day_load[(teacher_key, day)] = teacher_day_load.get((teacher_key, day), 0) + span
        same_subject_day[(subject["code"], day)] = same_subject_day.get((subject["code"], day), 0) + 1
        sessions.append({"day": day, "start": start, "span": span, "code": subject["code"], "occurrence": occurrence})
    sessions.sort(key=lambda item: (DAYS.index(item["day"]), item["start"]))
    tutorial_saturday = (department, year, semester) == ("Mining Engineering", "4th Year", "7th Semester")
    days = _build_days(sessions, tutorial_saturday)
    rooms = {subject.get("room") for subject in subjects}
    common_room = next(iter(rooms)) if len(rooms) == 1 else "See subject room"
    mining_time_slots = [
        "9:00-9:55", "10:00-10:55", "11:00-11:55", "12:00-12:55",
        "1:00-2:30", "2:30-3:25", "3:25-4:20", "4:20-5:00",
    ]
    return {"department": department, "year": year, "semester": semester, "academicYear": "2026-27", "commonRoom": common_room, "subjectDetails": subjects, "days": days, "sessions": sessions, **({"timeSlots": mining_time_slots} if tutorial_saturday else {}), "source": "AI constraint scheduler"}


def save_draft(schedule):
    key = (schedule["department"], schedule["year"], schedule["semester"])
    with _connect() as conn:
        cursor = conn.execute("INSERT INTO generated_timetables (department, year, semester, status, timetable_json) VALUES (?, ?, ?, 'Draft', ?)", (*key, json.dumps(schedule)))
        return cursor.lastrowid


def _compact_batch_schedules(schedules, replaced_keys):
    """Move sessions into holes when a globally conflict-free block can be kept."""
    teacher_counts, room_counts = {}, {}
    cohort_slots = {}

    def reserve(schedule, session, amount):
        subject = next(item for item in schedule["subjectDetails"] if item["code"] == session["code"])
        teacher = subject.get("email", "").casefold()
        room = subject.get("room", "").casefold()
        cohort = (schedule["department"], schedule["year"], schedule["semester"])
        local_slots = cohort_slots.setdefault(cohort, set())
        for slot in range(session["start"], session["start"] + session["span"]):
            key = (session["day"], slot)
            if amount > 0:
                local_slots.add(key)
                if teacher: teacher_counts[(teacher, *key)] = teacher_counts.get((teacher, *key), 0) + 1
                if room: room_counts[(room, *key)] = room_counts.get((room, *key), 0) + 1
            else:
                local_slots.discard(key)
                if teacher:
                    resource = (teacher, *key)
                    if teacher_counts.get(resource, 0) <= 1: teacher_counts.pop(resource, None)
                    else: teacher_counts[resource] -= 1
                if room:
                    resource = (room, *key)
                    if room_counts.get(resource, 0) <= 1: room_counts.pop(resource, None)
                    else: room_counts[resource] -= 1

    for schedule in schedules:
        for session in schedule["sessions"]:
            reserve(schedule, session, 1)

    def schedule_quality(schedule):
        daily = {day: set() for day in DAYS}
        for session in schedule["sessions"]:
            daily[session["day"]].update(SLOT_ORDER[slot] for slot in range(session["start"], session["start"] + session["span"]))
        periods = sum(len(slots) for slots in daily.values())
        target_days = min(len(DAYS), max(1, (periods + 5) // 6))
        capacity = sum(len(DAY_SLOTS[day]) for day in DAYS[:target_days])
        gaps = sum(max(slots) - min(slots) + 1 - len(slots) for slots in daily.values() if slots)
        balance = sum((len(daily[day]) - periods * len(DAY_SLOTS[day]) / capacity) ** 2 if day in DAYS[:target_days] else len(daily[day]) ** 2 for day in DAYS)
        early = sum(min(slots) for slots in daily.values() if slots)
        return gaps, balance, early

    for schedule in schedules:
        cohort = (schedule["department"], schedule["year"], schedule["semester"])
        subjects = {item["code"]: item for item in schedule["subjectDetails"]}
        published_teacher, published_room, _ = _published_reservations(cohort, ignored_draft_keys=replaced_keys)
        for _ in range(12):
            before = schedule_quality(schedule)
            if before == (0, 0, 0):
                break
            improved = False
            for session in schedule["sessions"]:
                subject = subjects[session["code"]]
                if subject.get("fixedSessions"):
                    continue
                teacher = subject.get("email", "").casefold()
                room = subject.get("room", "").casefold()
                available_days = {day.strip().casefold() for day in subject.get("teacherAvailableDays", ",".join(DAY_NAMES.values())).split(",") if day.strip()}
                old_day, old_start = session["day"], session["start"]
                reserve(schedule, session, -1)
                best = None
                for day in DAYS:
                    if DAY_NAMES[day].casefold() not in available_days:
                        continue
                    for start in DAY_SLOTS[day]:
                        slots = range(start, start + session["span"])
                        if not all(slot in DAY_SLOTS[day] for slot in slots):
                            continue
                        keys = [(day, slot) for slot in slots]
                        if any((day, slot) in cohort_slots[cohort] for day, slot in keys):
                            continue
                        if any((teacher, day, slot) in published_teacher or teacher_counts.get((teacher, day, slot), 0) for day, slot in keys):
                            continue
                        if any((room, day, slot) in published_room or room_counts.get((room, day, slot), 0) for day, slot in keys):
                            continue
                        session["day"], session["start"] = day, start
                        candidate_quality = schedule_quality(schedule)
                        if candidate_quality < before:
                            candidate_score = (*candidate_quality, DAYS.index(day), start)
                            if best is None or candidate_score < best[0]:
                                best = (candidate_score, day, start)
                    
                if best:
                    session["day"], session["start"] = best[1], best[2]
                    reserve(schedule, session, 1)
                    improved = True
                    break
                session["day"], session["start"] = old_day, old_start
                reserve(schedule, session, 1)
            if not improved:
                break
        schedule["sessions"].sort(key=lambda item: (DAYS.index(item["day"]), item["start"]))
        tutorial_saturday = (cohort == ("Mining Engineering", "4th Year", "7th Semester"))
        schedule["days"] = _build_days(schedule["sessions"], tutorial_saturday)
    return schedules


def generate_all():
    with _connect() as conn:
        datasets = conn.execute("SELECT DISTINCT department,year,semester FROM sample_subjects UNION SELECT DISTINCT department,year,semester FROM scheduling_subjects WHERE active=1 ORDER BY department,year,semester").fetchall()
    dataset_keys = {(row["department"], row["year"], row["semester"]) for row in datasets}
    default_semesters = {
        "1st Year": ("1st Semester", "2nd Semester"),
        "2nd Year": ("3rd Semester", "4th Semester"),
        "3rd Year": ("5th Semester", "6th Semester"),
        "4th Year": ("7th Semester", "8th Semester"),
    }
    for department in ("Computer Science and Engineering", "Mining Engineering", "Electrical Engineering", "Mechanical Engineering", "Civil Engineering"):
        for year, semesters in default_semesters.items():
            dataset_keys.update((department, year, semester) for semester in semesters)
    datasets = [dict(department=department, year=year, semester=semester) for department, year, semester in sorted(dataset_keys)]
    pending, ids = [], []
    last_error = None
    best_quality = None
    best_schedules = None
    # Greedy constraint search can hit a dead end or leave avoidable holes.
    # Compare deterministic restarts and keep the densest feasible complete set.
    for placement_seed in range(12):
        pending = []
        try:
            preferred_key = ("Mining Engineering", "4th Year", "7th Semester")
            fixed_datasets = [row for row in datasets if (row["department"], row["year"], row["semester"]) == preferred_key]
            flexible_datasets = [row for row in datasets if (row["department"], row["year"], row["semester"]) != preferred_key]
            offset = placement_seed % len(flexible_datasets) if flexible_datasets else 0
            ordered_datasets = fixed_datasets + flexible_datasets[offset:] + flexible_datasets[:offset]
            for row in ordered_datasets:
                schedule = generate(row["department"], row["year"], row["semester"], pending, dataset_keys, placement_seed)
                pending.append(schedule)
        except ValueError as error:
            last_error = error
            continue
        pending = _compact_batch_schedules(pending, dataset_keys)
        total_gaps = 0
        balance_cost = 0
        early_start_cost = 0
        for schedule in pending:
            daily_slots = {day: set() for day in DAYS}
            for session in schedule["sessions"]:
                daily_slots[session["day"]].update(range(session["start"], session["start"] + session["span"]))
            total_periods = sum(len(slots) for slots in daily_slots.values())
            target_days = min(len(DAYS), max(1, (total_periods + 5) // 6))
            target_capacity = sum(len(DAY_SLOTS[day]) for day in DAYS[:target_days])
            for day in DAYS:
                positions = sorted(SLOT_ORDER[slot] for slot in daily_slots[day])
                target = total_periods * len(DAY_SLOTS[day]) / target_capacity if day in DAYS[:target_days] else 0
                if positions:
                    total_gaps += positions[-1] - positions[0] + 1 - len(positions)
                    early_start_cost += positions[0]
                balance_cost += (len(positions) - target) ** 2
        quality = (total_gaps, balance_cost, early_start_cost)
        if best_quality is None or quality < best_quality:
            best_quality = quality
            best_schedules = pending
        if total_gaps == 0:
            break
    if best_schedules is not None:
        pending = best_schedules
    else:
        raise ValueError(f"Could not find a conflict-free timetable set for all branches and years after 12 optimization passes. Last issue: {last_error}")
    # Save all drafts in one SQLite transaction; a generation error above leaves no partial batch.
    with _connect() as conn:
        for schedule in pending:
            key = (schedule["department"], schedule["year"], schedule["semester"])
            cursor = conn.execute("INSERT INTO generated_timetables (department, year, semester, status, timetable_json) VALUES (?, ?, ?, 'Draft', ?)", (*key, json.dumps(schedule)))
            ids.append(cursor.lastrowid)
    return [{"id": row_id, **schedule} for row_id, schedule in zip(ids, pending)]


def load_schedule(department, year, semester):
    with _connect() as conn:
        row = conn.execute("SELECT id,status,timetable_json FROM generated_timetables WHERE department=? AND year=? AND semester=? AND status IN ('Draft','Published') ORDER BY id DESC LIMIT 1", (department, year, semester)).fetchone()
    if (department, year, semester) == MINING_REFERENCE_COHORT:
        current_subjects = catalog(department, year, semester)
        saved_schedule = json.loads(row["timetable_json"]) if row else None
        saved_subjects = {item.get("code"): item for item in (saved_schedule or {}).get("subjectDetails", [])}
        current_subject_map = {item["code"]: item for item in current_subjects}
        same_catalog = set(saved_subjects) == set(current_subject_map)
        if same_catalog:
            for code, current in current_subject_map.items():
                saved = saved_subjects[code]
                if any(saved.get(field) != current.get(field) for field in ("name", "facultyName", "email", "room", "type", "weeklySessions")):
                    same_catalog = False
                    break
        if not same_catalog:
            preview = generate(department, year, semester)
            preview.update(status="Preview", previewOnly=True)
            return preview
    if not row:
        return None
    return {**json.loads(row["timetable_json"]), "recordId": row["id"], "status": row["status"]}


def save(schedule):
    key = (schedule.get("department"), schedule.get("year"), schedule.get("semester"))
    teachers_busy, rooms_busy, teacher_load = _published_reservations(key)
    details = {subject["code"]: subject for subject in schedule.get("subjectDetails", [])}
    local_busy, local_teacher, local_room = set(), set(), set()
    for item in schedule.get("sessions", []):
        subject = details.get(item.get("code"))
        if not subject:
            raise ValueError(f"Unknown subject {item.get('code')} in this timetable.")
        email = subject.get("email", "").casefold()
        room = subject.get("room", "").casefold()
        for slot in range(item["start"], item["start"] + item["span"]):
            teacher_key = (email, item["day"], slot)
            room_key = (room, item["day"], slot)
            cohort_key = (item["day"], slot)
            if teacher_key in teachers_busy or teacher_key in local_teacher:
                raise ValueError(f"Teacher conflict for {subject['facultyName']} on {item['day']}.")
            if room_key in rooms_busy or room_key in local_room:
                raise ValueError(f"Room conflict for {room} on {item['day']}.")
            if cohort_key in local_busy:
                raise ValueError(f"Class conflict on {item['day']}.")
            local_teacher.add(teacher_key); local_room.add(room_key); local_busy.add(cohort_key)
        teacher_load[email] = teacher_load.get(email, 0) + item["span"]
        if teacher_load[email] > int(subject.get("teacherMaxWeeklyHours", 18)):
            raise ValueError(f"Weekly workload limit exceeded for {subject['facultyName']}.")
    with _connect() as conn:
        cursor = conn.execute("INSERT INTO generated_timetables (department, year, semester, status, timetable_json) VALUES (?, ?, ?, 'Published', ?)", (*key, json.dumps(schedule)))
        return cursor.lastrowid


def published_for_user(user):
    """Map the newest saved fixtures to the existing dashboard row format."""
    with _connect() as conn:
        rows = conn.execute("SELECT id, timetable_json FROM generated_timetables WHERE status = 'Published' ORDER BY created_at DESC, id DESC").fetchall()
    role = "admin" if (user.is_staff or user.is_superuser) else ""
    try:
        role = user.smarttime_profile.role
        profile = user.smarttime_profile
    except Exception:
        profile = None
    faculty_name = " ".join((user.get_full_name() or user.username).split()).casefold()
    unique_faculty_name = False
    if role == "faculty" and faculty_name:
        from .models import UserProfile

        matching_profiles = [
            item.user_id
            for item in UserProfile.objects.filter(role="faculty").select_related("user")
            if " ".join((item.user.get_full_name() or item.user.username).split()).casefold() == faculty_name
        ]
        unique_faculty_name = matching_profiles == [user.pk]
    days = {"MON": "Monday", "TUE": "Tuesday", "WED": "Wednesday", "THU": "Thursday", "FRI": "Friday", "SAT": "Saturday"}
    starts = {0: "09:00", 1: "10:00", 2: "11:05", 3: "12:05", 5: "14:30", 6: "15:20", 7: "16:10"}
    ends = {0: "09:55", 1: "10:55", 2: "12:00", 3: "13:00", 5: "15:20", 6: "16:10", 7: "17:00"}
    result, seen = [], set()
    for row_id, raw in rows:
        schedule = json.loads(raw)
        key = (schedule["department"], schedule["year"], schedule["semester"])
        if key in seen:
            continue
        seen.add(key)
        if role == "faculty":
            matching = []
            for item in schedule["sessions"]:
                subject = next((subject for subject in schedule["subjectDetails"] if subject["code"] == item["code"]), {})
                email_match = subject.get("email", "").strip().casefold() == user.email.strip().casefold()
                name_match = unique_faculty_name and " ".join(subject.get("facultyName", "").split()).casefold() == faculty_name
                if email_match or name_match:
                    matching.append(item)
        elif role == "student" and profile:
            profile_year = (profile.year or "").casefold()
            profile_course = (profile.course or "").casefold()
            department_name = schedule["department"].casefold()
            aliases = {
                "computer science and engineering": {"cse", "cs", "computer science"},
                "mining engineering": {"mining", "mine"},
                "electrical engineering": {"ee", "electrical"},
                "mechanical engineering": {"mech", "mechanical"},
                "civil engineering": {"ce", "civil"},
            }
            alias_match = any(profile_course in codes and branch in department_name for branch, codes in aliases.items())
            course_match = not profile_course or profile_course in department_name or department_name in profile_course or alias_match
            matching = schedule["sessions"] if course_match and (not profile_year or profile_year in schedule["year"].casefold() or schedule["year"].casefold() in profile_year) else []
        elif role == "admin":
            matching = schedule["sessions"]
        else:
            matching = []
        catalog_by_code = {subject["code"]: subject for subject in schedule["subjectDetails"]}
        for item in matching:
            subject = catalog_by_code[item["code"]]
            final_slot = item["start"] + item["span"] - 1
            result.append({"id": f"isolated-{row_id}-{item['code']}-{item['day']}-{item['start']}", "day": days[item["day"]], "start_time": starts[item["start"]], "end_time": ends[final_slot], "subject_name": subject["name"], "session_title": subject["name"], "teacher_name": subject["facultyName"], "room_number": subject["room"], "semester_name": schedule["semester"], "year": schedule["year"], "batch_section": ""})
    return result

