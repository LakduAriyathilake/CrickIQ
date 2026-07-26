import os
from dotenv import load_dotenv
from groq import Groq

from sql_agent import run_sql_query
from rag_agent import answer_from_knowledge

load_dotenv()
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def classify_question(question: str) -> str:
    """
    Ask the LLM to classify the question as either:
    - 'STATS' -> needs a database query (player performance, scores, records)
    - 'RULES' -> needs conceptual/rules knowledge (how does X work, what is Y)
    """
    prompt = f"""Classify the following cricket question into exactly ONE category:

STATS - questions about specific player statistics, match results, scores,
        records, or anything that requires looking up numbers from a database
        (e.g. "who scored the most runs", "best bowling economy", "head to head record")

RULES - questions about how cricket concepts, rules, or terminology work
        (e.g. "what is DLS", "how does a super over work", "explain reverse swing")

Question: {question}

Respond with ONLY one word: STATS or RULES"""

    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    classification = response.choices[0].message.content.strip().upper()
    return classification

def route_question(question: str):
    """Full router: classify, then call the right agent."""
    category = classify_question(question)
    print(f"[Router classified as]: {category}\n")

    if "STATS" in category:
        columns, rows = run_sql_query(question)
        if rows is None:
            return f"Error: {rows}"
        result_text = "\n".join(str(row) for row in rows)
        return f"Columns: {list(columns)}\n{result_text}"
    else:
        return answer_from_knowledge(question)

if __name__ == "__main__":
    test_questions = [
        "Who has the best economy rate in death overs?",
        "What is the DLS method?",
        "How does a super over work?",
        "Best strike rate in powerplay for women's matches",
    ]

    for q in test_questions:
        print(f"Q: {q}")
        answer = route_question(q)
        print(f"A: {answer}")
        print("=" * 60)