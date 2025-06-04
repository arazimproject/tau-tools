import json
import os
import re
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Union

import requests
from bs4 import BeautifulSoup
from requests.utils import cookiejar_from_dict, dict_from_cookiejar

from tau_tools.utilities import try_float, try_int


@dataclass
class CourseInfo:
    id: int
    name: str
    is_hidden: bool
    is_favourite: bool


@dataclass
class AssignmentInfo:
    id: int
    name: str
    course_id: int
    course_name: str
    due_date: datetime
    is_overdue: bool


@dataclass
class AttachmentInfo:
    filename: str
    url: str


@dataclass
class AdditionalAssignmentInfo:
    attachments: List[AttachmentInfo]
    description: str
    grade: Optional[int]
    grade_date: Optional[datetime]
    checker: Optional[str]
    feedback_comments: Optional[str]
    feedback_files: Optional[List[AttachmentInfo]]


@dataclass
class GradeInfo:
    assignment_id: int
    assignment_name: str
    grade: Optional[Union[float, str]]
    """The minimal grade possible for the assignment"""
    grade_min: Optional[Union[int, str]]
    """The maximal grade possible for the assignment"""
    grade_max: Optional[Union[int, str]]
    """The average grade of the assignment submissions"""
    grade_average: Optional[Union[float, str]]
    feedback: str


@dataclass
class RecordingInfo:
    name: str
    url: str


class MoodleException(Exception):
    def __init__(self, errorcode: str, message: str, link: str, more_info_url: str):
        Exception.__init__(self, errorcode)

        self.errorcode = errorcode
        self.message = message
        self.link = link
        self.more_info_url = more_info_url


