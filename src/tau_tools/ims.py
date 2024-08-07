import datetime
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

import requests
from bs4 import BeautifulSoup

IMS_BASE_URL = "https://iims.tau.ac.il"


@dataclass(unsafe_hash=True)
class GradeInfo:
    semester: str
    """The full semester of the course, in our year format, e.g. 2025a"""

    course_id: str
    """The 8-digit ID of the course, e.g. 03661111"""

    grade: Optional[int]
    """The grade of the user in the course"""

    is_exempt: bool
    """Is the student exempt from this course?"""


class IMS:
    def __init__(self, username: str, id: str, password: str):
        self.username = username
        self.id = id
        self.password = password
        self.session = requests.Session()

        self._sign_in()

    def _sign_in(self):
        self.session = requests.Session()

        # Because of stupid redirection stuff, we need to sign in to the regular stuff before IMS.
        self.session.get(IMS_BASE_URL + "/Tal/")
        self.session.post(
            "https://nidp.tau.ac.il/nidp/saml2/sso?id=10&sid=0&option=credential",
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
        self.session.get("https://nidp.tau.ac.il/nidp/saml2/sso?sid=0")

        response = self.session.post(
            IMS_BASE_URL + "/Tal/Login_Chk.aspx",
            data={
                "txtUser": self.username,
                "txtId": self.id,
                "txtPass": self.password,
                "enter": "כניסה",
                "javas": "1",
                "src": "",
            },
        )

        if "/Tal/Sys/Main.aspx" not in response.url:
            raise Exception("Invalid username or password!")

    def request_page(
        self,
        method: str,
        path: str,
        params: Dict[str, str],
        data: Optional[Any] = None,
        attempt_number=1,
        max_attempts=5,
        delay=0.1,
    ):
        params["id"] = self.id
        params["dt"] = datetime.datetime.now().strftime("%d%m%Y%H%M%S")

        url = IMS_BASE_URL + "/Tal/" + path + "?" + urlencode(params)
        response = self.session.request(method, url, data=data)
        result = BeautifulSoup(response.text, "html.parser")

        # The system is currently sometimes inconsistent.
        if attempt_number < 10 and (
            result.find("title") is None
            or result.find("title").text == 'אוניברסיטת ת"א - יציאה'
        ):
            time.sleep(attempt_number * delay)
            return self.request_page(
                method,
                path,
                params,
                data,
                attempt_number + 1,
                max_attempts,
                delay,
            )

        return result

    def get_study_plan_ids(self) -> List[str]:
        page = self.request_page(
            "get", "TP/Tziunim_P.aspx", params={"src": "", "sys": "tal", "rightmj": 1}
        )
        form_element = page.find("form", {"name": "frmfree"})
        return [
            input_element["value"]
            for input_element in form_element.find_all("input", {"name": "tckey"})
        ]

    def get_grades(self, study_plan_id: str, years: List[int]) -> List[GradeInfo]:
        results = []
        first_page = self.request_page(
            "post",
            "TP/Tziunim_L.aspx",
            params={"src": "", "sys": "tal", "rightmj": 1, "first": "yes", "lang": ""},
            data={
                "tckey": study_plan_id,
                "btnishur.x": 59,
                "btnishur.y": 15,
                "caller": "tziunim_p",
                "peula": 3,
                "javas": 1,
                "h_eng": "",
            },
        )

        for year in years:
            page = self.request_page(
                "post",
                "TP/Tziunim_L.aspx",
                params={
                    "src": "",
                    "sys": "tal",
                    "rightmj": 1,
                    "first": "yes",
                    "lang": "",
                },
                data={
                    "__VIEWSTATE": first_page.find("input", {"id": "__VIEWSTATE"})[
                        "value"
                    ],
                    "__VIEWSTATEGENERATOR": first_page.find(
                        "input", {"id": "__VIEWSTATEGENERATOR"}
                    )["value"],
                    "__EVENTVALIDATION": first_page.find(
                        "input", {"id": "__EVENTVALIDATION"}
                    )["value"],
                    "lstSem": str(year - 1) + "9",
                    "old_sem": str(year - 1) + "2",
                    "peula": "",
                    "javas": 1,
                },
            )

            table = page.find("form").find("table")
            for row in table.find_all("tr"):
                cells = row.find_all("td")
                if len(cells) != 13:
                    continue
                cells = [cell.text for cell in cells]

                semester = str(year) + ("a" if cells[0] == "א" else "b")
                course_id = cells[1].replace("-", "")
                grade = "".join([c for c in cells[5] if c.isnumeric()])
                notes = cells[11]

                if grade != "" or notes != "":
                    results.append(
                        GradeInfo(
                            semester,
                            course_id,
                            None if grade == "" else int(grade),
                            "פטור" in notes,
                        )
                    )

        return results

    def get_all_grades(self, years: List[int]) -> List[GradeInfo]:
        result = set()

        study_plan_ids = self.get_study_plan_ids()
        for study_plan_id in study_plan_ids:
            study_plan_grades = self.get_grades(study_plan_id, years)
            result.update(study_plan_grades)

        return list(result)
