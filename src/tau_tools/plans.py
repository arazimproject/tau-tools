"""
Download all of the study plans at Tel Aviv University.
This file has been created by inspecting the network requests when accessing https://exact-sciences.tau.ac.il/search-studies-programs?faculta=0300.
"""

import json
import sys
from dataclasses import dataclass
from typing import Dict, List, Optional

from tau_tools.logging import console, progress, setup_logging, log
from tau_tools.utilities import request


def request_graphql(
    request_json,
    api_url="https://tochniot.tau.ac.il/graphql",
    delay=1,
    cache_key: Optional[str] = None,
):
    """
    Send a GraphQL request to the `api_url`.
    Check for errors.
    Sleep for `delay` seconds, to prevent overwhelming anything.
    """

    response = request(
        "post",
        api_url,
        json=request_json,
        cache_category="plans",
        cache_key=cache_key,
        delay=delay,
    )
    result = json.loads(response)["data"]

    if (
        "results" in result
        and "body" in result["results"]
        and "Tau" in result["results"]["body"]
        and "errmsgeng" in result["results"]["body"]["Tau"]
    ):
        raise Exception(result["results"]["body"]["Tau"]["errmsgeng"])

    return result


@dataclass
class DepartmentInfo:
    name: str
    id: str


@dataclass
class FacultyInfo:
    name: str
    id: str
    departments: List[DepartmentInfo]


@dataclass
class SchoolInfo:
    name: str
    id: str
    faculties: List[FacultyInfo]


class PlanInfo:
    def __init__(
        self, name: str, id: Optional[str], language: str, year: str, egedid: str
    ):
        self.name = name
        self.id = id
        self.language = language

        if id is None:
            self.find_id(year, egedid)

    def find_id(self, year: str, egedid: str):
        """Tries to find the plan id (tcid) from the `year` and `egedid`"""
        try:
            response = request_graphql(
                {
                    "operationName": "results",
                    "variables": {
                        "filters": {
                            "safa": "1",
                            "shana": year,
                            "egedid": egedid,
                            "tab": "generalExplanation",
                        },
                        "apiUrl": "ydhesberklali",
                    },
                    "query": "query results($apiUrl: String!, $filters: JSON!) {\n  results(apiUrl: $apiUrl, filters: $filters) {\n    body\n    __typename\n  }\n}\n",
                },
                cache_key=f"get-id-{year}-{egedid}",
            )
            self.id = response["results"]["body"][0]["tcid"]
        except Exception:
            pass


def get_schools() -> List[SchoolInfo]:
    """Returns a list of tuples (name, id) of the schools."""

    hierarchy = request_graphql(
        {
            "operationName": "getProgramsHierarchy",
            "variables": {"search": {"safa": "1"}},
            "query": "query getProgramsHierarchy($search: JSON!) {\n  getProgramsHierarchy(search: $search) {\n    id\n    name\n    rama {\n      hasUndefinedBetsefer\n      id\n      name\n      field\n      rama {\n        id\n        name\n        field\n        chug\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}\n",
        },
        cache_key="schools",
    )

    return [
        SchoolInfo(
            school["name"],
            school["id"],
            [
                FacultyInfo(
                    faculty["name"],
                    faculty["id"],
                    [
                        DepartmentInfo(department["name"], department["id"])
                        for department in faculty["rama"]
                    ],
                )
                for faculty in school["rama"]
                if faculty["rama"] is not None
            ],
        )
        for school in hierarchy["getProgramsHierarchy"]
    ]


