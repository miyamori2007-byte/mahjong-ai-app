import streamlit as st
from ultralytics import YOLO
from PIL import Image
import os

st.set_page_config(page_title="麻雀符計算AI", layout="wide")

st.title("🀄 麻雀牌認識・符計算AI")
st.markdown("---")

# サイドバー
st.sidebar.header("📸 撮影方法")
input_type = st.sidebar.radio("選択", ["カメラ", "画像投稿"])

model = YOLO("yolov8n.pt")

col1, col2 = st.columns([1,1])

with col1:
    st.header("入力")
    if input_type == "カメラ":
        img_file = st.camera_input("牌を撮影（14枚全体）")
    else:
        img_file = st.file_uploader("牌画像投稿", type=['jpg','png'])
        
    if img_file:
        image = Image.open(img_file)
        st.image(image, caption="牌配置", use_column_width=True)

with col2:
    if img_file:
        st.header("AI分析結果")
        # 牌認識
        results = model(img_file)
        tile_count = len(results[0].boxes)
        st.metric("検出牌数", tile_count, delta="14牌目標")
        
        # デモ符計算（将来的にmahjong.py）
        fu = 30 + (tile_count // 5) * 10
        han = min(2 + tile_count // 10, 13)
        st.metric("推定符", fu)
        st.metric("推定翻", han)
        
        st.success(f"🀄 {tile_count}枚認識 → 符{fu}・翻{han}")
        
        # 認識画像表示
        st.image(results[0].plot(), caption="検出枠")

st.markdown("---")
st.caption("大会デモ用 | 完全無料・自作AI")
