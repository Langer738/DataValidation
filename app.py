import streamlit as st
import pandas as pd
import ast
from openai import OpenAI

# Initialize OpenAI client using secrets
client = OpenAI(api_key=st.secrets["openai"]["api_key"])

# Sample filter functions
def check_missing_emails(df):
    return df[df["email"].isna()]

def flag_short_names(df):
    return df[df["name"].str.len() < 3]

def check_age_range(df):
    return df[(df["age"] < 0) | (df["age"] > 120)]

# Available filters
FILTERS = {
    "check_missing_emails": check_missing_emails,
    "flag_short_names": flag_short_names,
    "check_age_range": check_age_range,
}

FILTER_DESCRIPTIONS = {
    "check_missing_emails": "Check for missing emails",
    "flag_short_names": "Flag names that are too short",
    "check_age_range": "Check for unrealistic ages",
}

def suggest_filters(headers, sample_rows):
    prompt = f"""
You are a data validation assistant. Your job is to help select which data checks to run.

Here are the CSV headers: {headers}
Sample data:
{sample_rows.to_dict(orient='records')[:3]}

Available validation filters and their descriptions:
{FILTER_DESCRIPTIONS}

Based on the headers and sample data, return a Python list (e.g., ["check_missing_emails", "flag_short_names"])
containing only the relevant filter keys from the list above.
Do NOT include any explanation. Only return the Python list.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300
        )
        content = response.choices[0].message.content.strip()

        # Show prompt and raw AI response in Streamlit for debugging
        st.subheader("📄 Prompt Sent to GPT")
        st.text(prompt)

        st.subheader("🧠 Raw AI Response (for debugging)")
        st.code(content, language="python")

        # Sanitize and parse the AI response safely
        content = content.replace("“", "\"").replace("”", "\"")
        result = ast.literal_eval(content)

        if not result:
            st.info("⚠️ No filters were suggested. Showing all filters for testing.")
            return list(FILTERS.keys())

        return [f for f in result if f in FILTERS]

    except Exception as e:
        st.error(f"❌ Error parsing AI response: {e}")
        return []

# Streamlit UI
st.title("🧪 AI Data Validator")
uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.write("📄 Preview of uploaded data:")
    st.dataframe(df.head())

    headers = df.columns.tolist()
    sample_rows = df.head(5)

    suggested_filters = suggest_filters(headers, sample_rows)

    st.subheader("✅ Suggested Filters")
    st.write(suggested_filters)

    for filter_key in suggested_filters:
        if filter_key in FILTERS:
            st.markdown(f"### 🔍 Results for: `{filter_key}`")
            result_df = FILTERS[filter_key](df)
            if not result_df.empty:
                st.dataframe(result_df)
            else:
                st.success("No issues found for this check ✅")