def get_plans(school: SchoolInfo) -> List[PlanInfo]:
    """Get all of the available plans at the specified school."""

    plans = request_graphql(
        {
            "operationName": "getPrograms",
            "variables": {
                "search": {
                    "safa": "1",
                    "faculta": [
                        {
                            "id": school.id,
                            "name": school.name,
                            "__typename": "HierarchyFilter",
                            "rama": [
                                {
                                    "id": faculty.id,
                                    "name": faculty.name,
                                    "__typename": "BetseferFilter",
                                    "hasUndefinedBetsefer": "false",
                                    "field": "betsefer",
                                    "rama": [
                                        {
                                            "id": department.id,
                                            "name": department.name,
                                            "__typename": "ChugFilter",
                                            "field": "chug",
                                            "chug": True,
                                        }
                                        for department in faculty.departments
                                    ],
                                }
                                for faculty in school.faculties
                            ],
                        }
                    ],
                    "isLoadPrograms": True,
                },
                "from": 0,
                "size": 1000,
            },
            "query": "query getPrograms($search: JSON!, $from: Int, $size: Int) {\n  getPrograms(search: $search, from: $from, size: $size) {\n    total\n    results {\n      tclongkey\n      shana\n      teur\n      toar\n      currentSafa\n      isSafaAfucha\n      tcid\n      egedid\n      faculta\n      teurfaculta\n      teurfacultaeng\n      betsefer\n      teurbetsefer\n      teurbetsefereng\n      maslul\n      chug\n      teurchug\n      teurchugeng\n      teurfaculta2\n      teurfacultaeng2\n      pail\n      title\n      pailheara\n      pailhearaeng\n      showtochnit\n      __typename\n    }\n    from\n    refreshData\n    __typename\n  }\n}\n",
        },
        cache_key=f"plans-{school.id}",
    )

    return [
        PlanInfo(
            result["teur"],
            result["tcid"],
            result["currentSafa"],
            result["shana"],
            result["egedid"],
        )
        for result in plans["getPrograms"]["results"]
    ]


def get_plan(plan: PlanInfo, year=2024) -> Dict[str, List[str]]:
    details = request_graphql(
        {
            "operationName": "results",
            "variables": {
                "filters": {
                    "tcid": plan.id,
                    "shana": str(year),
                    "safa": plan.language,
                    "tab": "programStudy",
                },
                "apiUrl": "ydtochnit",
            },
            "query": "query results($apiUrl: String!, $filters: JSON!) {\n  results(apiUrl: $apiUrl, filters: $filters) {\n    body\n    __typename\n  }\n}\n",
        },
        cache_key=f"plan-{year}-{plan.id}-{plan.language}",
    )

    categories = {}
    courses = set()

    for part in details["results"]["body"][0]["rama"]:
        if "rama" not in part:
            continue

        for category in part["rama"]:
            if "kurs" not in category:
                continue

            category_name = category["teurrama"]
            category_courses = []

            for course in category["kurs"]:
                if course["kursid"] in courses:
                    continue
                courses.add(course["kursid"])

                category_courses.append(course["kursid"])

            if len(category_courses) != 0:
                categories[part["teurrama"] + " - " + category_name] = category_courses

    return categories


def main(output_file_template="plans{year}.json", year=2024):
    result = {}

    schools = get_schools()
    with progress:
        schools_task_id = progress.add_task(
            "[purple]Fetching schools...", total=len(schools)
        )
        for school in schools:
            result[school.name] = {}
            plans = [plan for plan in get_plans(school) if plan.id is not None]
            school_task_id = progress.add_task(
                f"[green]Fetching school '{school.name}' plans...", total=len(plans)
            )
            for plan in plans:
                try:
                    plan_details = get_plan(plan, year)
                    if len(plan_details) != 0:
                        result[school.name][plan.name] = plan_details
                except Exception as e:
                    log.warning(
                        f"Error fetching {plan.name} in {school.name}: [red]{e}[/red]",
                        extra={"markup": True}
                    )
                progress.update(school_task_id, advance=1)
            progress.update(school_task_id, visible=False)
            progress.update(schools_task_id, advance=1)

    with open(output_file_template.format(year=year + 1), "w") as f:
        json.dump(result, f, ensure_ascii=False)


if __name__ == "__main__":
    setup_logging()

    if len(sys.argv) == 2:
        main(year=int(sys.argv[1]) - 1)
    else:
        main()
