# Maintaining Instructions

When modifying [types.ts](./types.ts), make sure to re-generate the json schemas by running:

```
bunx typescript-json-schema types.ts AllTimeCourses > schema/all_time_courses.schema.json
bunx typescript-json-schema types.ts SemesterCourses > schema/semester_courses.schema.json
bunx typescript-json-schema types.ts SemesterPlans > schema/semester_plans.schema.json
bunx typescript-json-schema types.ts GeneralInfo > schema/general_info.schema.json
```
