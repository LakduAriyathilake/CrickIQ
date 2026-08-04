import os
import re
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from groq import Groq, RateLimitError

load_dotenv()  # reads GROQ_API_KEY and DATABASE_URL from .env

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
engine = create_engine(os.getenv("DATABASE_URL"))

# This describes your actual database schema to the LLM, so it knows what tables/columns exist
SCHEMA_DESCRIPTION = """
SCHEMA (STRICT — each column belongs ONLY to the table listed. Never mix columns
across tables):

Table: matches
Columns: match_id (text), gender (text: 'male' or 'female'), date (date),
venue (text), city (text), toss_winner (text), toss_decision (text),
winner (text), match_type (text — ALWAYS 'T20', carries no stage/round info), team1 (text), team2 (text)

Table: deliveries
Columns: match_id (text), gender (text), inning (int), batting_team (text),
over (int, 0-indexed so over 0 = first over, powerplay = over < 6, death overs = over >= 15),
ball (int), batter (text), bowler (text), non_striker (text), runs_batter (int),
runs_extras (int), runs_total (int), wicket (boolean), dismissal_kind (text),
player_out (text)

CRITICAL SCOPE RULE:
This database contains ONLY ICC Men's and Women's T20 World Cup matches. There is
no ODI, Test, or IPL data. The "match_type" column on `matches` is ALWAYS the
literal value 'T20' — it does NOT distinguish group stage, semi-final, or final,
and no such stage/round column exists anywhere in this schema. NEVER filter or
match on match_type as if it identifies a stage (e.g. WHERE match_type = 'Final'
is always wrong and will return zero rows). match_type also does NOT exist on
`deliveries` at all.

If the question asks about a tournament/format other than the T20 World Cup
(e.g. ODI, IPL, Test), OR references any player/team/stat that would require a
column not listed above, generate exactly this and nothing else:
SELECT 'not_covered' AS result WHERE 1=0;
This guarantees an empty, safe result instead of a broken or wrong-table query.

TOURNAMENT WINNER queries (e.g. "who won the 2024 T20 World Cup"):
Since match_type cannot identify the final, use this proxy instead: filter matches
by date range for the year (and gender, if specified), then take the winner of the
LAST match by date within that range — that match is the final.
Example: "Who won the 2024 Men's T20 World Cup?" →
SELECT winner FROM matches
WHERE date >= '2024-01-01' AND date < '2025-01-01' AND gender = 'male'
ORDER BY date DESC LIMIT 1;
Note: some years have BOTH a men's and women's tournament. If gender isn't
specified in the question, return the latest match for EACH gender separately
(two rows, labeled by gender) rather than guessing one.

Important domain conventions to follow:
1. Strike rate = (SUM(runs_batter) * 100.0 / COUNT(*)) — always multiply by 100, it's a percentage.
2. Economy rate = (SUM(runs_total) * 6.0 / COUNT(*)) — runs conceded per 6 balls (one over).
3. Sample-size filters (HAVING) — apply for ANY season-wide or tournament-wide
   aggregate, including a single player's stats across a full tournament or across
   the whole dataset (e.g. "best strike rate overall", "Kohli's strike rate in the
   2026 World Cup", "best economy rate in death overs across the tournament"):
   - For batting stats: HAVING COUNT(*) >= 60 (minimum balls faced)
   - For bowling stats: HAVING COUNT(*) >= 30 (minimum balls bowled)
   For NARROW-scope questions — a single over, a single match, a specific inning —
   OMIT the HAVING filter entirely, since the natural sample size is already small
   (6-9 balls per over) and a 60-ball minimum can never be satisfied.
   Example: "best strike rate in powerplay" → tournament-wide → keep HAVING.
   Example: "best strike rate in the last over" → single-over scope → omit HAVING.
   Example: "Mandhana's strike rate in the 2026 World Cup" → tournament-wide → keep HAVING.
4. Powerplay = over < 6. Death overs = over >= 15.
5. TEAM HEAD-TO-HEAD queries ONLY — i.e. the question explicitly compares two
   named TEAMS against each other (e.g. "head to head between India and Pakistan"):
   normalize using LEAST(team1, team2) and GREATEST(team1, team2) in the SELECT
   and GROUP BY on the `matches` table, so both teams' matches aggregate into a
   single row regardless of which was team1/team2 originally.

   GENDER SPLIT: unless the question explicitly specifies "men's" or "women's",
   ALWAYS also GROUP BY gender and include it as a column in the SELECT, so
   men's and women's results appear as separate rows. Mixing men's and women's
   matches into one combined row is misleading, since they are different
   competitions with different teams and players.

   Example — "head to head between India and Sri Lanka" (no gender specified):
   SELECT gender,
          LEAST(team1, team2) AS team1, GREATEST(team1, team2) AS team2,
          COUNT(CASE WHEN winner = LEAST(team1, team2) THEN 1 END) AS team1_wins,
          COUNT(CASE WHEN winner = GREATEST(team1, team2) THEN 1 END) AS team2_wins,
          COUNT(CASE WHEN winner IS NULL THEN 1 END) AS draws
   FROM matches
   WHERE (team1 = 'India' AND team2 = 'Sri Lanka') OR (team1 = 'Sri Lanka' AND team2 = 'India')
   GROUP BY gender, LEAST(team1, team2), GREATEST(team1, team2);

   Example — "head to head between India and Pakistan in men's matches" (gender specified):
   omit the gender GROUP BY/column entirely, and add WHERE gender = 'male' instead,
   since the question already scoped it.

   Do NOT apply LEAST/GREATEST team grouping to PLAYER statistic queries (batting
   or bowling stats), even if the query joins `matches` and `deliveries`. Player
   leaderboard questions (e.g. "best strike rate in powerplay", "best economy in
   death overs", "Kohli's strike rate") must GROUP BY batter or bowler — NEVER
   by team1/team2 — since the question is about individual performance, not a
   team matchup. If a query needs to join matches (for gender/date filters) with
   deliveries (for batter/bowler stats), still GROUP BY the player column only.
6. When a "who won" question doesn't specify gender and the year could have both
   a men's and women's tournament, use a UNION ALL of two independently-ordered
   subqueries. CRITICAL: each branch MUST be individually wrapped in parentheses
   — PostgreSQL requires this whenever a branch has its own ORDER BY / LIMIT, and
   omitting the parentheses causes a guaranteed SQL syntax error.

   WRONG (missing parentheses — will always fail with a syntax error):
   SELECT 'male' AS gender, winner FROM matches WHERE ... ORDER BY date DESC LIMIT 1
   UNION ALL
   SELECT 'female' AS gender, winner FROM matches WHERE ... ORDER BY date DESC LIMIT 1;

   CORRECT (each branch wrapped in parentheses):
   (SELECT 'male' AS gender, winner FROM matches
    WHERE date >= '2024-01-01' AND date < '2025-01-01' AND gender = 'male'
    ORDER BY date DESC LIMIT 1)
   UNION ALL
   (SELECT 'female' AS gender, winner FROM matches
    WHERE date >= '2024-01-01' AND date < '2025-01-01' AND gender = 'female'
    ORDER BY date DESC LIMIT 1);

   Always double-check before finalizing: does every SELECT branch that has its
   own ORDER BY or LIMIT sit inside its own parentheses? If not, add them.
7. PLAYER NAME MATCHING: Player names in this database are stored in initials +
   surname format (e.g. "S Mandhana", not "Smriti Mandhana"). Users will often type
   full first names, nicknames, or slightly different spellings. NEVER use exact
   equality (=) for player name filters. Instead always use a partial, case-insensitive
   match on the surname:

   WHERE batter ILIKE '%mandhana%'

   This matches regardless of how the first name/initials are typed, and is
   case-insensitive so capitalization differences don't cause misses.
8. PLAYER + YEAR/TOURNAMENT FILTERS: When a question asks about a player's stats in
   a specific year or tournament (e.g. "Smriti Mandhana's strike rate in the 2026
   World Cup"), join deliveries to matches on match_id, then filter matches.date to
   that year's range, in addition to the ILIKE name filter on batter. Since this is
   a tournament-wide aggregate, keep the HAVING sample-size filter from rule 3:

   SELECT d.batter, (SUM(d.runs_batter) * 100.0 / COUNT(*)) AS strike_rate
   FROM deliveries d
   JOIN matches m ON d.match_id = m.match_id
   WHERE d.batter ILIKE '%mandhana%'
     AND m.date >= '2026-01-01' AND m.date < '2027-01-01'
   GROUP BY d.batter
   HAVING COUNT(*) >= 60;

   If the question asks about a player ACROSS MULTIPLE YEARS or the whole dataset
   (no year mentioned), omit the date filter and join, query deliveries alone, but
   still keep the HAVING filter and GROUP BY batter.
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
- Apply the minimum sample size filters (HAVING) ONLY as described in schema rule 3 above —
  season-wide/tournament-wide aggregates get the filter, narrow-scope queries (single over,
  single match, single inning) must OMIT it.
- Use LIMIT 10 unless the question asks for a specific number of results.

Question: {question}

SQL query:"""

    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
    except RateLimitError:
        # Signal the rate limit up to run_sql_query rather than letting the
        # exception crash the whole Streamlit app with a raw traceback.
        return "RATE_LIMIT_EXCEEDED"

    sql = response.choices[0].message.content.strip()
    sql = sql.replace("```sql", "").replace("```", "").strip()

    # Defensive fix: if a UNION/UNION ALL query has branches with their own
    # ORDER BY/LIMIT but isn't wrapped in parentheses, Postgres will reject it
    # with a syntax error. The schema rule tells the LLM to always parenthesize,
    # but this has proven to be an intermittent omission even with an explicit
    # rule, so this patches the exact two-branch UNION ALL pattern as a safety
    # net rather than relying on the prompt alone.
    if "UNION" in sql.upper() and not sql.strip().startswith("("):
        parts = re.split(r'\bUNION ALL\b', sql, flags=re.IGNORECASE)
        if len(parts) == 2:
            left = parts[0].strip().rstrip(';').strip()
            right = parts[1].strip().rstrip(';').strip()
            if not left.startswith("(") and not right.startswith("("):
                sql = f"({left})\nUNION ALL\n({right});"

    return sql

