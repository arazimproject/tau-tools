import json
from dataclasses import dataclass

from bs4 import BeautifulSoup

from tau_tools.logging import progress, setup_logging
from tau_tools.utilities import request


@dataclass
class RunStatistics:
    total_available: int
    run_available: int
    wanted: int
    received: int
    maximal: int
    minimal: int


def get_faculty(course: str):
    if course.startswith("016"):
        return "0160"
    elif course.startswith("01"):
        return "0100"
    elif course.startswith("03"):
        return "0300"
    elif course.startswith("04"):
        return "0400"
    elif course.startswith("05"):
        return "0500"
    elif course.startswith("06"):
        return "0600"
    elif course.startswith("07"):
        return "0700"
    elif course.startswith("08"):
        return "0800"
    elif course.startswith("09"):
        return "0900"
    elif course.startswith("10"):
        return "1000"
    elif course.startswith("11"):
        return "1100"
    elif course.startswith("123"):
        return "1230"
    elif course.startswith("12"):
        return "1200"
    elif course.startswith("14"):
        return "1400"
    elif course.startswith("188"):
        return "1880"


def main(output_file="bidding.json"):
    with open("courses.json") as f:
        courses = json.load(f)

    result = {}
    with progress:
        courses_task_id = progress.add_task(
            "[purple]Fetching courses...", total=len(courses)
        )
        for course in sorted(courses.keys()):
            course_result = {}
            faculty = get_faculty(course)
            if faculty is None:
                continue

            for semester in ["1", "2", "3"]:
                for run in ["1", "2", "3"]:
                    page = BeautifulSoup(
                        request(
                            "POST",
                            "https://www.ims.tau.ac.il/Bidd/Stats/Stats_L.aspx",
                            data={
                                "lstFacBidd": faculty,
                                "lstShana": "",
                                "sem": semester,
                                "ritza": run,
                                "txtKurs": course,
                                "txtKursName": "",
                                "lstPageSize": "1000",
                            },
                            cache_category="bidding",
                            cache_key=f"stats-{course}-{semester}-{run}",
                        ),
                        "html.parser",
                    )

                    table = page.find("table", {"id": "Grd1"})
                    rows = table.find_all("tr")[1:] if table is not None else []
                    for row in rows:
                        cells = [td.text.strip() for td in row.find_all("td")]
                        if len(cells) != 16:
                            continue

                        semester = cells[10].replace("/1", "a").replace("/2", "b")
                        faculty = cells[12].split("-")[0]
                        group = cells[13].removesuffix("*")
                        if group == "" or semester.endswith("/3"):
                            continue

                        statistics = RunStatistics(
                            total_available=int(cells[8]),
                            run_available=int(cells[7]),
                            wanted=int(cells[6]),
                            received=int(cells[5]),
                            maximal=int(cells[3]),
                            minimal=int(cells[2]),
                        )

                        if semester not in course_result:
                            course_result[semester] = {}
                        if group not in course_result[semester]:
                            course_result[semester][group] = []
                        course_result[semester][group].append(
                            {
                                "faculty": faculty,
                                "total_available": statistics.total_available,
                                "run_available": statistics.run_available,
                                "wanted": statistics.wanted,
                                "received": statistics.received,
                                "maximal": statistics.maximal,
                                "minimal": statistics.minimal,
                            }
                        )
            progress.update(courses_task_id, advance=1)

            if len(course_result) != 0:
                for semester in course_result:
                    for group in course_result[semester]:
                        with_faculty = [
                            x
                            for x in course_result[semester][group]
                            if x["faculty"] != ""
                        ]
                        if len(with_faculty) != 0:
                            course_result[semester][group] = with_faculty
                result[course] = course_result
    with open(output_file, "w") as f:
        json.dump(result, f, ensure_ascii=False)


if __name__ == "__main__":
    setup_logging()
    main()
