import os
import re
import pandas as pd
import streamlit as st
import duckdb
from sqlalchemy import create_engine
from langchain_groq import ChatGroq
from langchain_community.agent_toolkits import create_sql_agent
from langchain_community.utilities import SQLDatabase
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Ask Your Data", page_icon="📊", layout="wide")
st.title("📊 Ask Your Data")
st.caption("Upload a CSV, then ask questions about it in plain English.")

# --- Session state setup ---
if "db_path" not in st.session_state:
    st.session_state.db_path = None
if "table_name" not in st.session_state:
    st.session_state.table_name = None
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- File upload ---
uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)

    # Clean column names: lowercase, replace spaces/special chars with underscores
    df.columns = [
        re.sub(r"[^0-9a-zA-Z_]", "_", col.strip().lower().replace(" ", "_"))
        for col in df.columns
    ]

    table_name = "data"
    db_path = "uploaded_data.duckdb"

    # Remove any existing db file to avoid connection conflicts
    if os.path.exists(db_path):
        os.remove(db_path)

    # Load into a fresh DuckDB file (overwrite each time a new file is uploaded)
    con = duckdb.connect(db_path)
    con.register("df_view", df)
    con.execute(f"CREATE TABLE {table_name} AS SELECT * FROM df_view")
    con.close()

    st.session_state.db_path = db_path
    st.session_state.table_name = table_name

    st.success(f"Loaded `{uploaded_file.name}` — {df.shape[0]} rows, {df.shape[1]} columns")
    st.dataframe(df.head(10))

    with st.expander("Detected columns"):
        st.write(list(df.columns))

st.divider()

# --- Chat interface ---
if st.session_state.db_path is None:
    st.info("Upload a CSV above to start asking questions.")
else:
    groq_api_key = os.getenv("GROQ_API_KEY") or st.session_state.get("groq_api_key")

    if not groq_api_key:
        groq_api_key = st.text_input("Enter your Groq API key", type="password")
        if groq_api_key:
            st.session_state["groq_api_key"] = groq_api_key

    if groq_api_key:
        # Display chat history
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        question = st.chat_input("Ask a question about your data...")

        if question:
            st.session_state.messages.append({"role": "user", "content": question})
            with st.chat_message("user"):
                st.markdown(question)

            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    engine = create_engine(f"duckdb:///{st.session_state.db_path}")
                    sql_queries = []
                    try:
                        db = SQLDatabase(engine, include_tables=[st.session_state.table_name])

                        llm = ChatGroq(
                            groq_api_key=groq_api_key,
                            model_name="llama-3.3-70b-versatile",
                            temperature=0,
                        )

                        agent = create_sql_agent(
                            llm=llm,
                            db=db,
                            agent_type="tool-calling",
                            verbose=True,
                            prefix=(
                                "You are a SQL expert working with a DuckDB database. "
                                "The ONLY table in this database is called 'data'. "
                                "Do not reference any other table names. "
                                "Always start by running sql_db_schema on the 'data' table to see its columns "
                                "before writing any query."
                            ),
                        )

                        from langchain_core.callbacks.base import BaseCallbackHandler

                        class SQLCaptureCallback(BaseCallbackHandler):
                            def on_tool_start(self, serialized, input_str, **kwargs):
                                tool_name = serialized.get("name", "")
                                if tool_name == "sql_db_query":
                                    sql_queries.append(input_str)

                        response = agent.invoke(
                            {"input": question},
                            config={"callbacks": [SQLCaptureCallback()]},
                        )
                        answer = response["output"]
                    except Exception as e:
                        answer = f"Something went wrong: {e}"
                    finally:
                        engine.dispose()

                    st.markdown(answer)

                    if sql_queries:
                        with st.expander("View SQL query used"):
                            for q in sql_queries:
                                st.code(q, language="sql")
                        full_content = answer + "\n\n**SQL used:**\n```sql\n" + "\n".join(sql_queries) + "\n```"
                    else:
                        full_content = answer

                    st.session_state.messages.append({"role": "assistant", "content": full_content})
    else:
        st.warning("A Groq API key is required to ask questions. Get one free at console.groq.com")