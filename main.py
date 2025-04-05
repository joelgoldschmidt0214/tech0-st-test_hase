import streamlit as st
import pandas as pd
import numpy as np
import random
import matplotlib.pyplot as plt
import datetime

# ----------------------------
# Buttons Example
st.button("Reset", type="primary")
if st.button("Say hello"):
    st.write("Why hello there")
else:
    st.write("Goodbye")

if st.button("Aloha", type="tertiary"):
    st.write("Ciao")

# ----------------------------
# Markdown Examples
st.markdown("*Streamlit* is **really** ***cool***でしょ？.")
st.markdown('''
:red[Streamlit] :orange[can] :green[write] :blue[text] :violet[in]
:gray[pretty] :rainbow[colors] and :blue-background[highlight] text.
''')
st.markdown("Here's a bouquet &mdash; :tulip::cherry_blossom::rose::hibiscus::sunflower::blossom:")

multi = """If you end a line with two spaces,  
a soft return is used for the next line.

Two (or more) newline characters in a row will result in a hard return.
"""
st.markdown(multi)

# ----------------------------
# HTML Rendering
st.html("<p><span style='text-decoration: line-through double red;'>Oops</span>!</p>")

# ----------------------------
# DataFrame Example with Random Data
df = pd.DataFrame(np.random.randn(50, 20), columns=("col %d" % i for i in range(20)))
st.dataframe(df)

# ----------------------------
# DataFrame with Column Configurations
df_apps = pd.DataFrame({
    "name": ["Roadmap", "Extras", "Issues"],
    "url": [
        "https://roadmap.streamlit.app",
        "https://extras.streamlit.app",
        "https://issues.streamlit.app"
    ],
    "stars": [random.randint(0, 1000) for _ in range(3)],
    "views_history": [[random.randint(0, 5000) for _ in range(30)] for _ in range(3)]
})
st.dataframe(
    df_apps,
    column_config={
        "name": "App name",
        "stars": st.column_config.NumberColumn(
            "Github Stars", help="Number of stars on GitHub", format="%d ⭐"
        ),
        "url": st.column_config.LinkColumn("App URL"),
        "views_history": st.column_config.LineChartColumn(
            "Views (past 30 days)", y_min=0, y_max=5000
        )
    },
    hide_index=True,
)

# ----------------------------
# Matplotlib Histogram Plot
arr = np.random.normal(1, 1, size=100)
fig, ax = plt.subplots()
ax.hist(arr, bins=20)
st.pyplot(fig)

# ----------------------------
# Date Input Example
today = datetime.datetime.now()
next_year = today.year + 1
jan_1 = datetime.date(next_year, 1, 1)
dec_31 = datetime.date(next_year, 12, 31)

vacation_dates = st.date_input(
    "Select your vacation for next year",
    (jan_1, datetime.date(next_year, 1, 7)),
    jan_1,
    dec_31,
    format="MM.DD.YYYY",
)
st.write(vacation_dates)

# ----------------------------
# Dialog Vote Example
@st.dialog("Cast your vote")
def vote(item):
    st.write(f"Why is {item} your favorite?")
    reason = st.text_input("Because...")
    if st.button("Submit"):
        st.session_state.vote = {"item": item, "reason": reason}
        st.rerun()

if "vote" not in st.session_state:
    st.write("Vote for your favorite")
    if st.button("A"):
        vote("A")
    if st.button("B"):
        vote("B")
else:
    st.write(f"You voted for {st.session_state.vote['item']} because {st.session_state.vote['reason']}")