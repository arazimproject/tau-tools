<h1 align="center">
    🎓 TAU Tools
    <br />
    <img src="https://img.shields.io/badge/updated-2024-purple.svg">
    <img src="https://img.shields.io/badge/license-MIT-blue.svg">
    <img src="https://img.shields.io/badge/PRs-welcome-brightgreen.svg">
    <img src="https://img.shields.io/badge/tau-unofficial-red.svg">
</h1>

<p align="center">
    <b>A python library to retrieve information about the various plans and courses at Tel Aviv University, and interact with the various servers.</b>
</p>

<p align="center">
    💡 <a href="#features">Features</a>
    &nbsp;&middot&nbsp;
    🚶‍♂️ <a href="#getting-started">Getting Started</a>
    &nbsp;&middot&nbsp;
    🚗 <a href="#roadmap">Roadmap</a>
</p>

You can get mostly up to date data from the following URLs:

-   https://arazim-project.com/courses/2024a.json
-   https://arazim-project.com/courses/2024b.json
-   https://arazim-project.com/courses/plans.json

# Features

### Get course details

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

# Getting Started

## Dependencies

You will need to install the following packages: `pip install requests beautifulsoup4 colorama`.

Afterwards, you can simply clone the repository (or download the code), then run the available scripts in `tau_tools` using Python 3, e.g. `python3 courses.py`.

This will create a JSON with the result in your current directory.

# Roadmap

-   [x] Get courses
-   [x] Get plans
-   [ ] Create a nicer interface to the IMS
-   [ ] Create a nicer interface to the Moodle
-   [ ] Make the scripts accept command-line parameters
-   [ ] Add the package to PyPI for a simpler installation

# Acknowledgements

This repository contains modified versions of the following tools:

-   [CourseScrape](https://github.com/TAUHacks/CourseScrape)
