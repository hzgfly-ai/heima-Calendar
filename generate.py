#!/usr/bin/env python3
"""
generate.py — 根据 data/schedule.json 生成 ke.ics
用法: python3 generate.py
"""
import json
from pathlib import Path
from datetime import datetime, timedelta

ROOT = Path(__file__).parent
DATA = ROOT / "data" / "schedule.json"
OUT = ROOT / "ke.ics"


def uid(course: str, week: int, slot: int) -> str:
    return f"{course}-{week}-{slot}@heima-calendar"


def escape(s: str) -> str:
    return (
        s.replace("\\", "\\\\")
        .replace(",", "\\,")
        .replace(";", "\\;")
        .replace("\n", "\\n")
    )


def fmt(dt: datetime) -> str:
    return dt.strftime("%Y%m%dT%H%M%S")


def build():
    data = json.loads(DATA.read_text(encoding="utf-8"))
    term_start = datetime.strptime(data["term_start"], "%Y-%m-%d").date()
    courses = data["courses"]

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//heima-calendar//AI-generated//ZH",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:黑马课表",
        "X-WR-TIMEZONE:Asia/Shanghai",
    ]

    for c in courses:
        name = c["name"]
        location = c.get("location", "")
        teacher = c.get("teacher", "")
        weekday = c["weekday"]  # 1=周一 ... 7=周日
        start_slot = c["start"]  # 第几节开始
        end_slot = c["end"]      # 第几节结束
        weeks = c["weeks"]       # 上课的周次列表 [1,2,3,...]
        slot_times = c.get("slot_times")  # 可选,自定义时间

        # 默认节次时间(可按学校调整)
        DEFAULT_SLOTS = {
            1: ("08:00", "08:45"), 3: ("08:55", "09:40"),
            4: ("10:00", "10:45"), 5: ("10:55", "11:40"),
            6: ("14:00", "14:45"), 7: ("14:55", "15:40"),
            8: ("16:00", "16:45"), 9: ("16:55", "17:40"),
            10: ("19:00", "19:45"), 11: ("19:55", "20:40"),
        }

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

                summary = escape(name)
                loc = escape(location)
                desc = escape(f"老师:{teacher}") if teacher else ""

                lines.extend([
                    "BEGIN:VEVENT",
                    f"UID:{uid(name, week, slot)}",
                    f"DTSTAMP:{fmt(datetime.now())}",
                    f"DTSTART;TZID=Asia/Shanghai:{fmt(dt_start)}",
                    f"DTEND;TZID=Asia/Shanghai:{fmt(dt_end)}",
                    f"SUMMARY:{summary}",
                    f"LOCATION:{loc}" if loc else "LOCATION:",
                    f"DESCRIPTION:{desc}" if desc else "DESCRIPTION:",
                    "END:VEVENT",
                ])

    lines.append("END:VCALENDAR")
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    count = sum(1 for l in lines if l == "BEGIN:VEVENT")
    print(f"✓ 写入 {OUT} ({count} 个事件)")


if __name__ == "__main__":
    build()