"""Split HR_Analytics_Cleaned.xlsx into 6 related SQLite tables."""
import sqlite3
from pathlib import Path
import pandas as pd

SRC = Path("data/HR_Analytics_Cleaned.xlsx")
DB = Path("data/hr.db")

df = pd.read_excel(SRC, sheet_name="Employee_Data")

# Drop pre-made bucket columns: the copilot must derive them itself.
df = df.drop(columns=["Age_Group", "Tenure_Group", "Salary_Band",
                      "Overtime_Category", "Performance_Category", "Resigned_Flag"])
df["Resigned"] = df["Resigned"].astype(int)
df["Hire_Date"] = pd.to_datetime(df["Hire_Date"]).dt.strftime("%Y-%m-%d")

departments = df[["Department"]].drop_duplicates().sort_values("Department").reset_index(drop=True)
departments.insert(0, "department_id", departments.index + 1)
departments.columns = ["department_id", "department_name"]

jobs = df[["Job_Title"]].drop_duplicates().sort_values("Job_Title").reset_index(drop=True)
jobs.insert(0, "job_id", jobs.index + 1)
jobs.columns = ["job_id", "job_title"]

d = df.merge(departments, left_on="Department", right_on="department_name") \
      .merge(jobs, left_on="Job_Title", right_on="job_title")

employees = d[["Employee_ID", "Gender", "Age", "Education_Level", "Hire_Date",
               "Years_At_Company", "department_id", "job_id", "Resigned"]].copy()
employees.columns = ["employee_id", "gender", "age", "education_level", "hire_date",
                     "years_at_company", "department_id", "job_id", "resigned"]

compensation = d[["Employee_ID", "Monthly_Salary", "Promotions"]].copy()
compensation.columns = ["employee_id", "monthly_salary", "promotions"]

performance = d[["Employee_ID", "Performance_Score", "Projects_Handled",
                 "Training_Hours", "Employee_Satisfaction_Score"]].copy()
performance.columns = ["employee_id", "performance_score", "projects_handled",
                       "training_hours", "satisfaction_score"]

work_patterns = d[["Employee_ID", "Work_Hours_Per_Week", "Overtime_Hours",
                   "Sick_Days", "Remote_Work_Frequency", "Team_Size"]].copy()
work_patterns.columns = ["employee_id", "work_hours_per_week", "overtime_hours",
                         "sick_days", "remote_work_percent", "team_size"]

DB.unlink(missing_ok=True)
con = sqlite3.connect(DB)
con.executescript("""
CREATE TABLE departments (department_id INTEGER PRIMARY KEY, department_name TEXT NOT NULL);
CREATE TABLE jobs (job_id INTEGER PRIMARY KEY, job_title TEXT NOT NULL);
CREATE TABLE employees (
  employee_id INTEGER PRIMARY KEY, gender TEXT, age INTEGER, education_level TEXT,
  hire_date TEXT, years_at_company INTEGER,
  department_id INTEGER REFERENCES departments(department_id),
  job_id INTEGER REFERENCES jobs(job_id),
  resigned INTEGER CHECK (resigned IN (0,1)));
CREATE TABLE compensation (employee_id INTEGER PRIMARY KEY REFERENCES employees(employee_id),
  monthly_salary INTEGER, promotions INTEGER);
CREATE TABLE performance (employee_id INTEGER PRIMARY KEY REFERENCES employees(employee_id),
  performance_score INTEGER, projects_handled INTEGER, training_hours INTEGER,
  satisfaction_score REAL);
CREATE TABLE work_patterns (employee_id INTEGER PRIMARY KEY REFERENCES employees(employee_id),
  work_hours_per_week INTEGER, overtime_hours INTEGER, sick_days INTEGER,
  remote_work_percent INTEGER, team_size INTEGER);
""")
for name, frame in [("departments", departments), ("jobs", jobs), ("employees", employees),
                    ("compensation", compensation), ("performance", performance),
                    ("work_patterns", work_patterns)]:
    frame.to_sql(name, con, if_exists="append", index=False)
con.executescript("""
CREATE INDEX idx_emp_dept ON employees(department_id);
CREATE INDEX idx_emp_job ON employees(job_id);
CREATE INDEX idx_emp_resigned ON employees(resigned);
""")
con.commit()

for t in ["departments", "jobs", "employees", "compensation", "performance", "work_patterns"]:
    print(t, con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0])
orph = con.execute("""SELECT COUNT(*) FROM employees e
  LEFT JOIN departments d USING(department_id) LEFT JOIN jobs j USING(job_id)
  WHERE d.department_id IS NULL OR j.job_id IS NULL""").fetchone()[0]
print("orphaned employees:", orph)
assert len(employees) == len(df) == 100000 and orph == 0
con.close(); print("OK")