import sqlite3
import streamlit as st
import pandas as pd
import plotly.express as px
import os
st.set_page_config(page_title="Spotify 趨勢觀測儀表板", layout="wide")

# ----- 💡 雲端保險機制：如果找不到資料庫，自動在後端執行 fetch_data 生成資料 -----
if not os.path.exists("spotify_tracks.db"):
    import fetch_data

    fetch_data.init_db()
    fetch_data.generate_mock_pipeline()
# ------------------------------------------------------------------------

st.title("🎵 Spotify 每日發燒榜動態監測系統")
st.caption("本系統每日自動抓取最新 Top 50 數據，提供市場與熱門歌曲趨勢分析。")


# 讀取資料庫數據
def load_data():
    try:
        conn = sqlite3.connect("spotify_tracks.db")
        query = "SELECT * FROM daily_top_tracks ORDER BY date DESC, rank ASC"
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except Exception:
        return pd.DataFrame()


df = load_data()

if df.empty:
    st.warning("⚠️ 目前資料庫內無資料，請先執行 `python fetch_data.py` 初始化並抓取資料。")
else:
    # 側邊欄篩選器
    available_dates = sorted(df["date"].unique(), reverse=True)
    selected_date = st.sidebar.selectbox("選擇觀測日期", available_dates)

    # 篩選當日數據
    df_today = df[df["date"] == selected_date]

    # --- KPI 區塊 ---
    st.subheader(f"📊 {selected_date} 重點數據概覽")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="今日霸榜歌曲", value=df_today.iloc[0]["track_name"])
    with col2:
        st.metric(label="今日最熱門歌手", value=df_today.iloc[0]["artist_name"])
    with col3:
        st.metric(label="上榜歌曲平均熱度", value=f"{df_today['popularity'].mean():.1f} / 100")

    st.markdown("---")

    # --- 視覺化圖表區 ---
    left_col, right_col = st.columns(2)

    with left_col:
        st.subheader("📈 Top 10 歌曲人氣度對比")
        fig_bar = px.bar(
            df_today.head(10),
            x="popularity",
            y="track_name",
            orientation="h",
            text="popularity",
            color="popularity",
            color_continuous_scale="Viridis",
            labels={"track_name": "歌曲名稱", "popularity": "熱度值 (Popularity)"},
        )
        fig_bar.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig_bar, use_container_width=True)

    with right_col:
        st.subheader("分析：歌曲長度與人氣度關係")
        # 轉為分鐘
        df_today["duration_min"] = df_today["duration_ms"] / 60000
        fig_scatter = px.scatter(
            df_today,
            x="duration_min",
            y="popularity",
            size="popularity",
            color="rank",
            hover_name="track_name",
            labels={"duration_min": "歌曲長度 (分鐘)", "popularity": "人氣度"},
        )
        st.plotly_chart(fig_scatter, use_container_width=True)

    # --- 歷史排名追蹤趨勢 ---
    st.markdown("---")
    st.subheader("🔄 核心歌曲名次走勢追蹤")
    all_songs = df["track_name"].unique()
    selected_songs = st.multiselect(
        "選擇你想追蹤名次變化的歌曲 (可多選)：", all_songs, default=all_songs[:2]
    )

    if selected_songs:
        df_trend = df[df["track_name"].isin(selected_songs)]
        fig_trend = px.line(
            df_trend,
            x="date",
            y="rank",
            color="track_name",
            markers=True,
            labels={"date": "日期", "rank": "名次"},
        )
        fig_trend.update_yaxes(autorange="reversed")  # 讓第 1 名在最上面
        st.plotly_chart(fig_trend, use_container_width=True)

    # --- 詳細資料表 ---
    st.subheader("📋 今日 Top 50 完整數據庫")
    st.dataframe(
        df_today[
            ["rank", "track_name", "artist_name", "album_name", "popularity"]
        ].set_index("rank"),
        use_container_width=True,
    )