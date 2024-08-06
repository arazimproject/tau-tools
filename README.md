<h1 align="center">
    🎓 TAU Tools
    <br />
    <img src="https://img.shields.io/badge/updated-2024-purple.svg">
    <img src="https://img.shields.io/pypi/v/tau-tools">
    <img src="https://img.shields.io/badge/license-MIT-blue.svg">
    <img src="https://img.shields.io/badge/PRs-welcome-brightgreen.svg">
    <img src="https://img.shields.io/badge/tau-unofficial-red.svg">
</h1>

<p align="center">
    <b>A python library to retrieve information about the various plans and courses at Tel Aviv University, and interact with the various servers.</b>
</p>

<p align="center">
    🛠️ <a href="#installation">Installation</a>
    &nbsp;&middot&nbsp;
    💡 <a href="#features">Features</a>
    &nbsp;&middot&nbsp;
    🚗 <a href="#roadmap">Roadmap</a>
</p>

# Installation

You can get the latest version of TAU Tools by running `pip install tau-tools`!

# Features

### Moodle API

Here's an example of using the TAU Tools moodle package:

```python
from tau_tools.moodle import Moodle

m = Moodle("username", "123456789", "password", "session.json")
courses = m.get_courses()
print(courses)
print(m.get_recordings(courses[0]))
```

Full documentation will be available soon!

## Scrapers

You can get mostly up to date data from the following URLs:

-   https://arazim-project.com/courses/2025a.json
-   https://arazim-project.com/courses/2025b.json
-   https://arazim-project.com/courses/plans.json

### Get course details

You can get all details about a specific year's courses by running `python3 -m tau_tools.courses` or `python3 -m tau_tools.courses 2025`!

Example:

```json
{
    "03005031": {
        "name": "מבוא לביולוגיה לכימאים",
        "faculty": "מדעים מדויקים/פקולטה למדעים מדויקים",
        "exams": [
            {
                "moed": "א",
                "date": "08/02/2024",
                "hour": "",
                "type": "בחינה סופית"
            },
            ...
        ],
        "groups": [
            {
                "group": "01",
                "lecturer": "ד\"ר מאיו ליאור",
                "lessons": [
                    {
                        "day": "ה",
                        "time": "09:00-10:00",
                        "building": "קפלון",
                        "room": "118",
                        "type": "שיעור"
                    },
                    ...
                ]
            },
            ...
        ]
    },
    ...
}
```

### Get the available plans

You can get all details about the current (and past) study plans in Tel Aviv University by running `python3 -m tau_tools.plans` or `python3 -m tau_tools.plans 2025`!

Example:

```json
{
    "הפקולטה למדעי החברה ע\"ש גרשון גורדון": {
        "תוכנית לתואר שני בתקשורת במסלול מחקרי": {
            "קורסי תואר שני - קורסי ליבה": ["10854101", "10854102"],
            "קורסי תואר שני - קורסי מתודולוגיה": ["10854203", "10464101"],
            ...
        },
        ...
    },
    ...
}
```

# Roadmap

-   [x] Get courses
-   [x] Get plans
-   [ ] Create a nicer interface to the IMS
-   [x] Create a nicer interface to the Moodle
-   [ ] Make the scripts accept command-line parameters
-   [x] Add the package to PyPI for a simpler installation
-   [x] Show progress bars during scraping

# Acknowledgements

This repository contains modified versions of the following tools:

-   [CourseScrape](https://github.com/TAUHacks/CourseScrape)
