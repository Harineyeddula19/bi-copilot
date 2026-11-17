from copilot.llm import generate_sql
from copilot.runner import run_sql

for q in ["How many employees are in Sales?",
          "Which department has the highest attrition rate?"]:
    sql = generate_sql(q)
    print("\nQ:", q)
    print(sql)
    print(run_sql(sql))