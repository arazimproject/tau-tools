import json
import sys

from bs4 import BeautifulSoup

from tau_tools.logging import progress, setup_logging
from tau_tools.utilities import request


def main(output_file_template="syllabi-{year}.json", year=2024):
    with open("courses-{year}a.json".format(year=year)) as f:
        courses = json.load(f)
    with open("courses-{year}b.json".format(year=year)) as f:
        courses = {**courses, **json.load(f)}

    result = {}
    with progress:
        courses_task_id = progress.add_task(
            "[purple]Fetching syllabi...", total=len(courses)
        )
        for course in sorted(courses.keys()):
            first_group = courses[course]["groups"][0]["group"]
            syllabus = (
                BeautifulSoup(
                    request(
                        "GET",
                        f"https://www.ims.tau.ac.il/Tal/Syllabus/Syllabus_L.aspx?course={course}{first_group}&year={year}",
                        cache_category="syllabi",
                        cache_key=f"syllabus-{course}{first_group}-{year}",
                        headers={
                            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36"
                        },
                    ),
                    "html.parser",
                )
                .find("section", {"class": "main-course-contents"})
                .text.strip()
            )
            if syllabus != "":
                result[course] = syllabus
            progress.update(courses_task_id, advance=1)

    with open(output_file_template.format(year=str(year + 1)), "w") as f:
        json.dump(result, f, ensure_ascii=False)


if __name__ == "__main__":
    setup_logging()

    if len(sys.argv) == 2:
        main(year=int(sys.argv[1]) - 1)
    else:
        main()
