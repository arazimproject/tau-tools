"""
Download all of the course details at Tel Aviv University.
This file was inspired by https://github.com/TAUHacks/CourseScrape,
and we assume it was created by inspecting the network requests
when accessing https://www.ims.tau.ac.il/Tal/KR/Search_P.aspx.
"""

import json
import time
import urllib.parse
from enum import Enum
from typing import List, Optional, Tuple

import requests
from bs4 import BeautifulSoup
from colorama import Fore, init

HEBREW_SEMESTERS = {"a": "א'", "b": "ב'"}


class Semester(Enum):
    WINTER = ["a"]
    SPRING = ["b"]
    ALL = ["a", "b"]


class ExamInfo:
    def __init__(self, moed: str, date: str, hour: str, type: str):
        self.moed = moed
        self.date = date
        self.hour = hour
        self.type = type


class LessonInfo:
    def __init__(
        self, semester: str, day: str, time: str, building: str, room: str, type: str
    ):
        self.semester = semester
        self.day = day
        self.time = time
        self.building = building
        self.room = room
        self.type = type


class GroupInfo:
    def __init__(
        self,
        name: str,
        id: str,
        group: str,
        faculty: str,
        lecturer: str,
        exams: List[ExamInfo],
        lessons: List[LessonInfo],
    ):
        self.name = name
        self.id = id
        self.group = group
        self.faculty = faculty
        self.lecturer = lecturer
        self.exams = exams
        self.lessons = lessons


def request(url: str, s: Optional[requests.Session] = None):
    response = s.get(url) if s is not None else requests.get(url)

    return BeautifulSoup(response.text, "html.parser")


def get_schools() -> List[Tuple[str, List[str]]]:
    """
    Returns a list of tuples (school_name, selection_options) of the schools.
    The `selection_options` are either the option for everything in the school,
    or a list of every option for faculties/types in the school.
    """

    search_page = request("https://www.ims.tau.ac.il/Tal/KR/Search_P.aspx")
    all_schools = search_page.select(".table1 select.freeselect.list")
    all_options = []

    for school in all_schools:
        options = [x for x in school.select("option") if x.text != ""]

        if options[0].text.startswith("כל "):
            options = [options[0]]

        all_options.append((school["name"], [option["value"] for option in options]))

    return all_options


def get_exams(
    course_id: str,
    group: str,
    year: str,
    semester: str,
    s: Optional[requests.Session] = None,
) -> List[ExamInfo]:
    """Example: `get_exams("03683087", "01", "2023", "1")`"""

    url = "https://www.ims.tau.ac.il/Tal/KR/Bhina_L.aspx?" + urllib.parse.urlencode(
        {
            "kurs": course_id.replace("-", ""),
            "kv": group,
            "sem": year + semester,
        }
    )
    result_soup = request(url, s)

    if result_soup.select(".msgerrs"):
        # An error ocurred, assume there are no exams
        return []

    header_row, *all_rows = result_soup.select_one(".tableblds").select("tr")

    assert (
        str(header_row)
        == '<tr class="listth"><th>מועד</th><th>תאריך</th><th>שעה</th><th>סוג מטלה</th></tr>'
    )

    result = []
    for row in all_rows:
        cols = row.select("td")
        item = {
            "moed": cols[0].text.strip(),
            "date": cols[1].text.strip(),
            "hour": cols[2].text.strip(),
            "type": cols[3].text.strip(),
        }
        result.append(item)

    return result


def _parse_result_page(result_soup: BeautifulSoup, year: str) -> List[GroupInfo]:
    all_rows = result_soup.select_one("#frmgrid table[dir=rtl]").select("tr")
    all_rows = all_rows[1:]
    i = 0
    courses = []
    while i < len(all_rows):
        try:
            if (
                "kotcol" in all_rows[i]["class"]
                and len(list(all_rows[i].children)) == 2
            ):
                # start of course
                i += 1
                # next row is the course name + id
                course_name = list(all_rows[i].children)[1].text
                course_id = next(next(all_rows[i].children).children).strip()
                course_group = (
                    all_rows[i].select_one("span").next_element.next_element.strip()
                )
                i += 1
                # this row has the faculty
                course_faculty = list(all_rows[i].children)[1].text
                i += 1
                # look for the times and instructor section
                while not ("kotcol" in all_rows[i - 1]["class"]):
                    i += 1

                course_lecturer = None

                course_lessons: list[LessonInfo] = []

                # store a set of the semesters of the course
                semester_set = set()

                while "רשימת תפוצה" not in all_rows[i].text:
                    split = [x.text.strip() for x in all_rows[i].children]
                    if len(list(all_rows[i].children)) != 7:
                        if course_lecturer is not None:
                            course_lecturer += ", " + split[0]
                        i += 1
                        continue

                    (
                        curr_lecturer,
                        ofen_horaa,
                        building,
                        room,
                        day,
                        time,
                        semester,
                    ) = split

                    if course_lecturer == None and len(curr_lecturer) != 0:
                        course_lecturer = curr_lecturer

                    if ofen_horaa != "":
                        course_lessons.append(
                            LessonInfo(semester, day, time, building, room, ofen_horaa)
                        )
                        semester_set.add(semester)
                    i += 1

                # look up the exam if listing is only in one semester
                course_exams = []
                if len(semester_set) == 1 and course_lessons[0].semester in [
                    "א'",
                    "ב'",
                ]:
                    sem = ["א'", "ב'"].index(course_lessons[0].semester) + 1
                    try:
                        course_exams = get_exams(
                            course_id, course_group, year, str(sem)
                        )
                    except:
                        pass

                courses.append(
                    GroupInfo(
                        course_name,
                        course_id.replace("-", ""),
                        course_group,
                        course_faculty,
                        course_lecturer,
                        course_exams,
                        course_lessons,
                    )
                )
            else:
                i += 1
        except KeyError:
            i += 1

    return courses


