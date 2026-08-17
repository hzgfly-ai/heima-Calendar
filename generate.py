#!/usr/bin/env python3
"""
generate.py — 根据 data/schedule.json 生成 ke.ics

支持两种课表格式(可并存):
1. courses  — 按周循环的课(weekday + 节次 + weeks 列表)
2. events   — 按具体日期的一次性课表(用于集训/短期课)

用法: python3 generate.py
"""
import json
from pathlib import Path
from datetime import datetime, timedelta, date

ROOT = Path(__file__).parent
DATA = ROOT / "data" / "schedule.json"
OUT = ROOT / "ke.ics"


def escape(s: str) -> str:
    return (
        s.replace("\\", "\\\\")
        .replace(",", "\\,")
        .replace(";", "\\;")
        .replace("\n", "\\n")
    )


def fmt_dt(dt: datetime) -> str:
    return dt.strftime("%Y%m%dT%H%M%S")


def fmt_d(d: date) -> str:
    """全天事件用 DATE-only 格式"""
    return d.strftime("%Y%m%d")


def all_day(d: date, summary: str, location: str = "") -> list:
    """生成全天事件(00:00 → 次日 00:00)。全天事件用 VALUE=DATE 标记"""
    lines = [
        "BEGIN:VEVENT",
        f"UID:allday-{summary}-{d.isoformat()}@heima-calendar",
        f"DTSTAMP:{fmt_dt(datetime.now())}",
        f"DTSTART;VALUE=DATE:{fmt_d(d)}",
        f"DTEND;VALUE=DATE:{fmt_d(d + timedelta(days=1))}",
        f"SUMMARY:{escape(summary)}",
        f"LOCATION:{escape(location)}" if location else "LOCATION:",
        "TRANSP:TRANSPARENT",
        "END:VEVENT",
    ]
    return lines


def build_courses(data: dict, lines: list) -> int:
    """按周循环的课表。返回生成的事件数"""
    if "term_start" not in data or "courses" not in data:
        return 0

    term_start = datetime.strptime(data["term_start"], "%Y-%m-%d").date()
    DEFAULT_SLOTS = {
        1: ("08:00", "08:45"), 3: ("08:55", "09:40"),
        4: ("10:00", "10:45"), 5: ("10:55", "11:40"),
        6: ("14:00", "14:45"), 7: ("14:55", "15:40"),
        8: ("16:00", "16:45"), 9: ("16:55", "17:40"),
        10: ("19:00", "19:45"), 11: ("19:55", "20:40"),
    }

    count = 0
    for c in data["courses"]:
        name = c["name"]
        location = c.get("location", "")
        teacher = c.get("teacher", "")
        weekday = c["weekday"]
        start_slot = c["start"]
        end_slot = c["end"]
        weeks = c["weeks"]

        # JSON 加载后 slot_times 的 key 是字符串
        slot_times = c.get("slot_times")
        if slot_times:
            slot_times = {int(k): tuple(v) for k, v in slot_times.items()}

        for week in weeks:
            first_day = term_start + timedelta(days=(week - 1) * 7)
            event_date = first_day + timedelta(days=weekday - 1)

            for slot in range(start_slot, end_slot + 1):
                if slot_times and slot in slot_times:
                    sh, sm = slot_times[slot]
                elif slot in DEFAULT_SLOTS:
                    sh, sm = DEFAULT_SLOTS[slot]
                else:
                    continue

                sh_h, sh_m = map(int, sh.split(":"))
                sm_h, sm_m = map(int, sm.split(":"))

                dt_start = datetime.combine(event_date, datetime.min.time()).replace(
                    hour=sh_h, minute=sh_m
                )
                dt_end = datetime.combine(event_date, datetime.min.time()).replace(
                    hour=sm_h, minute=sm_m
                )

                lines.extend([
                    "BEGIN:VEVENT",
                    f"UID:course-{name}-{week}-{slot}@heima-calendar",
                    f"DTSTAMP:{fmt_dt(datetime.now())}",
                    f"DTSTART;TZID=Asia/Shanghai:{fmt_dt(dt_start)}",
                    f"DTEND;TZID=Asia/Shanghai:{fmt_dt(dt_end)}",
                    f"SUMMARY:{escape(name)}",
                    f"LOCATION:{escape(location)}" if location else "LOCATION:",
                    f"DESCRIPTION:{escape(f'老师:{teacher}')}" if teacher else "DESCRIPTION:",
                    "END:VEVENT",
                ])
                count += 1

    return count


def build_events(events: list, lines: list) -> int:
    """
    按具体日期的一次性课表。
    每条 event: { date: "YYYY-MM-DD", name: "...", location: "...", type: "course|self_study|rest" }
    - course: 真课,全天事件
    - self_study: 自习,全天事件
    - rest: 休息,不进日历(返回 0)
    """
    count = 0
    for e in events:
        etype = e.get("type", "course")
        if etype == "rest":
            continue

        d = datetime.strptime(e["date"], "%Y-%m-%d").date()
        name = e.get("name") or ("自习" if etype == "self_study" else "课程")
        location = e.get("location", "")

        lines.extend(all_day(d, name, location))
        count += 1

    return count


def build():
    data = json.loads(DATA.read_text(encoding="utf-8"))

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//heima-calendar//AI-generated//ZH",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:{escape(data.get('calname', '黑马课表'))}",
        "X-WR-TIMEZONE:Asia/Shanghai",
    ]

    n_courses = build_courses(data, lines)
    n_events = build_events(data.get("events", []), lines)

    lines.append("END:VCALENDAR")
    OUT.write_text("\r\n".join(lines) + "\r\n", encoding="utf-8")
    print(f"✓ 写入 {OUT} (周课 {n_courses} 个 + 一次性 {n_events} 个 = {n_courses + n_events} 个事件)")


if __name__ == "__main__":
    build()