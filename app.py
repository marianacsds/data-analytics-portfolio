import streamlit as st
import pandas as pd
import plotly.express as px
import gzip
import ast

st.set_page_config(page_title="Beauty Products Dashboard", layout="wide", page_icon="💄")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- Carregar reviews ---
df = pd.read_csv("ratings_Beauty.csv", names=["userId", "productId", "rating", "timestamp"])
df["rating"] = pd.to_numeric(df["rating"], errors="coerce")
df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s", errors="coerce")
df["year"] = df["timestamp"].dt.year
df["month"] = df["timestamp"].dt.month
df = df.dropna(subset=["rating"])

# --- Carregar metadados (nomes dos produtos) ---
@st.cache_data
def load_metadata(path):
    data = []
    with gzip.open(path, 'rt', encoding='utf-8') as f:
        for line in f:
            try:
                item = ast.literal_eval(line.strip())
                asin = item.get("asin", "")
                title = item.get("title", "")
                if asin:
                    data.append({"productId": asin, "productName": title})
            except:
                continue
    return pd.DataFrame(data)

try:
    df_meta = load_metadata("meta_Beauty.json.gz")
    df_meta = load_metadata("meta_Beauty.json.gz")
    df_meta = df_meta.drop_duplicates(subset="productId")
    df = df.merge(df_meta, on="productId", how="left")
    df["productName"] = df["productName"].fillna(df["productId"])
except FileNotFoundError:
    df["productName"] = df["productId"]

# --- Sidebar ---
st.title("💄 Beauty Products Dashboard")
st.markdown("Interactive analysis of Amazon Beauty Products ratings")
st.divider()

st.sidebar.header("Filters")
years = ["All"] + sorted(df["year"].dropna().unique().tolist())
selected_year = st.sidebar.selectbox("Year", years)
min_rating, max_rating = st.sidebar.slider("Rating range", 1.0, 5.0, (1.0, 5.0), 0.5)

filtered = df.copy()
if selected_year != "All":
    filtered = filtered[filtered["year"] == selected_year]
filtered = filtered[(filtered["rating"] >= min_rating) & (filtered["rating"] <= max_rating)]

# --- Overview ---
st.subheader("Overview")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Reviews", f"{len(filtered):,}")
col2.metric("Unique Products", f"{filtered['productId'].nunique():,}")
col3.metric("Unique Users", f"{filtered['userId'].nunique():,}")
col4.metric("Average Rating", f"{filtered['rating'].mean():.2f} ⭐")

st.divider()

# --- Rating Distribution + Reviews Over Time ---
col_a, col_b = st.columns(2)

with col_a:
    st.subheader("Rating Distribution")
    rating_dist = filtered["rating"].value_counts().reset_index()
    rating_dist.columns = ["Rating", "Count"]
    rating_dist = rating_dist.sort_values("Rating")
    fig1 = px.bar(rating_dist, x="Rating", y="Count", color="Count", color_continuous_scale="teal")
    fig1.update_layout(coloraxis_showscale=False)
    st.plotly_chart(fig1, use_container_width=True)

with col_b:
    st.subheader("Reviews Over Time")
    tempo = filtered.groupby("year").size().reset_index(name="Reviews")
    fig2 = px.line(tempo, x="year", y="Reviews", color_discrete_sequence=["#00b4d8"], markers=True)
    fig2.update_layout(xaxis_title="Year", yaxis_title="Number of Reviews")
    st.plotly_chart(fig2, use_container_width=True)

# --- Top 10 Most Reviewed Products ---
st.subheader("Top 10 Most Reviewed Products")
top_products = filtered.groupby("productName").agg(
    reviews=("rating", "count"),
    avg_rating=("rating", "mean")
).reset_index().sort_values("reviews", ascending=False).head(10)
top_products["avg_rating"] = top_products["avg_rating"].round(2)
fig3 = px.bar(top_products, x="reviews", y="productName", orientation="h",
              color="avg_rating", color_continuous_scale="teal",
              labels={"reviews": "Number of Reviews", "productName": "Product", "avg_rating": "Avg Rating"})
fig3.update_layout(yaxis={"categoryorder": "total ascending"})
st.plotly_chart(fig3, use_container_width=True)

# --- Reviews by Month + Rating Share ---
col_c, col_d = st.columns(2)

with col_c:
    st.subheader("Reviews by Month")
    monthly = filtered.groupby("month").size().reset_index(name="Reviews")
    months = {1:"Jan",2:"Feb",3:"Mar",4:"Apr",5:"May",6:"Jun",
              7:"Jul",8:"Aug",9:"Sep",10:"Oct",11:"Nov",12:"Dec"}
    monthly["month"] = monthly["month"].map(months)
    fig4 = px.bar(monthly, x="month", y="Reviews", color="Reviews", color_continuous_scale="teal")
    fig4.update_layout(coloraxis_showscale=False, xaxis_title="Month")
    st.plotly_chart(fig4, use_container_width=True)

with col_d:
    st.subheader("Rating Share")
    share = filtered["rating"].value_counts().reset_index()
    share.columns = ["Rating", "Count"]
    share["Rating"] = share["Rating"].astype(str) + " ⭐"
    fig5 = px.pie(share, names="Rating", values="Count", hole=0.4)
    st.plotly_chart(fig5, use_container_width=True)

st.divider()

# --- Raw Data ---
st.subheader("Raw Data")
st.dataframe(filtered[["userId", "productId", "productName", "rating", "timestamp", "year", "month"]].head(1000), use_container_width=True)