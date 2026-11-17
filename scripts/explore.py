import sqlite3
import pandas as pd

con = sqlite3.connect("file:data/hr.db?mode=ro", uri=True)

def show(title, sql):
    print("\n" + title)
    print(pd.read_sql_query(sql, con).to_string(index=False))

show("1. Employees per department", """
SELECT d.department_name, COUNT(*) AS employees
FROM employees e JOIN departments d USING(department_id)
GROUP BY d.department_name ORDER BY employees DESC""")

show("2. Total resigned and overall attrition %", """
SELECT SUM(resigned) AS resigned, ROUND(100.0*AVG(resigned),2) AS attrition_pct
FROM employees""")

show("3. Attrition % by department", """
SELECT d.department_name, ROUND(100.0*AVG(e.resigned),2) AS attrition_pct
FROM employees e JOIN departments d USING(department_id)
GROUP BY d.department_name ORDER BY attrition_pct DESC""")

show("4. Average monthly salary by job title", """
SELECT j.job_title, ROUND(AVG(c.monthly_salary),2) AS avg_salary
FROM employees e JOIN jobs j USING(job_id)
JOIN compensation c USING(employee_id)
GROUP BY j.job_title ORDER BY avg_salary DESC""")

show("5. Hires per year", """
SELECT strftime('%Y', hire_date) AS year, COUNT(*) AS hires
FROM employees GROUP BY year ORDER BY year""")

show("6. Top department by satisfaction among performance-5 employees", """
SELECT d.department_name, ROUND(AVG(p.satisfaction_score),2) AS avg_satisfaction
FROM employees e JOIN departments d USING(department_id)
JOIN performance p USING(employee_id)
WHERE p.performance_score = 5
GROUP BY d.department_name ORDER BY avg_satisfaction DESC LIMIT 1""")

con.close()