import os
import pandas as pd
import streamlit as st

st.set_page_config(page_title="113歷屆國文考卷系統", layout="wide")

# =========================
# 基本設定
# =========================
QUESTION_FILE = "113歷屆.csv"
OPTION_FILE = "113歷屆選項.csv"
EXPLANATION_FILE = "113歷屆詳解.csv"
IMAGE_FOLDER = "images"


# =========================
# 小工具函式
# =========================
def safe_str(value):
    if pd.isna(value):
        return ""
    return str(value).strip()


def image_path(filename):
    filename = safe_str(filename)
    if filename == "":
        return None

    path = os.path.join(IMAGE_FOLDER, filename)
    if os.path.exists(path):
        return path
    return None


def show_text_and_image(text, img_file, width=400):
    text = safe_str(text)
    img_path = image_path(img_file)

    if text != "":
        st.write(text)

    if img_path is not None:
        st.image(img_path, width=width)


# =========================
# 讀取資料
# =========================
@st.cache_data
def load_data():
    questions_df = pd.read_csv(QUESTION_FILE).fillna("")
    options_df = pd.read_csv(OPTION_FILE).fillna("")
    explanations_df = pd.read_csv(EXPLANATION_FILE).fillna("")

    # 刪掉會衝突的 id
    options_df = options_df.drop(columns=["id"], errors="ignore")
    explanations_df = explanations_df.drop(columns=["id"], errors="ignore")

    # 合併資料
    df = questions_df.merge(
        options_df,
        left_on="id",
        right_on="question_id",
        how="left"
    )

    df = df.merge(
        explanations_df,
        left_on="id",
        right_on="question_id",
        how="left",
        suffixes=("", "_exp")
    )

    return df.fillna("")


# =========================
# 主畫面
# =========================
st.title("113歷屆國文考卷系統")

try:
    df = load_data()
except Exception as e:
    st.error(f"讀取檔案失敗：{e}")
    st.stop()

st.write(f"目前共有 {len(df)} 題")

# 初始化作答紀錄
if "answers" not in st.session_state:
    st.session_state.answers = {}

st.divider()

# =========================
# 顯示整份考卷
# =========================
for i, row in df.iterrows():
    q_num = i + 1

    st.subheader(f"第 {q_num} 題")

    # 顯示題目基本資訊
    col_info1, col_info2, col_info3 = st.columns(3)
    with col_info1:
        st.caption(f"題號：{safe_str(row.get('id', ''))}")
    with col_info2:
        st.caption(f"年份：{safe_str(row.get('year', ''))}")
    with col_info3:
        st.caption(f"分類：{safe_str(row.get('subject', ''))}")

    # 題目文字
    title = safe_str(row.get("title", ""))
    description = safe_str(row.get("description", ""))
    q_image = safe_str(row.get("image", ""))

    if title != "":
        st.write(f"**題目：** {title}")

    if description != "":
        st.write(description)

    # 題目圖片
    q_img_path = image_path(q_image)
    if q_img_path is not None:
        st.image(q_img_path, width=500)

    st.markdown("**選項：**")

    # 先把四個選項完整顯示出來
    option_labels = ["A", "B", "C", "D"]
    for label in option_labels:
        option_text = safe_str(row.get(f"選項{label}", ""))
        option_img = safe_str(row.get(f"{label}_image", ""))

        st.write(f"{label}.")
        if option_text != "":
            st.write(option_text)

        option_img_path = image_path(option_img)
        if option_img_path is not None:
            st.image(option_img_path, width=350)

    # 作答
    saved_answer = st.session_state.answers.get(row["id"], None)

    user_choice = st.radio(
        f"請選擇第 {q_num} 題答案",
        ["A", "B", "C", "D"],
        index=["A", "B", "C", "D"].index(saved_answer) if saved_answer in ["A", "B", "C", "D"] else 0,
        key=f"radio_{row['id']}"
    )

    st.session_state.answers[row["id"]] = user_choice

    st.divider()

# =========================
# 交卷
# =========================
if st.button("提交整份考卷", type="primary"):
    score = 0
    total = len(df)

    st.header("作答結果")

    for i, row in df.iterrows():
        q_num = i + 1
        qid = row["id"]

        correct_answer = safe_str(row.get("answer", "")).upper()
        user_answer = safe_str(st.session_state.answers.get(qid, "")).upper()

        st.subheader(f"第 {q_num} 題")

        if user_answer == correct_answer:
            score += 1
            st.success(f"答對了！你的答案：{user_answer}")
        else:
            st.error(f"答錯了！你的答案：{user_answer}；正確答案：{correct_answer}")

        # 顯示正確選項內容
        correct_text = safe_str(row.get(f"選項{correct_answer}", ""))
        correct_img = safe_str(row.get(f"{correct_answer}_image", ""))

        st.markdown("**正確答案內容：**")
        if correct_text != "":
            st.write(correct_text)

        correct_img_path = image_path(correct_img)
        if correct_img_path is not None:
            st.image(correct_img_path, width=350)

        # 詳解
        explanation = safe_str(row.get("content", ""))
        if explanation != "":
            st.markdown("**詳解：**")
            st.write(explanation)

        st.divider()

    st.subheader(f"總分：{score} / {total}")