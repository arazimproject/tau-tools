"""
Collects all of the scraped course data into a single `courses.json` which contains only
the names of the courses and the semesters they were taught in.
"""

import json
import os

from tau_tools.logging import log, setup_logging


def main(output_file="courses.json"):
    result = {}

    courses_jsons = [
        f
        for f in sorted(os.listdir("."))[::-1]
        if f.startswith("courses-") and f.endswith(".json")
    ]
    log.info(f"Found courses JSONs: {courses_jsons}")

    for courses_json in courses_jsons:
        semester = courses_json.removeprefix("courses-").removesuffix(".json")

        with open(courses_json, "r") as f:
            courses = json.load(f)

        for course_id in courses:
            if course_id not in result:
                result[course_id] = {
                    "name": courses[course_id]["name"],
                    "semesters": [semester],
                }
            else:
                if result[course_id]["name"] != courses[course_id]["name"]:
                    log.warning(
                        f"Name mismatch of course {course_id}: changed from {courses[course_id]['name']} to {result[course_id]['name']}"
                    )
                result[course_id]["semesters"].append(semester)

    with open(output_file, "w") as f:
        json.dump(result, f, ensure_ascii=False)


if __name__ == "__main__":
    setup_logging()
    main()