class Moodle:
    SAML_RESPONSE_REGEX = re.compile(r'name="SAMLResponse" value="(.*?)"')
    SESSKEY_REGEX = re.compile(
        r'"https:\/\/moodle\.tau\.ac\.il\/login\/logout\.php\?sesskey=(.*?)"'
    )
    USER_ID_REGEX = re.compile(
        r'"https:\/\/moodle\.tau\.ac\.il\/user\/profile\.php\?id=(.*?)"'
    )

    sesskey: str
    user_id: int

    def __init__(
        self, username: str, id: str, password: str, session_file: Optional[str] = None
    ):
        self.username = username
        self.id = id
        self.password = password
        self.session = requests.Session()
        self.session_file = session_file

        if session_file is not None and os.path.exists(session_file):
            with open(session_file, "r") as f:
                session_info = json.load(f)

            if (
                "sesskey" in session_info
                and "cookies" in session_info
                and "user_id" in session_info
            ):
                self.session.cookies = cookiejar_from_dict(session_info["cookies"])
                self.sesskey = session_info["sesskey"]
                self.user_id = session_info["user_id"]
                return

        self._sign_in()

    def _sign_in(self):
        self.session = requests.Session()
        self.session.get("https://moodle.tau.ac.il/login/index.php")
        self.session.post(
            "https://nidp.tau.ac.il/nidp/saml2/sso?id=10&sid=0&option=credential"
        )
        self.session.post(
            "https://nidp.tau.ac.il/nidp/saml2/sso?sid=0",
            {
                "option": "credential",
                "Ecom_User_ID": self.username,
                "Ecom_User_Pid": self.id,
                "Ecom_Password": self.password,
            },
        )
        response = self.session.get("https://nidp.tau.ac.il/nidp/saml2/sso?sid=0")
        saml_response = Moodle.SAML_RESPONSE_REGEX.findall(response.text)[0]
        response = self.session.post(
            "https://moodle.tau.ac.il/auth/saml2/sp/saml2-acs.php/moodle.tau.ac.il",
            {
                "SAMLResponse": saml_response,
                "RelayState": "https://moodle.tau.ac.il/login/index.php",
            },
        )
        self.sesskey = Moodle.SESSKEY_REGEX.findall(response.text)[0]
        self.user_id = int(Moodle.USER_ID_REGEX.findall(response.text)[0])

        if self.session_file is not None:
            with open(self.session_file, "w") as f:
                json.dump(
                    {
                        "cookies": dict_from_cookiejar(self.session.cookies),
                        "sesskey": self.sesskey,
                        "user_id": self.user_id,
                    },
                    f,
                )

    def request_service(self, service_name: str, payload):
        result = self.session.post(
            f"https://moodle.tau.ac.il/lib/ajax/service.php?&sesskey={self.sesskey}&info={service_name}",
            json=payload,
        ).json()[0]

        if "error" in result and result["error"]:
            exception = result["exception"]

            if exception["errorcode"] == "servicerequireslogin":
                self._sign_in()
                return self.request_service(service_name, payload)

            raise MoodleException(
                exception["errorcode"],
                exception["message"],
                exception["link"],
                exception["moreinfourl"],
            )

        return result["data"]

    def get_page(
        self, page_id: Optional[str] = None, page_url: Optional[str] = None
    ) -> BeautifulSoup:
        if page_id is None and page_url is None:
            raise Exception(
                "At least one of `page_id` or `page_url` must be specified!"
            )
        if page_url is None:
            page_url = f"https://moodle.tau.ac.il/course/view.php?id={page_id}"
        result = self.session.get(page_url)
        return BeautifulSoup(result.text, "html.parser")

    def get_courses(self, only_visible=True) -> List[CourseInfo]:
        response = self.request_service(
            "block_mycourses_get_enrolled_courses_by_timeline_classification",
            [
                {
                    "index": 0,
                    "methodname": "block_mycourses_get_enrolled_courses_by_timeline_classification",
                    "args": {
                        "offset": 0,
                        "limit": 0,
                        "classification": "all",
                        "sort": "fullname",
                        "customfieldname": "",
                        "customfieldvalue": "",
                        "groupmetacourses": 1,
                    },
                }
            ],
        )

        return [
            CourseInfo(
                info["id"], info["fullname"], info["hidden"], info["isfavourite"]
            )
            for info in response["courses"]
            if not only_visible or info["visible"]
        ]

    def get_assignments(
        self, limit=50, since=0, until=100000000000
    ) -> List[AssignmentInfo]:
        # TODO: understand the limittononsuspendedevents argument
        response = self.request_service(
            "block_timeline_extra_local_get_action_events_by_timesort",
            [
                {
                    "index": 0,
                    "methodname": "block_timeline_extra_local_get_action_events_by_timesort",
                    "args": {
                        "limitnum": limit,
                        "timesortfrom": since,
                        "timesortto": until,
                        "limittononsuspendedevents": True,
                    },
                }
            ],
        )

        return [
            AssignmentInfo(
                info["instance"],
                info["name"],
                info["course"]["id"],
                info["course"]["fullname"],
                datetime.fromtimestamp(info["timesort"]),
                info["overdue"],
            )
            for info in response["events"]
        ]

    def get_additional_info(self, assignment_id: int):
        # TODO: parse for grade, grade_date, checker, feedback_comments and feedback_files. Note that a lot of different subsets of these optionals are possible.

        page = BeautifulSoup(
            self.session.get(
                f"https://moodle.tau.ac.il/mod/assign/view.php?id={assignment_id}"
            ).text,
            "html.parser",
        )

        attachments = [
            AttachmentInfo(a.text, a["href"])
            for a in page.find_all("a")
            if "href" in a.attrs and "introattachment" in a["href"]
        ]

        description = page.find("div", {"class": "activity-description"})

        return AdditionalAssignmentInfo(
            attachments,
            str(description) if description.text.strip() != "" else "",
            None,
            None,
            None,
            None,
            None,
        )

    def download_url(self, url: str):
        response = self.session.get(url)
        return response.content

    def get_recordings(self, course_id: int):
        response = self.session.post(
            "https://moodle.tau.ac.il/blocks/panopto/panopto_content.php",
            {"sesskey": self.sesskey, "courseid": course_id},
        )
        response = BeautifulSoup(response.text, "html.parser")

        return [
            RecordingInfo(a.text, a["href"])
            for a in response.find_all("a")
            # filtering is needed to ignore the settings link
            if "Viewer.aspx" in a["href"]
        ]

    def get_grades(self, course_id: int) -> List[GradeInfo]:
        response = self.session.get(
            f"https://moodle.tau.ac.il/course/user.php?mode=grade&id={course_id}&user={self.user_id}"
        )
        response = BeautifulSoup(response.text, "html.parser")

        grades = []
        for tr in response.find_all("tr"):
            tds: List[BeautifulSoup] = tr.find_all("td")

            if len(tds) != 6:
                continue

            a: BeautifulSoup = tds[0].find("a")

            if a is None:
                continue

            grade_range = tds[3].text.split("–")

            grades.append(
                GradeInfo(
                    assignment_id=int(a["href"].split("=")[-1]),
                    assignment_name=a.text,
                    grade=None if tds[2].text == "-" else try_float(tds[2].text),
                    grade_min=try_int(grade_range[0]),
                    grade_max=try_int(grade_range[1]),
                    grade_average=None
                    if tds[4].text == "-"
                    else try_float(tds[4].text),
                    feedback=tds[5].text.strip(),
                )
            )

        return grades
