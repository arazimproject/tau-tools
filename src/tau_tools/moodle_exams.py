import json
import time

from rich.prompt import Prompt

from tau_tools.logging import console, log, progress, setup_logging
from tau_tools.moodle import Moodle

EXAM_COURSE_PAGE_ID = 5800030001


def main(output_file="moodle-exams.json"):
    username = Prompt.ask("Enter your Moodle username", console=console)
    id = Prompt.ask("Enter your ID", console=console)
    password = Prompt.ask("Enter your Moodle password", console=console)

    with console.status("Signing in to Moodle..."):
        m = Moodle(username, id, password)

    with console.status("Fetching exams course page..."):
        exam_course_page = m.get_page(EXAM_COURSE_PAGE_ID)

    year_links = [
        year_link
        for year_link in exam_course_page.find_all("a", {"class": "nav-link"})
        if "href" in year_link.attrs
        and "title" in year_link.attrs
        and year_link["title"].isnumeric()
        and int(year_link["title"]) >= 2000
    ]
    results = []
    log.info(f"Found year links {year_links}")
    with progress:
        years_task_id = progress.add_task(
            "[purple]Fetching years...", total=len(year_links)
        )
        for year_link in year_links:
            year = int(year_link["title"]) + 1
            year_results = []

            exams_year_page = m.get_page(
                page_url=year_link["href"].replace("§ionid", "&sectionid")
            )

            schools = [
                school
                for school in exams_year_page.find_all(
                    "li", {"class": "course-section"}
                )
                # This is just the folder itself
                if not school.find("h3", {"class": "sectionname"})
                .text.strip()
                .isnumeric()
            ]
            schools_task_id = progress.add_task(
                "[blue]Fetching schools...", total=len(schools)
            )
            for school in schools:
                school_name = school.find("h3", {"class": "sectionname"}).text.strip()
                log.info(f"Fetching folders in {school_name}")

                folders = [
                    folder_link
                    for folder_link in school.find_all("a")
                    if "/folder/" in folder_link["href"]
                ]
                folders_task_id = progress.add_task(
                    "[green]Fetching folders...", total=len(folders)
                )
                for folder_index, folder_link in enumerate(folders):
                    print("\t\tFetching folder", f"[{folder_index+1}/{len(folders)}]")
                    folder = m.get_page(page_url=folder_link["href"]).find(
                        "div", {"class": "filemanager"}
                    )
                    for exam_link in folder.find_all("a"):
                        year_results.append((exam_link.text, exam_link["href"]))

                    time.sleep(1)
                    progress.update(folders_task_id, advance=1)
                progress.update(folders_task_id, visible=False)

                time.sleep(1)
                progress.update(schools_task_id, advance=1)
            progress.update(schools_task_id, visible=False)

            results.append({"results": year_results, "year": year})
            progress.update(years_task_id, advance=1)

    with open(output_file, "w") as f:
        json.dump(results, f, ensure_ascii=False)


if __name__ == "__main__":
    setup_logging()
    main()
