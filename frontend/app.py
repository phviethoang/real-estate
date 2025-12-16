import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from map_visualization import create_price_heatmap, create_price_per_square_heatmap
import requests
from typing import List, Dict, Optional
import asyncio
from typing import Any
import json
import uuid
import re
from dashboard_utils import *
from auth_utils import *
from chat_utils import *

BASE_URL = "http://localhost:8000"


def init_auth_state():
    if "is_authenticated" not in st.session_state:
        st.session_state.is_authenticated = False
    if "current_user" not in st.session_state:
        st.session_state.current_user = None
    if "full_name" not in st.session_state:
        st.session_state.full_name = None

def login(email, password):
    if email and password and is_valid_email(email):
        try:
            user = login_api(email, password)
            if user:
                st.session_state.is_authenticated = True
                st.session_state.current_user = user["email"]
                st.session_state.full_name = user["name"]
                return True
        except Exception as e:
            st.error(f"Lỗi kết nối: {str(e)}")
            print(f"Lỗi kết nối: {str(e)}")
    return False

def register(email, password, confirm_password, full_name):
    if email and password and password == confirm_password and full_name and is_valid_email(email):
        result = register_api(full_name, email, password)
        if "error" not in result:
            st.session_state.is_authenticated = True
            st.session_state.current_user = email
            st.session_state.full_name = full_name
            return True
        else:
            st.error(result["error"])
    return False

def logout():
    st.session_state.is_authenticated = False
    st.session_state.current_user = None

def load_chat_history():
    if not st.session_state.is_authenticated:
        return []

    if "chat_history" not in st.session_state:
        chats = get_chat_history_api(st.session_state.current_user)
        st.session_state.chat_history = chats
    else:
        chats = get_chat_history_api(st.session_state.current_user)
        st.session_state.chat_history = chats

    return st.session_state.chat_history

def save_chat_history():
    if st.session_state.messages and st.session_state.is_authenticated:
        chat_data = {
            "chat_id": st.session_state.current_chat_id,
            "chat_title": st.session_state.current_chat_title,
            "messages": st.session_state.messages
        }
        save_chat_history_api(
            st.session_state.current_user,
            st.session_state.current_chat_id,
            st.session_state.current_chat_title,
            st.session_state.messages
        )
        existing_chat = next((chat for chat in st.session_state.chat_history if chat["chat_id"] == st.session_state.current_chat_id), None)
        if existing_chat:
            existing_chat.update(chat_data)
        else:
            st.session_state.chat_history.append(chat_data)

def create_new_chat():
    st.session_state.messages = []
    st.session_state.current_chat_id = str(uuid.uuid4())
    st.session_state.current_chat_title = f"Cuộc hội thoại mới {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    save_chat_history()

def load_chat(chat_id):
    chat = get_chat_by_id_api(chat_id)
    if chat:
        st.session_state.messages = chat["messages"]
        st.session_state.current_chat_id = chat["chat_id"]
        st.session_state.current_chat_title = chat["chat_title"]

def run_async(coroutine):
    loop = asyncio.get_event_loop()
    if loop.is_running():
        return asyncio.run_coroutine_threadsafe(coroutine, loop).result()
    else:
        return loop.run_until_complete(coroutine)

st.set_page_config(page_title="Chatbot", layout="wide")

st.markdown("""
    <style>
    .main > div {
        padding-top: 1rem;
    }
    .stSidebar {
        padding-top: 1rem;
    }
    .stChatMessage {
        padding: 0.5rem 0;
    }
    .stChatInput {
        padding-top: 0.5rem;
    }
    .stMarkdown {
        padding: 0.5rem 0;
    }
    </style>
""", unsafe_allow_html=True)

init_auth_state()

st.sidebar.title("Điều hướng")

if st.session_state.is_authenticated:
    st.sidebar.success(f"Xin chào, {st.session_state.full_name}!")
    if st.sidebar.button("Đăng xuất"):
        logout()
        st.rerun()

if not st.session_state.is_authenticated:
    page = st.sidebar.radio("Chọn trang", ["Đăng nhập", "Đăng ký"])
else:
    page = st.sidebar.radio("Chọn trang", ["Chatbot", "Dashboard"])

if page == "Đăng nhập":
    st.title("🔐 Đăng nhập")

    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Mật khẩu", type="password")
        submit = st.form_submit_button("Đăng nhập")

        if submit:
            print("gửi api")
            if not is_valid_email(email):
                st.error("Email không hợp lệ!")
            elif login(email, password):
                st.success("Đăng nhập thành công!")
                st.rerun()
            else:
                st.error("Email hoặc mật khẩu không đúng!")

