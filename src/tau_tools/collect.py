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

    semester_jsons = {}

    for courses_json in courses_jsons:
        semester = courses_json.removeprefix("courses-").removesuffix(".json")
        log.info(f"Loading courses from {semester}")

        with open(courses_json, "r") as f:
            courses = json.load(f)

        semester_jsons[semester] = courses

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

    if not os.path.exists("moodle-exams.json"):
        return

    log.info("Found moodle exams JSON")
    with open("moodle-exams.json", "r") as f:
        moodle_exams = json.load(f)

    corrections = {}
    if os.path.exists("corrections.json"):
        log.info("Found corrections JSON")
        with open("corrections.json", "r") as f:
            corrections = json.load(f)

    for year_exams in moodle_exams:
        year = year_exams["year"]
        if f"{year}a" not in semester_jsons or f"{year}b" not in semester_jsons:
            log.warning(f"Missing JSON for {year}, skipping")

        # Remove existing links.
        for course in list(semester_jsons[f"{year}a"].values()) + list(
            semester_jsons[f"{year}b"].values()
        ):
            if "exam_links" in course:
                course.pop("exam_links")

        for filename, url in year_exams["results"]:
            exam_course_id = "".join(filename.split("-")[:2]).strip()
            exam_course_id = exam_course_id.split(" ")[0]

            if exam_course_id in corrections:
                exam_course_id = corrections[exam_course_id]

            semesters = ["a", "b"]
            if "סמ א" in filename:
                semesters = ["a"]
            elif "סמ ב" in filename:
                semesters = ["b"]

            count = 0
            # Account for +-1 errors in the year.
            for y in [int(year), int(year) + 1, int(year) - 1]:
                for semester in semesters:
                    if f"{y}{semester}" not in semester_jsons:
                        continue
                    semester_courses = semester_jsons[f"{y}{semester}"]
                    if exam_course_id in semester_courses:
                        if "exam_links" not in semester_courses[exam_course_id]:
                            semester_courses[exam_course_id]["exam_links"] = []
                        count += 1
                        if count == 1:
                            semester_courses[exam_course_id]["exam_links"].append(url)

                if count > 0:
                    break
            if count == 0:
                log.error(
                    f"Couldn't find {filename} in {year}",
                )
            elif count != 1:
                log.warning(
                    "Added to semester a only: " + exam_course_id,
                )

    for semester, semester_courses in semester_jsons.items():
        with open(f"courses-{semester}.json", "w") as f:
            json.dump(semester_courses, f, ensure_ascii=False)


if __name__ == "__main__":
    setup_logging()
    main()
