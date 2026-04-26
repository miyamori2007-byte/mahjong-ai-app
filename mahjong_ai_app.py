import streamlit as st
from mahjong.hand_calculating.hand import HandCalculator
from mahjong.tile import TilesConverter
from mahjong.hand_calculating.hand_config import HandConfig
from mahjong.meld import Meld

st.set_page_config(layout="wide")
st.title("🀄 麻雀AI（完全版・確定）")

# =========================
# 初期化
# =========================
if "hand" not in st.session_state:
    st.session_state.hand = []
if "melds" not in st.session_state:
    st.session_state.melds = []

# =========================
# 設定
# =========================
st.sidebar.header("設定")

riichi = st.sidebar.checkbox("立直")
ippatsu = st.sidebar.checkbox("一発")

win_type = st.sidebar.radio("和了方法", ["ロン", "ツモ"])
is_tsumo = (win_type == "ツモ")

field_wind = st.sidebar.selectbox("場風", ["東","南","西","北"])
self_wind = st.sidebar.selectbox("自風", ["東","南","西","北"])

honba = st.sidebar.number_input("本場", 0, 20, 0)

tiles_all = [
    *[f"{i}m" for i in range(1,10)],
    *[f"{i}p" for i in range(1,10)],
    *[f"{i}s" for i in range(1,10)],
    "東","南","西","北","白","發","中"
]

dora_tiles = st.sidebar.multiselect("ドラ", tiles_all)
ura_tiles = st.sidebar.multiselect("ウラドラ", tiles_all)

# =========================
# 手牌入力
# =========================
st.subheader("手牌入力")

cols = st.columns(9)
for i, tile in enumerate(tiles_all):
    if cols[i % 9].button(tile, key=f"add_{tile}_{i}"):
        st.session_state.hand.append((tile, False))

st.write("### 手牌")

for i, (tile, red) in enumerate(st.session_state.hand):
    col1, col2, col3 = st.columns([2,1,1])
    col1.write(f"{tile}🔴" if red else tile)

    if tile.startswith("5"):
        if col2.button("赤", key=f"red_{i}"):
            st.session_state.hand[i] = (tile, not red)
            st.rerun()

    if col3.button("削除", key=f"del_{i}"):
        st.session_state.hand.pop(i)
        st.rerun()

if st.button("全削除"):
    st.session_state.hand = []

# =========================
# 鳴き
# =========================
st.sidebar.subheader("鳴き")

pon = st.sidebar.selectbox("ポン", tiles_all)
if st.sidebar.button("ポン追加"):
    st.session_state.melds.append([pon]*3)

kan = st.sidebar.selectbox("カン", tiles_all)
if st.sidebar.button("カン追加"):
    st.session_state.melds.append([kan]*4)

chi_base = st.sidebar.selectbox("チー開始", ["1","2","3","4","5","6","7"])
chi_suit = st.sidebar.selectbox("種別", ["m","p","s"])

if st.sidebar.button("チー追加"):
    n = int(chi_base)
    st.session_state.melds.append(
        [f"{n}{chi_suit}", f"{n+1}{chi_suit}", f"{n+2}{chi_suit}"]
    )

st.sidebar.write("副露:")
for i, m in enumerate(st.session_state.melds):
    col1, col2 = st.sidebar.columns([3,1])
    col1.write(m)
    if col2.button("削除", key=f"meld_del_{i}"):
        st.session_state.melds.pop(i)
        st.rerun()

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
            honors += {"東":"1","南":"2","西":"3","北":"4","白":"5","發":"6","中":"7"}[t]

    return TilesConverter.string_to_136_array(
        man=man, pin=pin, sou=sou, honors=honors
    )

def build_melds():
    melds = []
    for m in st.session_state.melds:
        tiles136 = convert_tiles(m)
        if len(m)==3:
            meld_type = Meld.PON if m[0]==m[1] else Meld.CHI
        else:
            meld_type = Meld.KAN
        melds.append(Meld(meld_type, tiles136))
    return melds

def wind_to_int(w):
    return {"東":0,"南":1,"西":2,"北":3}[w]

def count_dora():
    tiles = [t for t, _ in st.session_state.hand]
    for m in st.session_state.melds:
        tiles += m

    total = sum(tiles.count(d) for d in dora_tiles)
    if riichi:
        total += sum(tiles.count(d) for d in ura_tiles)
    return total

# =========================
# 計算
# =========================
st.subheader("点数計算")

if st.session_state.hand:
    win_tile = st.selectbox("和了牌", [t for t, _ in st.session_state.hand])

if st.button("計算"):
    try:
        melds = build_melds()
        expected = 14 - len(melds)*3

        if len(st.session_state.hand) != expected:
            st.error(f"手牌は{expected}枚必要")
            st.stop()

        tiles136 = convert_tiles([t for t, _ in st.session_state.hand])
        win_tile136 = convert_tiles([win_tile])[0]

        calc = HandCalculator()
        result = calc.estimate_hand_value(
            tiles=tiles136,
            win_tile=win_tile136,
            melds=melds,
            config=HandConfig(
                is_riichi=riichi,
                is_ippatsu=ippatsu,
                is_tsumo=is_tsumo,
                player_wind=wind_to_int(self_wind),
                round_wind=wind_to_int(field_wind)
            )
        )

        if result.error:
            st.error(result.error)
            st.stop()

        red = sum(1 for _, r in st.session_state.hand if r)
        dora = count_dora()
        total_han = result.han + red + dora

        cost = result.cost
        is_dealer = (self_wind == "東")

        st.write("## 結果")

        # =========================
        # ロン
        # =========================
        if win_type == "ロン":
            total = cost['main'] + honba * 300
            st.write(f"ロン（{'親' if is_dealer else '子'}）: {cost['main']}")
            st.write(f"👉 最終獲得点: {total}")

        # =========================
        # ツモ
        # =========================
        else:
            if cost['additional'] > 0:
                # 子ツモ
                child = cost['additional'] * 2
                parent = cost['main'] * 2

                st.write(f"ツモ（子）: {child} / {parent}")

                total = parent + child * 2 + honba * 300

            else:
                # 親ツモ
                pay = cost['main'] * 2
                st.write(f"ツモ（親）: {pay}オール")

                total = pay * 3 + honba * 300

            st.write(f"👉 最終獲得点: {total}")

        st.write("翻:", total_han)
        st.write("符:", result.fu)

        st.write("役:")
        for y in result.yaku:
            st.write("-", y.name)

    except Exception as e:
        st.error(str(e))
