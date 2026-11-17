import os
import re
from dotenv import load_dotenv
from openai import OpenAI
from .prompt import SCHEMA_DOC

load_dotenv()
client = OpenAI(base_url=os.getenv("LLM_BASE_URL"), api_key=os.getenv("LLM_API_KEY"))
MODEL = os.getenv("LLM_MODEL")


def _clean(text: str) -> str:
    """Remove markdown fences and trailing semicolons from the model's reply."""
    text = (text or "").strip()
    m = re.search(r"```(?:sql)?\s*(.*?)```", text, re.S | re.I)
    if m:
        text = m.group(1)
    return text.strip().rstrip(";").strip()


def generate_sql(question, previous_sql=None, error=None):
    messages = [{"role": "system", "content": SCHEMA_DOC},
                {"role": "user", "content": question}]
    if previous_sql:
        messages += [
            {"role": "assistant", "content": previous_sql},
            {"role": "user", "content":
                f"That query failed with this error: {error}\n"
                "Return a corrected single SELECT only."},
        ]
    r = client.chat.completions.create(model=MODEL, messages=messages, temperature=0)
    return _clean(r.choices[0].message.content)