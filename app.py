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
I have the following CSV headers: {headers}
Here is a sample of the data:
{sample_rows.to_dict(orient='records')[:3]}

Based on this, which of the following checks would you apply?
Available checks:
{FILTER_DESCRIPTIONS}

Return a Python list of filter keys that should apply.
"""
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=200
    )
    try:
        result = eval(response["choices"][0]["message"]["content"])
        return [f for f in result if f in FILTERS]
    except:
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