elif page == "Đăng ký":
    st.title("📝 Đăng ký")

    with st.form("register_form"):
        full_name = st.text_input("Tên của bạn")
        email = st.text_input("Email")
        password = st.text_input("Mật khẩu", type="password")
        confirm_password = st.text_input("Xác nhận mật khẩu", type="password")
        submit = st.form_submit_button("Đăng ký")

        if submit:
            if not is_valid_email(email):
                st.error("Email không hợp lệ!")
            elif register(email, password, confirm_password, full_name):
                st.success("Đăng ký thành công!")
                st.rerun()
            else:
                st.error("Vui lòng nhập đầy đủ thông tin và mật khẩu phải khớp!")

elif page == "Chatbot":
    st.title("🤖 Chatbot")

    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "current_chat_id" not in st.session_state:
        st.session_state.current_chat_id = str(uuid.uuid4())
    if "current_chat_title" not in st.session_state:
        st.session_state.current_chat_title = f"Cuộc hội thoại mới {datetime.now().strftime('%d/%m/%Y %H:%M')}"

    with st.sidebar:
        st.title("Lịch sử hội thoại")

        if st.button("➕ Cuộc hội thoại mới", key="new_chat_button"):
            create_new_chat()
            st.rerun()

        st.markdown("---")

        chat_history = load_chat_history()
        for idx, chat in enumerate(chat_history):
            if st.button(
                chat.get("chat_title", "Cuộc hội thoại không có tiêu đề"),
                key=f"chat_button_{chat['chat_id']}"
            ):
                load_chat(chat["chat_id"])
                st.rerun()


    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])


    if prompt := st.chat_input("Nhập tin nhắn của bạn..."):
        st.session_state.messages.append({"role": "user", "content": prompt, "user_id": st.session_state.current_user})
        with st.chat_message("user"):
            st.markdown(prompt)

        response = get_response(st.session_state.messages)

        with st.chat_message("assistant"):
            relevant_question = "\n".join(response["follow_up_questions"])
            final_response = response["real_estate_findings"] + "\n" + "# Phân tích: \n" + response["analytics_and_advice"] + "\n" + "# Câu hỏi có thể bạn quan tâm: \n" + relevant_question + "\n"
            st.markdown(final_response)
            st.session_state.messages.append({"role": "assistant", "content": final_response})

        if len(st.session_state.messages) == 2:
            name_conversation = get_conversation_name(st.session_state.messages)
            st.session_state.current_chat_title = name_conversation

        # Lưu lịch sử chat sau mỗi tin nhắn
        save_chat_history()
        # Cập nhật lại giao diện để hiển thị cuộc hội thoại mới trong sidebar
        if len(st.session_state.messages) == 2:
            st.rerun()
