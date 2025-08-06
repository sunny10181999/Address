import streamlit as st
import pandas as pd
from Address_choice import process_addresses

st.set_page_config(page_title="📍 地址抽取智能工具", layout="wide")
st.title("📍 地址抽取智能工具")

# ---------- 侧边栏 ----------
with st.sidebar:
    api_key = st.text_input("请输入 API 密钥：", type="password")
    st.markdown("[获取API密钥)](https://help.aliyun.com/zh/model-studio/developer-reference/get-api-key?)")

# ---------- 文件上传 ----------
uploaded_file = st.file_uploader("上传包含「序号,地址」两列的 CSV 文件：", type=["csv"])
df_input = None
if uploaded_file is not None:
    df_input = pd.read_csv(uploaded_file)
    st.session_state["df"] = df_input
    with st.expander("原始数据预览"):
        st.dataframe(df_input)

# ---------- 初始化 session_state ----------
if "result" not in st.session_state:
    st.session_state.result = None
if "output_path" not in st.session_state:
    st.session_state.output_path = None

# ---------- 解析按钮 ----------
button = st.button("生成地址解析文件")

if button:
    if not api_key:
        st.warning("请输入你的 API 密钥")
    elif "df" not in st.session_state:
        st.warning("请先上传数据文件")
    else:
        # 取出地址列
        address_list = st.session_state["df"]["地址"].astype(str).tolist()
        output_path = "parsed_addresses.csv"
        with st.spinner("AI 正在思考中，请稍等…"):
            process_addresses(address_list, api_key, output_path)
        # 保存结果到 session_state
        st.session_state.result = pd.read_csv(output_path)
        st.session_state.output_path = output_path

# ---------- 结果展示与下载 ----------
if st.session_state.result is not None:
    st.success("解析完成！")
    st.dataframe(st.session_state.result)
    # 下载按钮
    with open(st.session_state.output_path, "rb") as f:
        st.download_button(
            label="📥 下载解析结果 CSV",
            data=f,
            file_name="parsed_addresses.csv",
            mime="text/csv"
        )