import streamlit as st
import pandas as pd
import seaborn as sns
import plotly.express as px
import matplotlib.pyplot as plt
from pinotdb import connect

from datetime import datetime
import time

conn = connect(host='localhost', port=9000, path='/sql', scheme='http')

st.set_page_config(layout="wide")
st.title("Mastodon Usage")

now = datetime.now()
dt_string = now.strftime("%d %B %Y %H:%M:%S")
st.write(f"Last update: {dt_string}")

if not "sleep_time" in st.session_state:
    st.session_state.sleep_time = 2

if not "auto_refresh" in st.session_state:
    st.session_state.auto_refresh = True

mapping = {
    "1 hour": "PT1H",
    "10 minutes": "PT10M",
    "5 minutes": "PT5M"
}

mapping2 = {
    "1 hour": {"period": "PT60M", "granularity": "minute", "raw": 60},
    "30 minutes": {"period": "PT30M", "granularity": "minute", "raw": 30},
    "10 minutes": {"period": "PT10M", "granularity": "second", "raw": 10},
    "5 minutes": {"period": "PT5M", "granularity": "second", "raw": 5}
}

with st.expander("Configure Dashboard", expanded=True):
    left, right = st.columns(2)

    with left:
        auto_refresh = st.checkbox('Auto Refresh?', st.session_state.auto_refresh)

        if auto_refresh:
            number = st.number_input('Refresh rate in seconds', value=st.session_state.sleep_time)
            st.session_state.sleep_time = number

    with right:
            time_ago = st.radio("Time period to cover", mapping2.keys(), horizontal=True, key="time_ago")


curs = conn.cursor()

st.header("Live Mastodon Usage")
query = """
select count(*) as "Num toots"
, count(distinct(username)) as "Num users"
, count(distinct(url)) as "Num urls"
from mastodon
where created_at*1000 > ago(%(timeAgo)s)
order by 1 DESC;
"""
curs.execute(query, {"timeAgo": mapping2[time_ago]["period"]})
df = pd.DataFrame(curs, columns=[item[0] for item in curs.description])

query = """
select count(*) as "Num toots"
, count(distinct(username)) as "Num users"
, count(distinct(url)) as "Num urls"
from mastodon
where created_at*1000 < ago(%(timeAgo)s) AND created_at*1000 > ago(%(prevTimeAgo)s)
order by 1 DESC;
"""
curs.execute(query, {"timeAgo": mapping2[time_ago]["period"], "prevTimeAgo": f"PT{mapping2[time_ago]['raw']*2}M"})
prev_df = pd.DataFrame(curs, columns=[item[0] for item in curs.description])

metric1, metric2, metric3 = st.columns(3)

metric1.metric(
    label="Number of toots",
    value=float(df['Num toots'].values[0]),
    delta=float(df['Num toots'].values[0] - prev_df['Num toots'].values[0]) if prev_df['Num toots'].values[0] else None
)

metric2.metric(
    label="Number of users",
    value=float(df['Num users'].values[0]),
    delta=float(df['Num users'].values[0] - prev_df['Num users'].values[0]) if prev_df['Num users'].values[0] else None
)

metric3.metric(
    label="Number of urls",
    value=float(df['Num urls'].values[0]),
    delta=float(df['Num urls'].values[0] - prev_df['Num urls'].values[0]) if prev_df['Num urls'].values[0] else None
)


st.header("The Mastodon Server Landscape")
query = """
select base_url, 
       count(*)
from mastodon
where created_at*1000 > ago(%(timeAgo)s)
group by base_url
order by count(*) DESC;
"""
curs.execute(query, {"timeAgo": mapping2[time_ago]["period"]})
mastodon_app_df = pd.DataFrame(curs, columns=[item[0] for item in curs.description])

st.plotly_chart(px.bar(
     mastodon_app_df.sort_values(by=['count(*)'], ascending=False), y='base_url', x='count(*)',  color="base_url",
        color_discrete_sequence =['red', 'blue', 'green', 'orange', 'purple', 'aqua', 'orangered', 'palegreen', 'plum', 'pink']
     ), 
     use_container_width=True)

# fig = plt.figure(figsize=(10, 4))
# sns.barplot(data=mastodon_app_df, x="count(*)", y="app")
# st.pyplot(fig)

st.header("Time of Day Mastodon Usage")


query = """
select ToDateTime(DATETRUNC('MINUTE', created_at*1000), 'yyyy-MM-dd hh:mm:ss') AS created_minute
, count(*) as num
from mastodon
where created_at*1000 > ago(%(timeAgo)s)
group by 1
order by 1 desc
LIMIT 100;
"""
curs.execute(query, {"timeAgo": mapping2[time_ago]["period"]})
mastodon_usage_df = pd.DataFrame(curs, columns=[item[0] for item in curs.description])
fig = px.line(mastodon_usage_df, x='created_minute', y="num",  color_discrete_sequence =['blue', 'red', 'green'])
st.plotly_chart(fig, use_container_width=True)

st.header("Toot Length by Language Usage")
query = """
select characters, language
from mastodon
where language not in ('unknown') AND created_at*1000 > ago(%(timeAgo)s)
LIMIT 100000
"""
curs.execute(query, {"timeAgo": mapping2[time_ago]["period"]})
mastodon_lang_df = pd.DataFrame(curs, columns=[item[0] for item in curs.description])

top_languages= mastodon_lang_df.language.value_counts().iloc[:20].index
fig = px.box(mastodon_lang_df[mastodon_lang_df.language.isin(top_languages)].sort_values(by=["language"]), x="characters", y="language", width=800, height=600, color="language")
st.plotly_chart(fig, use_container_width=True)

# fig = plt.figure(figsize=(10, 4))
# sns.boxplot(data=mastodon_lang_df, x="characters", y="language", whis=100, orient="h", order=mastodon_lang_df.language.value_counts().iloc[:20].index)
# st.pyplot(fig)


if auto_refresh:
    time.sleep(number)
    st.experimental_rerun()