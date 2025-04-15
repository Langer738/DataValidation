import streamlit as st
import pandas as pd
import openai

# Get API key from Streamlit secrets
openai.api_key = st.secrets["openai"]["api_key"]  # Replace with your OpenAI key

# === Define filters ===
def check_missing_emails(df):
    return df[df['email'].isnull()]

def flag_short_names(df):
    return df[df['name'].str.len() < 2]

def check_age_range(df):
    return df[(df['age'] < 0) | (df['age'] > 120)]

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

# === Ask LLM which filters to apply ===
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
            max_tokens=200
        )
        content = response.choices[0].message.content.strip()

        st.subheader("🧠 Raw AI Response (for debugging)")
        st.code(content, language="python")

        result = eval(content)

        # 🔁 Add fallback if AI doesn't return anything
        if not result:
            st.info("⚠️ No filters were suggested. Showing all filters for testing purposes.")
            return list(FILTERS.keys())

        return [f for f in result if f in FILTERS]

    except Exception as e:
        st.error(f"❌ Error parsing AI response: {e}")
        return []

# === Streamlit UI ===
st.title("Smart CSV Validator with AI Filters")

uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])
if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.write("\U0001F4CA Data Preview:", df.head())

    # Ask AI which filters to apply
    suggested = suggest_filters(list(df.columns), df)
    st.write("\U0001F916 Suggested Filters:", [FILTER_DESCRIPTIONS[k] for k in suggested])

    # Run the filters
    for key in suggested:
        failed_rows = FILTERS[key](df)
        if not failed_rows.empty:
            st.warning(f"Issues found: {FILTER_DESCRIPTIONS[key]}")
            st.dataframe(failed_rows)
        else:
            st.success(f"Passed: {FILTER_DESCRIPTIONS[key]}")
