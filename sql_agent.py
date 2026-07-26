import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from groq import Groq

load_dotenv()  # reads GROQ_API_KEY and DATABASE_URL from .env

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
engine = create_engine(os.getenv("DATABASE_URL"))

# This describes your actual database schema to the LLM, so it knows what tables/columns exist
SCHEMA_DESCRIPTION = """
Table: matches
Columns: match_id (text), gender (text: 'male' or 'female'), date (date),
venue (text), city (text), toss_winner (text), toss_decision (text),
winner (text), match_type (text), team1 (text), team2 (text)

Table: deliveries
Columns: match_id (text), gender (text), inning (int), batting_team (text),
over (int, 0-indexed so over 0 = first over, powerplay = over < 6, death overs = over >= 15),
ball (int), batter (text), bowler (text), non_striker (text), runs_batter (int),
runs_extras (int), runs_total (int), wicket (boolean), dismissal_kind (text),
player_out (text)

Important domain conventions to follow:
1. Strike rate = (SUM(runs_batter) * 100.0 / COUNT(*)) — always multiply by 100, it's a percentage.
2. Economy rate = (SUM(runs_total) * 6.0 / COUNT(*)) — runs conceded per 6 balls (one over).
3. Always filter out small, unreliable samples using HAVING:
   - For batting stats: HAVING COUNT(*) >= 60 (minimum balls faced)
   - For bowling stats: HAVING COUNT(*) >= 30 (minimum balls bowled)
4. Powerplay = over < 6. Death overs = over >= 15.
"""

def generate_sql(question: str) -> str:
    prompt = f"""You are a SQL expert for a cricket statistics database.

Database schema:
{SCHEMA_DESCRIPTION}

Given this question, write ONE PostgreSQL query that answers it.
Rules:
- Return ONLY the SQL query, no explanation, no markdown formatting, no ```sql``` fences.
- Always end with a semicolon.
- If the question doesn't specify gender, don't filter by gender.
- Always apply the minimum sample size filters described above using HAVING when aggregating player stats.
- Use LIMIT 10 unless the question asks for a specific number of results.

Question: {question}

SQL query:"""

    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    sql = response.choices[0].message.content.strip()
    sql = sql.replace("```sql", "").replace("```", "").strip()
    return sql

def run_sql_query(question: str):
    """Full pipeline: question -> SQL -> execute -> results"""
    sql = generate_sql(question)
    print(f"[Generated SQL]: {sql}\n")

    try:
        with engine.connect() as conn:
            result = conn.execute(text(sql))
            rows = result.fetchall()
            columns = result.keys()
        return columns, rows
    except Exception as e:
        return None, f"SQL execution error: {e}"

if __name__ == "__main__":
    # Quick manual test
    question = "Who scored the most runs in powerplay overs for men's matches?"
    columns, rows = run_sql_query(question)
    print(columns)
    for row in rows:
        print(row)