else:
    st.title("📊 Dashboard")

    estate_type = st.radio(
        "Chọn loại nhà:",
        ["Nhà phố", "Nhà riêng", "Chung cư", "Biệt thự"],
        horizontal=True
    )

    estate_type_mapping = {
        "Nhà phố": "nhapho",
        "Nhà riêng": "nharieng",
        "Chung cư": "chungcu",
        "Biệt thự": "bietthu"
    }
    estate_type_index = estate_type_mapping.get(estate_type, "nhapho")

    try:
        price_by_district_df = price_by_district(estate_type_index)
        price_per_square_df = price_per_square_by_district(estate_type_index)
        area_by_district_df = area_by_district(estate_type_index)

        col1, col2, col3 = st.columns(3)

        with col1:
            fig_price_district = px.bar(price_by_district_df,
                                        x='Quận/Huyện',
                                        y='Giá Trung Bình (VNĐ)',
                                        title=f'Giá Trung Bình {estate_type} Theo Quận/Huyện Hà Nội',
                                        labels={'Quận/Huyện': 'Quận/Huyện',
                                                'Giá Trung Bình (VNĐ)': 'Giá Trung Bình (VNĐ)'})

            fig_price_district.update_layout(
                xaxis_tickangle=-45,
                showlegend=False,
                height=400,
                margin=dict(t=50, b=100)
            )

            st.plotly_chart(fig_price_district, use_container_width=True)

            st.subheader(f"Bảng giá trung bình theo quận/huyện ({estate_type})")
            st.dataframe(price_by_district_df, use_container_width=True)

        with col2:
            fig_price_per_square = px.bar(price_per_square_df,
                                          x='Quận/Huyện',
                                          y='Giá Trung Bình/m² (VNĐ)',
                                          title=f'Giá Trung Bình/m² {estate_type} Theo Quận/Huyện Hà Nội',
                                          labels={'Quận/Huyện': 'Quận/Huyện',
                                                  'Giá Trung Bình/m² (VNĐ)': 'Giá Trung Bình/m² (VNĐ)'})

            fig_price_per_square.update_layout(
                xaxis_tickangle=-45,
                showlegend=False,
                height=400,
                margin=dict(t=50, b=100)
            )

            st.plotly_chart(fig_price_per_square, use_container_width=True)

            st.subheader(f"Bảng giá trung bình/m² theo quận/huyện ({estate_type})")
            st.dataframe(price_per_square_df, use_container_width=True)

        with col3:
            fig_area_district = px.bar(area_by_district_df,
                                       x='Quận/Huyện',
                                       y='Diện tích trung bình (m²)',
                                       title=f'Diện Tích Trung Bình {estate_type} Theo Quận/Huyện Hà Nội',
                                       labels={'Quận/Huyện': 'Quận/Huyện',
                                               'Diện tích trung bình (m²)': 'Diện tích trung bình (m²)'})

            fig_area_district.update_layout(
                xaxis_tickangle=-45,
                showlegend=False,
                height=400,
                margin=dict(t=50, b=100)
            )

            st.plotly_chart(fig_area_district, use_container_width=True)

            st.subheader(f"Bảng diện tích trung bình theo quận/huyện ({estate_type})")
            st.dataframe(area_by_district_df, use_container_width=True)

        st.markdown("---")
        st.subheader("Biểu đồ giá theo thời gian")

        selected_district = st.selectbox(
            "Chọn quận/huyện:",
            options=price_by_district_df['Quận/Huyện'].tolist()
        )

        time_col1, time_col2 = st.columns(2)

        with time_col1:
            price_by_date_df = price_by_date(estate_type_index, selected_district)

            price_by_date_df_filtered = price_by_date_df[price_by_date_df['Giá Trung Bình (VNĐ)'] != 0]

            fig_price_trend = px.line(
                price_by_date_df_filtered,
                x='Ngày',
                y='Giá Trung Bình (VNĐ)',
                title=f'Giá Trung Bình {estate_type} Theo Thời Gian - {selected_district}',
                labels={'Ngày': 'Ngày',
                        'Giá Trung Bình (VNĐ)': 'Giá Trung Bình (VNĐ)'}
            )

            fig_price_trend.update_layout(
                xaxis_tickangle=-45,
                showlegend=False,
                height=400,
                margin=dict(t=50, b=100)
            )

            st.plotly_chart(fig_price_trend, use_container_width=True)

            st.subheader(f"Bảng giá theo thời gian - {selected_district}")
            st.dataframe(price_by_date_df_filtered, use_container_width=True)

        with time_col2:
            price_per_square_by_date_df = price_per_square_by_date(estate_type_index, selected_district)

            price_per_square_by_date_df_filtered = price_per_square_by_date_df[
                price_per_square_by_date_df['Giá Trung Bình/m² (VNĐ)'] != 0]

            fig_price_per_square_trend = px.line(
                price_per_square_by_date_df_filtered,
                x='Ngày',
                y='Giá Trung Bình/m² (VNĐ)',
                title=f'Giá Trung Bình/m² {estate_type} Theo Thời Gian - {selected_district}',
                labels={'Ngày': 'Ngày',
                        'Giá Trung Bình/m² (VNĐ)': 'Giá Trung Bình/m² (VNĐ)'}
            )

            fig_price_per_square_trend.update_layout(
                xaxis_tickangle=-45,
                showlegend=False,
                height=400,
                margin=dict(t=50, b=100)
            )

            st.plotly_chart(fig_price_per_square_trend, use_container_width=True)

            st.subheader(f"Bảng giá/m² theo thời gian - {selected_district}")
            st.dataframe(price_per_square_by_date_df_filtered, use_container_width=True)

        st.markdown("---")
        st.subheader("Bản đồ nhiệt giá theo quận/huyện")

        map_col1, map_col2 = st.columns(2)

        with map_col1:
            st.subheader("Bản đồ nhiệt giá trung bình")
            price_map = create_price_heatmap(price_by_district_df)
            st.components.v1.html(price_map._repr_html_(), height=500)

        with map_col2:
            st.subheader("Bản đồ nhiệt giá trung bình/m²")
            price_per_square_map = create_price_per_square_heatmap(price_per_square_df)
            st.components.v1.html(price_per_square_map._repr_html_(), height=500)

    except Exception as e:
        st.error(f"Có lỗi xảy ra khi kết nối đến Elasticsearch: {str(e)}")
        st.info("Vui lòng kiểm tra kết nối và thử lại sau.")

if __name__ == "__main__":
    st.write("")