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

### IMS API

Here's an example of using the TAU Tools ims package:

```python
from tau_tools.ims import IMS

ims = IMS("username", "123456789", "password")
grades = ims.get_all_grades([2023, 2024])
print(grades)
```

## Lobby Dashboard

You can get information about exams happening today by running `python3 -m tau_tools.lobby_dashboard`.

Example:

```python
[
    ExamInfo(
        course_id='03682162',
        course_name='מערכות הפעלה',
        group='08',
        semester=2,
        start_hour='09:00',
        end_hour='12:00',
        building="אודיטור' לב",
        room='009',
        surname_letters='א - ד'
    ),
    ...
]
```

## Scrapers

You can get mostly up to date data from the following URLs:

-   https://arazim-project.com/courses/courses-2025a.json
-   https://arazim-project.com/courses/courses-2025b.json
-   https://arazim-project.com/courses/plans.json

You can also get rolled-up information about all of the courses in https://arazim-project.com/courses/courses.json, using the [collect](#collect-the-data-together) script.

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

### Get the Moodle exam bank

You can get links to all of the exams hosted on Moodle (copying the exams themselves is prohibited) by running `python3 -m tau_tools.moodle_exams`!

Example:

```json
{
    {
        "results": [
            [
                "0321-1100-אלגברה לינארית לפיז-מועד א.pdf",
                "https://moodle.tau.ac.il/pluginfile.php/421164/mod_folder/content/0/0321-1100-%D7%90%D7%9C%D7%92%D7%91%D7%A8%D7%94%20%D7%9C%D7%99%D7%A0%D7%90%D7%A8%D7%99%D7%AA%20%D7%9C%D7%A4%D7%99%D7%96-%D7%9E%D7%95%D7%A2%D7%93%20%D7%90.pdf"
            ],
            ...
        ],
        "year": 2024
    },
    ...
}
```

### Collect the data together

Running `python3 -m tau_tools.collect` will go over all courses and moodle exams JSONs in the current directory and place the moodle exam data into the courses jsons. It also creates a summary `courses.json` which contains rolled-up information from all of the courses jsons.

An optional `corrections.json` file is available to account for errors in the moodle exam bank.

The current corrections are:

```json
{
    "03514321": "03514312",
    "03662016": "03662106",
    "03211110": "03211100",
    "032121012": "03213101",
    "03683035": "03683058",
    "03664841": "03724841",
    "03724453": "03724553",
    "03513118": "03653118",
    "03664041": "03684041",
    "03651105": "03681105",
    "03684229": "03684429",
    "03214308": "03213804",
    "03664117": "03214117",
    "03664127": "03214127"
}
```

# Roadmap

-   [x] Get courses
-   [x] Get plans
-   [x] Create a nicer interface to the IMS
-   [x] Create a nicer interface to the Moodle
-   [ ] Make the scripts accept command-line parameters
-   [x] Add the package to PyPI for a simpler installation
-   [x] Show progress bars during scraping

# Acknowledgements

This repository contains modified versions of the following tools:

-   [CourseScrape](https://github.com/TAUHacks/CourseScrape)
-   [CLIMS](https://github.com/TAUHacks/clims)
