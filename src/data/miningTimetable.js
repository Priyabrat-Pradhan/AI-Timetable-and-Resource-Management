const department = "Mining Engineering";
const year = "4th Year";
const semester = "7th Semester";
const room = "Room No. 213, Block-III";

const teachers = {
  mse: { name: "Dr. Soumya Ranjan Mallik", key: "soumyaranjan.mallik@mining.local.invalid", displayEmail: "" },
  res: { name: "Dr. Suman Kalyan Das", key: "suman.kalyan.das@mining.local.invalid", displayEmail: "" },
  mm: { name: "BS&H Department", key: "bsh.department@mining.local.invalid", displayEmail: "" },
  adl: { name: "Mrs. Sasmita Pani", key: "sasmita.pani@gcek.ac.in", displayEmail: "sasmita.pani@gcek.ac.in" },
  all: { name: "ALL FACULTIES", key: "all-faculties-mining-4-7@local.invalid", displayEmail: "" },
};

const subjects = [
  { code: "MIPE4001", abbreviation: "MSE", name: "Mine Safety Engineering", teacher: teachers.mse, type: "Theory", periods: 3, credits: "3" },
  { code: "EEPE3005", abbreviation: "RES", name: "Renewable Energy Sources", teacher: teachers.res, type: "Theory", periods: 3, credits: "3" },
  { code: "HSOE4001", abbreviation: "MM", name: "Marketing Management", teacher: teachers.mm, type: "Theory", periods: 3, credits: "3" },
  { code: "PCAC4007", abbreviation: "ADL", name: "Applied Deep Learning", teacher: teachers.adl, type: "Theory", periods: 3, credits: "3" },
  { code: "MIPS4201", abbreviation: "SIRE-II", name: "Seminar on SIRE - II", teacher: teachers.all, type: "Seminar", periods: 2, credits: "6" },
  { code: "MIPS4202", abbreviation: "PPD-II", name: "Project for Product Development - II", teacher: teachers.all, type: "Project", periods: 2, credits: "6" },
];

const subjectRecords = subjects.map(({ code, name, teacher, type, periods, credits }) => ({
  code,
  name,
  department,
  year,
  semester,
  credits,
  weeklySessions: periods,
  type,
  teacherName: teacher.name,
  facultyName: teacher.name,
  teacherEmail: teacher.displayEmail,
  email: teacher.key,
  displayEmail: teacher.displayEmail,
  facultyId: teacher.displayEmail || "Not provided",
  teacherMaxWeeklyHours: 18,
  teacherAvailableDays: "Monday,Tuesday,Wednesday,Thursday,Friday,Saturday",
  room,
  roomType: type === "Seminar" ? "Seminar Room" : type === "Project" ? "Classroom" : "Classroom",
  roomCapacity: 60,
  expectedStudents: 30,
  active: true,
  isSample: true,
}));

const placements = [
  ["MON", "MIPE4001", 1, 1], ["MON", "PCAC4007", 2, 1], ["MON", "EEPE3005", 3, 1], ["MON", "MIPS4201", 5, 3],
  ["TUE", "EEPE3005", 1, 1], ["TUE", "MIPE4001", 2, 1], ["TUE", "HSOE4001", 3, 1], ["TUE", "MIPS4201", 5, 3],
  ["WED", "EEPE3005", 2, 1], ["WED", "HSOE4001", 3, 1], ["WED", "MIPS4202", 5, 3],
  ["THU", "HSOE4001", 2, 1], ["THU", "PCAC4007", 3, 1], ["THU", "MIPS4202", 5, 3],
  ["FRI", "MIPE4001", 1, 1], ["FRI", "PCAC4007", 2, 1],
];

const slotIndexes = [0, 1, 2, 3, 5, 6, 7];
const weekdays = ["MON", "TUE", "WED", "THU", "FRI", "SAT"];

function buildDay(day) {
  const sessions = placements.filter(([sessionDay]) => sessionDay === day);
  const cells = Object.fromEntries(slotIndexes.map((start) => [start, { start, span: 1, label: "X", empty: true }]));

  sessions.forEach(([, code, start, span]) => {
    cells[start] = { start, span, code };
    for (let slot = start + 1; slot < start + span; slot += 1) {
      cells[slot] = { start: slot, span: 0, label: "", empty: true };
    }
  });

  if (day === "SAT") {
    cells[0] = { start: 0, span: 4, label: "Tutorial/Extra Classes/Academic Activities", empty: false };
    [1, 2, 3].forEach((slot) => { cells[slot] = { start: slot, span: 0, label: "", empty: true }; });
  }

  return {
    day,
    beforeLunch: [0, 1, 2, 3].map((slot) => cells[slot]).filter((cell) => cell.span > 0),
    afterLunch: [5, 6, 7].map((slot) => cells[slot]).filter((cell) => cell.span > 0),
  };
}

export const miningSubjectRecords = subjectRecords;

export function isMiningCurrentSchedule(schedule) {
  const staleCodes = new Set(["ME401", "ME402", "ME403", "ME404", "MN054", "MN056"]);
  const details = schedule?.subjectDetails || [];
  return schedule?.department === department
    && schedule?.year === year
    && schedule?.semester === semester
    && details.length >= subjectRecords.length
    && !details.some((subject) => staleCodes.has(String(subject.code).toUpperCase()))
    && details.every((subject) => subject.name && subject.facultyName)
    && (schedule?.sessions || []).length > 0;
}

export function makeMiningSchedulePreview() {
  return {
    department,
    year,
    semester,
    academicYear: "2026-27",
    commonRoom: room,
    subjectDetails: subjectRecords.map((subject) => ({
      ...subject,
      facultyId: subject.facultyId,
      email: subject.email,
      facultyName: subject.facultyName,
    })),
    days: weekdays.map(buildDay),
    sessions: placements.map(([day, code, start, span], occurrence) => ({ day, code, start, span, occurrence })),
    timeSlots: ["9:00-9:55", "10:00-10:55", "11:00-11:55", "12:00-12:55", "1:00-2:30", "2:30-3:25", "3:25-4:20", "4:20-5:00"],
    source: "Provided Mining 7th-semester timetable",
    status: "Preview",
    previewOnly: true,
  };
}
