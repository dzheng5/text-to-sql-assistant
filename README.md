# Ask Your Data — Text-to-SQL CSV Assistant

A Streamlit app that lets you upload a CSV and ask questions about it in plain English. A LangChain SQL agent inspects the data, writes the SQL query, runs it, and returns an answer — along with the exact SQL it used.

## How it works
Upload CSV → DuckDB (in-memory table) → LangChain SQL Agent → Groq (Llama 3.3 70B) → Answer + SQL

1. You upload a CSV file.
2. The app loads it into a local DuckDB table, automatically cleaning column names.
3. You type a question in the chatbox (e.g. "What's the total revenue by region?").
4. A LangChain SQL agent inspects the table schema, writes a SQL query, and runs it against DuckDB.
5. The answer is shown in plain English, with an expandable section showing the exact SQL that was run.

## Tech stack

- **Frontend**: Streamlit
- **Database**: DuckDB (in-memory, per-session)
- **Agent orchestration**: LangChain (SQL Agent Toolkit)
- **LLM**: Llama 3.3 70B via Groq

## Setup

1. Clone the repo and create a virtual environment:

\`\`\`bash
git clone https://github.com/dzheng5/text-to-sql-assistant.git
cd text-to-sql-assistant
python -m venv venv
venv\\Scripts\\activate   # on Windows
source venv/bin/activate  # on Mac/Linux
\`\`\`

2. Install dependencies:

\`\`\`bash
pip install -r requirements.txt
\`\`\`

3. Get a free Groq API key from [console.groq.com](https://console.groq.com), then create a `.env` file in the project root:

\`\`\`
GROQ_API_KEY=your_key_here
\`\`\`

4. Run the app:

\`\`\`bash
streamlit run app.py
\`\`\`

## Try it out

A sample dataset, `sample_sales.csv`, is included in this repo — 100 rows of sales data across 10 customers, 5 products, and 4 regions throughout 2024. Upload it and try questions like:

- "What's the total revenue by region?"
- "Which customer ordered the most Doohickeys?"
- "What's the average order value in the East region?"
- "Which month had the most orders?"
- "Rank customers by total quantity ordered, highest first"

## Notes & limitations

- Each upload creates a fresh, temporary DuckDB table — data does not persist between sessions.
- Column names are automatically cleaned (lowercased, special characters replaced) to improve SQL generation reliability.
- Best suited for small-to-medium CSVs (tens of thousands of rows, fewer than ~30 columns). Very large or very wide files may hit LLM context limits or slow down schema inspection.