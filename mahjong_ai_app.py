import streamlit as st
from mahjong.hand_calculating.hand import HandCalculator
from mahjong.tile import TilesConverter
from mahjong.hand_calculating.hand_config import HandConfig

st.set_page_config(layout="wide")
st.title("🀄 麻雀点数計算AI（mahjongエンジン）")

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
# 牌変換
# =========================
def convert_tiles(s):
    man = pin = sou = honors = ""
    num = ""

    for c in s:
        if c.isdigit():
            num += c
        elif c in "mps":
            if c == "m": man += num
            if c == "p": pin += num
            if c == "s": sou += num
            num = ""
        else:
            honors += convert_honor(c)

    return TilesConverter.string_to_136_array(
        man=man, pin=pin, sou=sou, honors=honors
    )

def convert_honor(c):
    table = {
        "東":"1","南":"2","西":"3","北":"4",
        "白":"5","發":"6","中":"7"
    }
    return table.get(c,"")

# =========================
# 風変換
# =========================
def wind_to_int(w):
    table = {"東":0, "南":1, "西":2, "北":3}
    return table[w]

# =========================
# 実行
# =========================
if st.button("計算"):

    try:
        tiles = convert_tiles(tiles_str)

        calculator = HandCalculator()

        config = HandConfig(
            is_riichi=riichi,
            is_ippatsu=ippatsu,
            is_tsumo=(win_type == "ツモ"),
            is_rinshan=rinshan,
            is_haitei=haitei,
            player_wind=wind_to_int(self_wind),
            round_wind=wind_to_int(field_wind)
        )

        result = calculator.estimate_hand_value(
            tiles=tiles,
            win_tile=tiles[-1],
            config=config
        )

        st.subheader("結果")

        if result.error:
            st.error(result.error)
        else:
            han = result.han + dora + red_dora
            fu = result.fu

            # 数え役満なし
            if han >= 13:
                han = 12

            # 基本点
            base = fu * (2 ** (han + 2))

            # 切り上げ満貫
            if base >= 1920:
                base = 2000

            # 点数
            if win_type == "ロン":
                score = base * 4
            else:
                score = base * 2

            score += honba * 300

            st.write(f"翻: {han}")
            st.write(f"符: {fu}")
            st.write(f"点数: {int(score)}")

            st.write("役:")
            for y in result.yaku:
                st.write("-", y.name)

    except Exception as e:
        st.error(str(e))
