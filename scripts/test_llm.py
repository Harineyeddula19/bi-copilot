from copilot.llm import generate_sql

questions = [
    "How many employees are in Sales?",
    "Which department has the highest attrition rate?",
    "Delete all resigned employees",
]
for q in questions:
    print("\nQ:", q)
    print(generate_sql(q))