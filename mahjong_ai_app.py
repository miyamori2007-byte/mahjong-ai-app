import streamlit as st
import numpy as np
from PIL import Image

from ultralytics import YOLO
from mahjong.hand_calculating.hand import HandCalculator
from mahjong.tile import TilesConverter
from mahjong.hand_calculating.hand_config import HandConfig
from mahjong.meld import Meld

st.set_page_config(layout="wide")
st.title("🀄 麻雀AI（画像認識 × 鳴き対応 完全版）")

# =========================
# YOLOモデル
# =========================
@st.cache_resource
def load_model():
    try:
        return YOLO("mahjong_yolo.pt")
    except:
        return None

model = load_model()

# =========================
# 入力UI
# =========================
st.sidebar.header("入力")

img_file = st.file_uploader("画像アップロード")

riichi = st.sidebar.checkbox("立直")
ippatsu = st.sidebar.checkbox("一発")
tsumo = st.sidebar.checkbox("ツモ")

field_wind = st.sidebar.selectbox("場風", ["東", "南", "西", "北"])
self_wind = st.sidebar.selectbox("自風", ["東", "南", "西", "北"])

dora = st.sidebar.number_input("ドラ", 0, 10, 0)
red_dora = st.sidebar.number_input("赤ドラ", 0, 4, 0)
honba = st.sidebar.number_input("本場", 0, 20, 0)

# 副露入力
st.sidebar.subheader("鳴き（副露）")
melds_input = st.sidebar.text_area("例: 555p,123s,7777m", "")

# =========================
# ラベル
# =========================
label_map = {
    0:"1m",1:"2m",2:"3m",3:"4m",4:"5m",5:"6m",6:"7m",7:"8m",8:"9m",
    9:"1p",10:"2p",11:"3p",12:"4p",13:"5p",14:"6p",15:"7p",16:"8p",17:"9p",
    18:"1s",19:"2s",20:"3s",21:"4s",22:"5s",23:"6s",24:"7s",25:"8s",26:"9s",
    27:"東",28:"南",29:"西",30:"北",31:"白",32:"發",33:"中"
}

# =========================
# YOLO検出
# =========================
def detect_tiles(image):
    if model is None:
        return []

    img_np = np.array(image)
    results = model(img_np)[0]

    tiles = []
    for box in results.boxes:
        cls = int(box.cls[0])
        x = float(box.xyxy[0][0])
        if cls in label_map:
            tiles.append((x, label_map[cls]))

    tiles.sort(key=lambda x: x[0])
    return [t[1] for t in tiles]

# =========================
# パース
# =========================
def parse_tiles_str(s):
    tiles = []
    num = ""
    for c in s:
        if c.isdigit():
            num += c
        elif c in "mps":
            for n in num:
                tiles.append(n + c)
            num = ""
        elif c in ["東","南","西","北","白","發","中"]:
            tiles.append(c)
    return tiles

# =========================
# 変換
# =========================
def convert_tiles(tile_list):
    man = pin = sou = honors = ""
    for t in tile_list:
        if t.endswith("m"):
            man += t[0]
        elif t.endswith("p"):
            pin += t[0]
        elif t.endswith("s"):
            sou += t[0]
        else:
            honors += convert_honor(t)

    return TilesConverter.string_to_136_array(
        man=man, pin=pin, sou=sou, honors=honors
    )

def convert_honor(c):
    return {"東":"1","南":"2","西":"3","北":"4","白":"5","發":"6","中":"7"}.get(c,"")

def wind_to_int(w):
    return {"東":0,"南":1,"西":2,"北":3}[w]

# =========================
# 副露パース
# =========================
def parse_melds(melds_str):
    melds = []
    if not melds_str.strip():
        return melds

    raw = melds_str.split(",")

    for m in raw:
        m = m.strip()
        suit = m[-1]
        nums = m[:-1]

        tiles = [n + suit for n in nums]
        tiles136 = convert_tiles(tiles)

        if len(tiles) == 3:
            if nums[0] == nums[1]:
                meld_type = Meld.PON
            else:
                meld_type = Meld.CHI
        elif len(tiles) == 4:
            meld_type = Meld.KAN
        else:
            continue

        melds.append(Meld(meld_type, tiles136))

    return melds

# =========================
# メイン
# =========================
if img_file:

    img = Image.open(img_file)
    st.image(img, caption="入力画像", use_column_width=True)

    detected = detect_tiles(img)

    if len(detected) == 0:
        st.warning("牌が認識できませんでした。手動入力してください。")

    tiles_str = st.text_input(
        "牌列（修正可）",
        "".join(detected) if detected else "123m123p123s東東東白白"
    )

    tile_list = parse_tiles_str(tiles_str)
    melds = parse_melds(melds_input)

    # 和了牌
    win_tile_input = st.selectbox("和了牌", tile_list) if tile_list else None

    if st.button("点数計算"):

        try:
            expected_tiles = 14 - (len(melds) * 3)

            if len(tile_list) != expected_tiles:
                st.error(f"手牌は {expected_tiles} 枚にしてください")
                st.stop()

            tiles136 = convert_tiles(tile_list)
            win_tile = convert_tiles([win_tile_input])[0]

            calculator = HandCalculator()

            config = HandConfig(
                is_riichi=riichi,
                is_ippatsu=ippatsu,
                is_tsumo=tsumo,
                player_wind=wind_to_int(self_wind),
                round_wind=wind_to_int(field_wind)
            )

            result = calculator.estimate_hand_value(
                tiles=tiles136,
                win_tile=win_tile,
                melds=melds,
                config=config
            )

            if result.error:
                st.error(result.error)
            else:
                han = result.han + dora + red_dora
                fu = result.fu

                if han >= 13:
                    han = 12

                base = fu * (2 ** (han + 2))
                if base >= 1920:
                    base = 2000

                score = base * (4 if not tsumo else 2)
                score += honba * 300

                st.subheader("結果")
                st.write(f"点数: {int(score)}")
                st.write(f"翻: {han}")
                st.write(f"符: {fu}")

                st.write("役:")
                for y in result.yaku:
                    st.write("-", y.name)

        except Exception as e:
            st.error(str(e))