def get_school_courses(
    school_details: Tuple[str, List[str]],
    year="2023",
    semester=Semester.ALL,
    delay=1.0,
    print_progress=True,
) -> List[GroupInfo]:
    school_select, school_options = school_details
    result = []

    s = requests.Session()

    payload = {
        "lstYear1": year,
        "txtShemKurs": "",
        "txtShemMore": "",
    }

    if semester == Semester.WINTER:
        payload["ckSem"] = "1"
    elif semester == Semester.SPRING:
        payload["ckSem"] = "2"

    for option_index, option in enumerate(school_options):
        if print_progress:
            print(
                f"{Fore.GREEN}[Search]{Fore.RESET} Searching option ({option_index + 1}/{len(school_options)})"
            )
        data = {**payload, school_select: option}
        search_result_page = BeautifulSoup(
            s.post(
                "https://www.ims.tau.ac.il/Tal/KR/Search_L.aspx",
                data=data,
                headers={
                    "Accept": "text/html,application/xhtml+xml,application/xml",
                    "Content-Type": "application/x-www-form-urlencoded",
                    "User-Agent": "CourseScrape",
                },
            ).text,
            "html.parser",
        )

        while len(search_result_page.select("#next")) > 0:
            if print_progress:
                print(f"{Fore.GREEN}[Search]{Fore.RESET} Fetching page")
            result += _parse_result_page(search_result_page, year)

            data = {"dir1": "1"}
            for hidden_input in search_result_page.select("input[type=hidden]"):
                try:
                    data[hidden_input["name"]] = hidden_input["value"]
                except KeyError:
                    pass

            search_result_page = BeautifulSoup(
                s.post(
                    "https://www.ims.tau.ac.il/Tal/KR/Search_L.aspx",
                    data=data,
                    headers={
                        "Accept": "text/html,application/xhtml+xml,application/xml",
                        "Content-Type": "application/x-www-form-urlencoded",
                        "User-Agent": "CourseScrape",
                    },
                ).text,
                "html.parser",
            )

            time.sleep(delay)

        # The final page
        result += _parse_result_page(search_result_page, year)

    return result


def main(
    output_file_template="{year}{semester}.json", year="2023", semesters=Semester.ALL
):
    init()

    schools = get_schools()
    groups: list[GroupInfo] = []

    for school_index, school in enumerate(schools):
        print(
            f"{Fore.BLUE}[School]{Fore.RESET} Fetching school ({school_index + 1}/{len(schools)})"
        )
        groups += get_school_courses(school, year, semesters)

    for semester in semesters.value:
        output_file = output_file_template.format(year=year, semester=semester)

        courses = {}
        for group in groups:
            group_lessons = [
                l for l in group.lessons if l.semester == HEBREW_SEMESTERS[semester]
            ]
            if len(group_lessons) == 0:
                continue

            if group.id not in courses:
                courses[group.id] = {
                    "name": group.name,
                    "faculty": group.faculty,
                    "exams": group.exams,
                    "groups": [],
                }

            if len(group.exams) != 0:
                courses[group.id]["exams"] = group.exams

            courses[group.id]["groups"].append(
                {
                    "group": group.group,
                    "lecturer": group.lecturer,
                    "lessons": [
                        {k: v for k, v in lesson.__dict__.items() if k != "semester"}
                        for lesson in group_lessons
                    ],
                }
            )

        with open(output_file, "w") as f:
            json.dump(courses, f, ensure_ascii=False)


if __name__ == "__main__":
    main()