def run_sql_query(question: str):
    """Full pipeline: question -> SQL -> execute -> results"""
    sql = generate_sql(question)
    print(f"[Generated SQL]: {sql}\n")

    if sql == "RATE_LIMIT_EXCEEDED":
        return None, "RATE_LIMIT: Groq API rate limit reached — please try again in a few minutes."

    try:
        with engine.connect() as conn:
            result = conn.execute(text(sql))
            rows = result.fetchall()
            columns = result.keys()
        return columns, rows
    except Exception as e:
        return None, f"SQL execution error: {e}"

if __name__ == "__main__":
    test_questions = [
        "Best strike rate in powerplay for men's matches",   # Bug F check
        "Best economy rate in death overs",                   # Bug F check
        "Who won the 2024 Men's T20 World Cup?",              # Bug E check
        "Who won the 2024 Women's T20 World Cup?",             # Bug E check
        "Who won the 2024 T20 World Cup?",                     # Bug E/G, gender-unspecified + parentheses check
        "Head to head between India and Pakistan",             # Bug D regression check
    ]

    for q in test_questions:
        print(f"\n{'='*60}")
        print(f"QUESTION: {q}")
        print('='*60)
        columns, rows = run_sql_query(q)
        print(columns)
        if isinstance(rows, str):  # error case
            print(rows)
        else:
            for row in rows:
                print(row)