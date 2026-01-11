#!/usr/bin/env python3

import argparse
import datetime as dt
import yaml
import requests
import sys
from zoneinfo import ZoneInfo

PACIFIC = ZoneInfo("America/Los_Angeles")

DAY_TO_OFFSET = {
    "sunday": 0,
    "monday": 1,
    "tuesday": 2,
    "wednesday": 3,
    "thursday": 4,
    "friday": 5,
    "saturday": 6,
}

def parse_time_range(s):
    start, end = s.split("-")
    sh, sm = map(int, start.split(":"))
    eh, em = map(int, end.split(":"))
    duration = (eh * 60 + em) - (sh * 60 + sm)
    return sh, sm, duration

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("yaml_file")
    parser.add_argument("--token", required=True)
    args = parser.parse_args()

    with open(args.yaml_file) as f:
        config = yaml.safe_load(f)

    shifts = {
        name.lower(): parse_time_range(timerange)
        for name, timerange in config["shifts"].items()
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"CS198 {args.token}",
    }

    for cohort in config["cohorts"]:
        for week_num in cohort["weeks"]:
            base_date = config["weeks"][week_num]

            for sunet, assignment in cohort["helpers"].items():
                day_name, shift_name = assignment.split()
                day_offset = DAY_TO_OFFSET[day_name.lower()]
                sh, sm, duration = shifts[shift_name.lower()]

                start_date = base_date + dt.timedelta(days=day_offset)

                start_time = dt.datetime(
                    year=start_date.year,
                    month=start_date.month,
                    day=start_date.day,
                    hour=sh,
                    minute=sm,
                    tzinfo=PACIFIC
                )

                payload = {
                    "id": None,
                    "isRegular": True,
                    "numCopies": 1,
                    "queues": [],
                    "people": [sunet],
                    "person": None,
                    "duration": duration,
                    "startTime": start_time.isoformat()
                }

                url = f"{config["endpoint"]}/quarters/{config["quarter"]}/lair/shifts"

                r = requests.post(url, json=payload, headers=headers)
                if not r.ok:
                    print("FAILED:", sunet, assignment, start_time, file=sys.stderr)
                    print(r.text, file=sys.stderr)
                else:
                    print("OK:", sunet, assignment, start_time)

if __name__ == "__main__":
    main()
