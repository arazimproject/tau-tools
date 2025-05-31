import json
import sys

from bs4 import BeautifulSoup, Tag

from tau_tools.logging import progress, setup_logging
from tau_tools.utilities import request


def convert_table(table: Tag):
    if table.text.strip() == "אין נתונים":
        return

    result = {"kind": "all", "courses": []}
    working_result = result
    for row in table.find_all("tr", recursive=False):
        subtable = row.find("table")
        if row.text == "או":
            working_result["kind"] = "any"
        elif row.text == "וגם":
            continue
        elif subtable is not None and len(subtable.find_all("tr")) > 1:
            working_result["courses"].append(convert_table(subtable))
        elif row.text == "קורסים מקבילים נדרשים":
            result["parallel"] = {"kind": "all", "courses": []}
            working_result = result["parallel"]
        else:
            td = row.find("td") if subtable is None else subtable.find("td")
            if td is not None and (course := td.text.replace("-", "").strip()) != "":
                working_result["courses"].append(course)
    if len(result["courses"]) == 0:
        result.pop("courses")
        result.pop("kind")
    return result


def get_prerequisites(course: str, group: str, year: int, semester: str):
    page = BeautifulSoup(
        request(
            "GET",
            f"https://www.ims.tau.ac.il/tal/kr/Drishot_L.aspx?kurs={course}&kv={group}&sem={year}{semester}",
            cache_category="prerequisites",
            cache_key=f"prerequisites-{course}{group}-{year}{semester}",
            headers={
                "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Mobile Safari/537.36,gzip(gfe)"
            },
        ),
        "html.parser",
    )
    table = page.find_all("table", {"class": "tableblds"})[-1]
    return convert_table(table)


def main(
    output_file_template="prerequisites-{year}{semester}.json",
    year=2024,
    semesters=["a", "b"],
):
    for semester in semesters:
        with open(
            "courses-{year}{semester}.json".format(year=year + 1, semester=semester)
        ) as f:
            courses = json.load(f)

        result = {}
        with progress:
            courses_task_id = progress.add_task(
                "[purple]Fetching prerequisites...", total=len(courses)
            )
            for course in sorted(courses.keys()):
                try:
                    first_group = courses[course]["groups"][0]["group"]
                    course_result = get_prerequisites(
                        course, first_group, year, semester
                    )
                    if course_result is not None:
                        result[course] = course_result
                except Exception as e:
                    print(
                        f"Exception in prerequisites-{course}{first_group}-{year}{semester}"
                    )
                    raise e

                progress.update(courses_task_id, advance=1)
            progress.update(courses_task_id, visible=False)

        with open(
            output_file_template.format(year=str(year + 1), semester=semester), "w"
        ) as f:
            json.dump(result, f, ensure_ascii=False)


if __name__ == "__main__":
    setup_logging()

    if len(sys.argv) == 2:
        main(year=int(sys.argv[1]) - 1)
    else:
        main()
