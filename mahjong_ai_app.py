import streamlit as st
from PIL import Image
import numpy as np

st.set_page_config(layout="wide", page_title="麻雀符計算AI")
st.title("🀄 日本プロ麻雀符計算AI")
st.markdown("赤ドラ・連風・役満複合・全ルール対応")

# サイドバー
st.sidebar.header("状況")
tsumo = st.sidebar.radio("和了", ["ロン", "ツモ"])
riichi = st.sidebar.checkbox("立直", True)
ippatsu = st.sidebar.checkbox("一発")
haitei = st.sidebar.checkbox("海底/河底")
ling_shang = st.sidebar.checkbox("嶺上開花")
rob_gang = st.sidebar.checkbox("搶槓")

field_wind = st.sidebar.selectbox("場風", ["東", "南", "西", "北"])
player_wind = st.sidebar.selectbox("自風", ["東", "南", "西", "北"])

dora = st.sidebar.slider("表ドラ", 0, 5, 0)
ura_dora = st.sidebar.slider("裏ドラ", 0, 5, 0)
tenbou = st.sidebar.slider("積棒", 0, 50, 0)

st.sidebar.header("役牌修正")
yakuhai_count = st.sidebar.slider("役牌数", 0
