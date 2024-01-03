import os
import json
import re
from typing import List, Optional
import requests
from requests.utils import dict_from_cookiejar, cookiejar_from_dict
from datetime import datetime
from dataclasses import dataclass
from bs4 import BeautifulSoup


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
            self.session.cookies = cookiejar_from_dict(session_info["cookies"])
            self.sesskey = session_info["sesskey"]
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
        self.sesskey: str = Moodle.SESSKEY_REGEX.findall(response.text)[0]

        if self.session_file is not None:
            with open(self.session_file, "w") as f:
                json.dump(
                    {
                        "cookies": dict_from_cookiejar(self.session.cookies),
                        "sesskey": self.sesskey,
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
            if not (only_visible and info["visible"])
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
                info["id"],
                info["name"],
                info["course"]["id"],
                info["course"]["fullname"],
                datetime.fromtimestamp(info["timesort"]),
                info["overdue"],
            )
            for info in response["events"]
        ]

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
