import streamlit as st
import math

st.set_page_config(layout="wide")
st.title("🀄 麻雀点数計算AI（プロルール準拠）")

# =========================
# 入力UI
# =========================
st.sidebar.header("入力")

tiles_str = st.sidebar.text_input(
    "手牌（例: 123m123p123s東東東白白）",
    "123m123p123s東東東白白"
)

win_type = st.sidebar.radio("和了", ["ロン", "ツモ"])
riichi = st.sidebar.checkbox("立直")
ippatsu = st.sidebar.checkbox("一発")
rinshan = st.sidebar.checkbox("嶺上開花")
haitei = st.sidebar.checkbox("海底/河底")

field_wind = st.sidebar.selectbox("場風", ["東", "南", "西", "北"])
self_wind = st.sidebar.selectbox("自風", ["東", "南", "西", "北"])

dora = st.sidebar.number_input("ドラ", 0, 10, 0)
red_dora = st.sidebar.number_input("赤ドラ", 0, 4, 0)
honba = st.sidebar.number_input("本場", 0, 20, 0)

# =========================
# 手牌変換
# =========================
def parse_tiles(s):
    result = []
    num = ""
    for c in s:
        if c.isdigit():
            num += c
        else:
            for n in num:
                result.append(n + c)
            num = ""
            if c in ["東","南","西","北","白","發","中"]:
                result.append(c)
    return result

tiles = parse_tiles(tiles_str)

# =========================
# 簡易役判定
# =========================
def calculate_han(tiles):
    han = 0
    yaku = []

    # 立直
    if riichi:
        han += 1
        yaku.append("立直")

    if ippatsu:
        han += 1
        yaku.append("一発")

    if win_type == "ツモ":
        han += 1
        yaku.append("門前清自摸和")

    # タンヤオ（簡易）
    if all(t[0] not in "19" and t not in ["東","南","西","北","白","發","中"] for t in tiles):
        han += 1
        yaku.append("断么九")

    # 役牌（超簡易）
    for honor in ["白","發","中", field_wind, self_wind]:
        if tiles.count(honor) >= 3:
            han += 1
            yaku.append(f"役牌({honor})")

    # ドラ
    han += dora + red_dora

    return han, yaku

# =========================
# 符計算（簡易）
# =========================
def calculate_fu():
    fu = 20

    if win_type == "ロン" and riichi:
        fu += 10

    if win_type == "ツモ":
        fu += 2

    # 雀頭（連風牌）
    fu += 2  # 仮で加算

    return int(math.ceil(fu / 10.0) * 10)

# =========================
# 点数計算
# =========================
def calculate_score(fu, han):
    # 数え役満なし
    if han >= 13:
        han = 12

    base = fu * (2 ** (han + 2))

    # 切り上げ満貫
    if base >= 1920:
        base = 2000

    if win_type == "ロン":
        score = base * 4
    else:
        score = base * 2  # 簡易

    score += honba * 300

    return int(score)

# =========================
# 実行
# =========================
if st.button("計算"):
    han, yaku = calculate_han(tiles)
    fu = calculate_fu()
    score = calculate_score(fu, han)

    st.subheader("結果")
    st.write(f"翻数: {han}")
    st.write(f"符: {fu}")
    st.write(f"点数: {score}")

    st.write("役:")
    for y in yaku:
        st.write("-", y)
