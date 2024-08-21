"""
Get information about exams happening today at Tel Aviv University.
Inspired by the dashboard at https://lobbydashboard.tau.ac.il/exact-sciences/monitors/%D7%9C%D7%95%D7%97-%D7%91%D7%97%D7%99%D7%A0%D7%95%D7%AA-%D7%99%D7%95%D7%9E%D7%99-%D7%94%D7%A4%D7%A7%D7%95%D7%9C%D7%98%D7%94-%D7%9C%D7%9E%D7%93%D7%A2%D7%99%D7%9D-%D7%9E%D7%93%D7%95%D7%99%D7%A7%D7%99/
"""

from dataclasses import dataclass

import requests

from tau_tools.logging import console, setup_logging


@dataclass
class ExamInfo:
    course_id: str
    course_name: str
    group: str
    semester: int
    """Either 1 or 2"""
    start_hour: str
    """Example: '09:00'"""
    end_hour: str
    """Example: '12:00'"""
    building: str
    room: str
    surname_letters: str
    """Example: א - ד""" """Example: א - ד"""


def get_exam_info(post_id=68, site_id=7):
    response = requests.post(
        "https://lobbydashboard.tau.ac.il/evg-ajax/",
        data={"act": "get_app", "post_id": post_id, "site_id": site_id},
    )
    json = response.json()

    if "is_error" in json and json["is_error"]:
        raise Exception(json["message"])

    return [
        ExamInfo(
            exam["course_ID"],
            exam["course_name"],
            exam["group"],
            exam["semester"],
            exam["exam_hour"],
            exam["exam_end_hour"],
            exam["building"],
            exam["room"],
            exam["surname_letters"],
        )
        for exam in json["data"]["examslist"]
    ]


if __name__ == "__main__":
    setup_logging()

    console.print(get_exam_info())
