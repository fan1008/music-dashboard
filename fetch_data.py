import random
import sqlite3
from datetime import datetime
import pandas as pd

# 模擬一組華語與西洋熱門歌手與歌曲池，讓它隨機噴出每天的榜單
SONG_POOL = [
    ("周杰倫", "最偉大的作品", "最偉大的作品"),
    ("告五人", "好不容易", "影集插曲"),
    ("韋禮安", "如果可以", "電影主題曲"),
    ("陳華", "想和你看五月的晚霞", "華語流行"),
    ("美秀集團", "捲菸", "獨立音樂"),
    ("Taylor Swift", "Cruel Summer", "Lover"),
    ("Bruno Mars", "Die With A Smile", "Single"),
    ("Sabrina Carpenter", "Espresso", "Short n' Sweet"),
    ("NewJeans", "Super Shy", "Get Up"),
    ("YOASOBI", "Idol", "Idol Single"),
    ("張惠妹", "連名帶姓", "偷故事的人"),
    ("林俊傑", "修煉愛情", "因你而在"),
    ("蔡依林", "玫瑰少年", "UGLY BEAUTY"),
    ("五月天", "突然好想你", "後青春期的詩"),
    ("ØZI", "B.O.", "PEDESTAL"),
    ("李榮浩", "烏梅子醬", "縱橫四海"),
    ("周興哲", "以後別做朋友", "學著愛"),
    ("鄧紫棋", "光年之外", "心之科學"),
    ("派偉俊", "3A07", "Single"),
    ("宇宙人", "藍色的你", "理想狀態"),
]


def init_db():
    """初始化 SQLite 資料庫"""
    conn = sqlite3.connect("spotify_tracks.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_top_tracks (
            date TEXT,
            rank INTEGER,
            track_id TEXT,
            track_name TEXT,
            artist_name TEXT,
            popularity INTEGER,
            duration_ms INTEGER,
            album_name TEXT,
            PRIMARY KEY (date, rank)
        )
    """)
    conn.commit()
    conn.close()


def generate_mock_pipeline():
    """ETL 核心邏輯：模擬從 Stream 抓取、清洗並載入資料庫"""
    print(f"[{datetime.now()}] 啟動串流資料 Mocking Pipeline...")

    # 模擬今天與過去幾天的日期，讓你的 Dashboard 一打開就有漂亮的「歷史趨勢圖」可以秀！
    # 如果資料庫是空的，我們自動幫你補齊過去 3 天的歷史資料
    conn = sqlite3.connect("spotify_tracks.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM daily_top_tracks")
    data_count = cursor.fetchone()[0]
    conn.close()

    # 如果沒資料，就生成過去 3 天 + 今天；如果有資料，就只生成今天
    dates_to_generate = (
        ["2026-06-01", "2026-06-02", "2026-06-03", "2026-06-04"]
        if data_count == 0
        else [datetime.now().strftime("%Y-%m-%d")]
    )

    all_parsed_tracks = []

    for target_date in dates_to_generate:
        # 随機打亂歌曲庫來決定當天排名
        shuffled_pool = random.sample(SONG_POOL, len(SONG_POOL))

        for idx, item in enumerate(shuffled_pool[:15]):  # 每天挑 15 首上榜
            # 隨機生成稍微變動的音樂特徵（符合真實世界數據特徵）
            popularity = random.randint(75, 99)
            duration_ms = random.randint(180, 240) * 1000  # 3~4 分鐘

            track_info = {
                "date": target_date,
                "rank": idx + 1,
                "track_id": f"mock_{item[1][:3].lower()}_{idx}",
                "track_name": item[1],
                "artist_name": item[0],
                "popularity": popularity,
                "duration_ms": duration_ms,
                "album_name": item[2],
            }
            all_parsed_tracks.append(track_info)

    df = pd.DataFrame(all_parsed_tracks)

    # Load: 寫入資料庫
    conn = sqlite3.connect("spotify_tracks.db")
    df.to_sql("daily_top_tracks", conn, if_exists="append", index=False)

    # SQL Wrangle: 去除重複值
    cursor = conn.cursor()
    cursor.execute("""
        DELETE FROM daily_top_tracks 
        WHERE rowid NOT IN (
            SELECT MIN(rowid) FROM daily_top_tracks GROUP BY date, rank
        )
    """)
    conn.commit()
    conn.close()

    print(f"[{datetime.now()}] 成功模擬並導入 {len(dates_to_generate)} 天的流行榜單資料至資料庫！")


if __name__ == "__main__":
    init_db()
    generate_mock_pipeline()