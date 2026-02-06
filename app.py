import sys
import io

# ★最重要：Streamlitなどのライブラリを読み込む「前」に設定を変更する★
# これでWindowsのターミナルを再起動しても日本語エラーが出なくなります
# クラウド上で禁止されている場合は無視してエラーを防ぐ安全装置付きです
try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
except Exception:
    pass
# -------------------------------------------------------

# ここからライブラリの読み込み
import streamlit as st
import os
from google import genai
from google.genai import types
from dotenv import load_dotenv
from PIL import Image

# 1. アプリの基本設定
load_dotenv()
st.set_page_config(page_title="医学部合格AI", page_icon="🩺")

st.title("🩺 医学部受験対策 AI家庭教師")
st.caption("東大・順天堂・慶應などの過去問PDFや、図表の解説も可能です")

# 2. APIキーの準備（PCとクラウドの両方に対応）
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    # PCになければクラウドの金庫(Secrets)を探す
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
    except:
        pass

if not api_key:
    st.error("APIキーが見つかりません。PCなら.env、クラウドならSecretsの設定を確認してください。")
else:
    client = genai.Client(api_key=api_key)

# 3. 会話の履歴を保存する場所
if "history" not in st.session_state:
    st.session_state.history = []
    st.session_state.history.append({"role": "model", "text": "こんにちは！PDFの過去問や、画像の解説も任せてください。"})

# 4. サイドバー（ファイルアップロード機能）
with st.sidebar:
    st.header("📂 資料のアップロード")
    uploaded_file = st.file_uploader("問題(PDF/画像)をここにドラッグ", type=["jpg", "png", "jpeg", "pdf"])
    
    user_content = None
    
    if uploaded_file:
        # PDFの場合
        if uploaded_file.type == "application/pdf":
            st.success(f"📄 PDFファイルを読み込みました: {uploaded_file.name}")
            # PDFをAIが読める形式に変換
            user_content = types.Part.from_bytes(
                data=uploaded_file.getvalue(),
                mime_type="application/pdf"
            )
        # 画像の場合
        else:
            user_content = Image.open(uploaded_file)
            st.image(user_content, caption="読み込んだ画像", use_container_width=True)

# 5. チャット履歴の表示
for message in st.session_state.history:
    with st.chat_message(message["role"]):
        st.write(message["text"])

# 6. チャット入力とAIの回答処理
prompt = st.chat_input("質問を入力してください...")

if prompt:
    # ユーザーの質問を表示
    with st.chat_message("user"):
        st.write(prompt)
    st.session_state.history.append({"role": "user", "text": prompt})

    # AIの回答処理
    with st.chat_message("assistant"):
        with st.spinner("資料を読み込んで考え中..."):
            try:
                system_instruction = """
                あなたは医学部受験のプロ家庭教師です。
                PDFや画像が提供された場合は、その内容を詳細に分析して解説してください。
                数式はLaTeX形式ではなく、読みやすいテキストで表現してください。
                """

                # テキストとファイルをセットにする
                contents = [prompt]
                if user_content:
                    # ファイルがある場合は先頭に追加
                    contents.insert(0, user_content)

                if 'client' in locals():
                    response = client.models.generate_content(
                        model="gemini-flash-latest",
                        contents=contents,
                        config=types.GenerateContentConfig(
                            system_instruction=system_instruction,
                            temperature=0.7,
                        )
                    )
                    st.write(response.text)
                    st.session_state.history.append({"role": "model", "text": response.text})
            
            except Exception as e:
                st.error(f"エラーが発生しました: {e}")
