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
PROVINCES_LIST = [
    "An Giang", "Bà Rịa - Vũng Tàu", "Bắc Giang", "Bắc Kạn", "Bạc Liêu", 
    "Bắc Ninh", "Bến Tre", "Bình Định", "Bình Dương", "Bình Phước", 
    "Bình Thuận", "Cà Mau", "Cần Thơ", "Cao Bằng", "Đà Nẵng", 
    "Đắk Lắk", "Đắk Nông", "Điện Biên", "Đồng Nai", "Đồng Tháp", 
    "Gia Lai", "Hà Giang", "Hà Nam", "Hà Nội", "Hà Tĩnh", 
    "Hải Dương", "Hải Phòng", "Hậu Giang", "Hòa Bình", "TP. Hồ Chí Minh", 
    "Hưng Yên", "Khánh Hòa", "Kiên Giang", "Kon Tum", "Lai Châu", 
    "Lâm Đồng", "Lạng Sơn", "Lào Cai", "Long An", "Nam Định", 
    "Nghệ An", "Ninh Bình", "Ninh Thuận", "Phú Thọ", "Phú Yên", 
    "Quảng Bình", "Quảng Nam", "Quảng Ngãi", "Quảng Ninh", "Quảng Trị", 
    "Sóc Trăng", "Sơn La", "Tây Ninh", "Thái Bình", "Thái Nguyên", 
    "Thanh Hóa", "Thừa Thiên Huế", "Tiền Giang", "Trà Vinh", "Tuyên Quang", 
    "Vĩnh Long", "Vĩnh Phúc", "Yên Bái"
]

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
# else:
#     st.title("📊 Dashboard")

#     estate_type = st.radio(
#         "Chọn loại nhà:",
#         ["Nhà phố", "Nhà riêng", "Chung cư", "Biệt thự"],
#         horizontal=True
#     )

#     estate_type_mapping = {
#         "Nhà phố": "nhapho",
#         "Nhà riêng": "nharieng",
#         "Chung cư": "chungcu",
#         "Biệt thự": "bietthu"
#     }
#     estate_type_index = estate_type_mapping.get(estate_type, "nhapho")

#     try:
#         price_by_district_df = price_by_district(estate_type_index)
#         price_per_square_df = price_per_square_by_district(estate_type_index)
#         area_by_district_df = area_by_district(estate_type_index)

#         col1, col2, col3 = st.columns(3)

#         with col1:
#             fig_price_district = px.bar(price_by_district_df,
#                                         x='Quận/Huyện',
#                                         y='Giá Trung Bình (VNĐ)',
#                                         title=f'Giá Trung Bình {estate_type} Theo Quận/Huyện Hà Nội',
#                                         labels={'Quận/Huyện': 'Quận/Huyện',
#                                                 'Giá Trung Bình (VNĐ)': 'Giá Trung Bình (VNĐ)'})

#             fig_price_district.update_layout(
#                 xaxis_tickangle=-45,
#                 showlegend=False,
#                 height=400,
#                 margin=dict(t=50, b=100)
#             )

#             st.plotly_chart(fig_price_district, use_container_width=True)

#             st.subheader(f"Bảng giá trung bình theo quận/huyện ({estate_type})")
#             st.dataframe(price_by_district_df, use_container_width=True)

#         with col2:
#             fig_price_per_square = px.bar(price_per_square_df,
#                                           x='Quận/Huyện',
#                                           y='Giá Trung Bình/m² (VNĐ)',
#                                           title=f'Giá Trung Bình/m² {estate_type} Theo Quận/Huyện Hà Nội',
#                                           labels={'Quận/Huyện': 'Quận/Huyện',
#                                                   'Giá Trung Bình/m² (VNĐ)': 'Giá Trung Bình/m² (VNĐ)'})

#             fig_price_per_square.update_layout(
#                 xaxis_tickangle=-45,
#                 showlegend=False,
#                 height=400,
#                 margin=dict(t=50, b=100)
#             )

#             st.plotly_chart(fig_price_per_square, use_container_width=True)

#             st.subheader(f"Bảng giá trung bình/m² theo quận/huyện ({estate_type})")
#             st.dataframe(price_per_square_df, use_container_width=True)

#         with col3:
#             fig_area_district = px.bar(area_by_district_df,
#                                        x='Quận/Huyện',
#                                        y='Diện tích trung bình (m²)',
#                                        title=f'Diện Tích Trung Bình {estate_type} Theo Quận/Huyện Hà Nội',
#                                        labels={'Quận/Huyện': 'Quận/Huyện',
#                                                'Diện tích trung bình (m²)': 'Diện tích trung bình (m²)'})

#             fig_area_district.update_layout(
#                 xaxis_tickangle=-45,
#                 showlegend=False,
#                 height=400,
#                 margin=dict(t=50, b=100)
#             )

#             st.plotly_chart(fig_area_district, use_container_width=True)

#             st.subheader(f"Bảng diện tích trung bình theo quận/huyện ({estate_type})")
#             st.dataframe(area_by_district_df, use_container_width=True)

# ... (Phần code trước đó giữ nguyên)
else:
    st.title("📊 Dashboard Phân Tích")
    
    
    selected_province = st.selectbox(
        "Chọn Tỉnh/Thành phố:",
        options=PROVINCES_LIST, 
        index=PROVINCES_LIST.index("Hà Nội"), # Mặc định chọn Hà Nội
        placeholder="Gõ tên tỉnh để tìm kiếm..."
    )
    if "current_province" not in st.session_state:
        st.session_state.current_province = ""

    if selected_province != st.session_state.current_province:
        # Gọi hàm wrapper POST
        success = set_active_province(selected_province)
        
        if success:
            st.session_state.current_province = selected_province
            st.toast(f"Đã chuyển dữ liệu sang: {selected_province}", icon="✅")
            # Rerun để làm mới các biểu đồ bên dưới theo tỉnh mới
            st.rerun()

    st.subheader(f"🏙️Thống kê Giá và Diện tích các loại hình bất động sản tại từng khu vực ở **{selected_province}**") 
    # --- PHẦN 1: CHỌN LOẠI NHÀ GỌN GÀNG ---
    listing_type = st.radio("Chọn hình thức bất động sản:",
        ["Bán", "Cho thuê"],
        horizontal=True
    )
    estate_type = st.radio(
        "Chọn loại bất động sản:",
        ["Nhà mặt tiền", "Nhà riêng", "Chung cư", "Biệt thự", "Đất"],
        horizontal=True
    )
    
    # Hiển thị thông báo nhẹ nhàng thay vì nhồi vào tiêu đề biểu đồ
    st.info(f"📌 Đang hiển thị dữ liệu phân tích cho: **{listing_type} {estate_type}** tại **{selected_province}**")
    listing_type_mapping = {
        "Bán": "buy",
        "Cho thuê": "rent"
    }
    listing_type_index = listing_type_mapping.get(listing_type, "buy")

    estate_type_mapping = {
        "Nhà mặt tiền": "nhamatpho",
        "Nhà riêng": "nharieng",
        "Chung cư": "chungcu",
        "Biệt thự": "bietthu",
        "Đất": "dat"
    }
    estate_type_index = estate_type_mapping.get(estate_type, "nhamatpho")

    # Hàm nhỏ giúp đánh lại số thứ tự (STT) và ẩn Index gốc
    def clean_dataframe(df):
        df_new = df.copy()
        # Tạo cột STT chạy từ 1 đến hết
        df_new.insert(0, 'STT', range(1, len(df_new) + 1))
        return df_new
    def process_data(df, type_col):
            df_new = df.copy()
            
            # Xử lý cột Diện tích: Làm tròn đến hàng đơn vị (m2)
            if 'square' in df_new.columns: # Nếu tên cột raw là 'square'
                 df_new['square'] = df_new['square'].fillna(0).round(0).astype(int)
            # Hoặc nếu tên cột đã là tiếng Việt từ hàm BE trả về
            for col in df_new.columns:
                if "Diện tích" in col:
                    df_new[col] = df_new[col].fillna(0).round(0).astype(int)

            # Xử lý cột Giá: Làm tròn đến hàng nghìn (round -3) và chuyển về Int
            for col in df_new.columns:
                if "Giá" in col: # Áp dụng cho cả cột Giá TB và Giá/m2
                    df_new[col] = df_new[col].fillna(0).round(-3).astype(int)
                    # df_new[col] = df_new[col].apply(format_vnd)
            
            return df_new

    try:
        # PART 1
        # Lấy dữ liệu
        price_by_district_df = price_by_district(estate_type_index, listing_type_index)
        price_per_square_df = price_per_square_by_district(estate_type_index, listing_type_index)
        area_by_district_df = area_by_district(estate_type_index, listing_type_index)
        
        # Làm sạch & Làm tròn số liệu
        price_by_district_df = process_data(price_by_district_df, 'price')
        price_per_square_df = process_data(price_per_square_df, 'price_m2')
        area_by_district_df = process_data(area_by_district_df, 'area')

        col1, col2, col3 = st.columns(3)
        
        # --- CỘT 1: GIÁ TRUNG BÌNH ---
        with col1:
            # st.subheader("💰 Giá Trung Bình")
            fig_price_district = px.bar(
                price_by_district_df,
                x='Quận/Huyện',
                y='Giá Trung Bình (VNĐ)',
                title='Giá Trung Bình',
                labels={'Quận/Huyện': 'Quận', 'Giá Trung Bình (VNĐ)': 'Mức giá'}
            )
            fig_price_district.update_layout(xaxis_tickangle=-45, showlegend=False, height=350, margin=dict(t=40, b=0, l=0, r=0))
            st.plotly_chart(fig_price_district, use_container_width=True)
            
            # Hiển thị DataFrame với Column Config
            st.dataframe(
                clean_dataframe(price_by_district_df),
                use_container_width=True,
                hide_index=True, # Ẩn index đi để đỡ rối mắt khi sort
                column_config={
                    "Giá Trung Bình (VNĐ)": st.column_config.NumberColumn(
                        "Giá TB (VNĐ)",
                    )
                }
            )

        # --- CỘT 2: ĐƠN GIÁ / M2 ---
        with col2:
            # st.subheader("📉 Đơn Giá / m²")
            fig_price_per_square = px.bar(
                price_per_square_df,
                x='Quận/Huyện',
                y='Giá Trung Bình/m² (VNĐ)',
                title='Đơn Giá / m²',
                labels={'Quận/Huyện': 'Quận', 'Giá Trung Bình/m² (VNĐ)': 'Đơn giá/m²'}
            )
            fig_price_per_square.update_layout(xaxis_tickangle=-45, showlegend=False, height=350, margin=dict(t=40, b=0, l=0, r=0))
            st.plotly_chart(fig_price_per_square, use_container_width=True)

            st.dataframe(
                clean_dataframe(price_per_square_df),
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Giá Trung Bình/m² (VNĐ)": st.column_config.NumberColumn(
                        "Giá/m² (VNĐ)",
                    )
                }
            )

        # --- CỘT 3: DIỆN TÍCH ---
        with col3:
            # st.subheader("📐 Diện Tích")
            fig_area_district = px.bar(
                area_by_district_df,
                x='Quận/Huyện',
                y='Diện tích trung bình (m²)',
                title='Diện Tích',
                labels={'Quận/Huyện': 'Quận', 'Diện tích trung bình (m²)': 'Diện tích (m²)'}
            )
            fig_area_district.update_layout(xaxis_tickangle=-45, showlegend=False, height=350, margin=dict(t=40, b=0, l=0, r=0))
            st.plotly_chart(fig_area_district, use_container_width=True)

            st.dataframe(
                clean_dataframe(area_by_district_df),
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Diện tích trung bình (m²)": st.column_config.NumberColumn(
                        "Diện tích (m²)",
                        format="%d", # Thêm hậu tố m2 cho đẹp
                    )
                }
            )



        # # PART 2
        # st.markdown("---")
        # st.subheader("Biểu đồ giá theo thời gian")

        # selected_district = st.selectbox(
        #     "Chọn quận/huyện:",
        #     options=price_by_district_df['Quận/Huyện'].tolist()
        # )

        # time_col1, time_col2 = st.columns(2)

        # with time_col1:
        #     price_by_date_df = price_by_date(estate_type_index, selected_district)

        #     price_by_date_df_filtered = price_by_date_df[price_by_date_df['Giá Trung Bình (VNĐ)'] != 0]

        #     fig_price_trend = px.line(
        #         price_by_date_df_filtered,
        #         x='Ngày',
        #         y='Giá Trung Bình (VNĐ)',
        #         title=f'Giá Trung Bình {estate_type} Theo Thời Gian - {selected_district}',
        #         labels={'Ngày': 'Ngày',
        #                 'Giá Trung Bình (VNĐ)': 'Giá Trung Bình (VNĐ)'}
        #     )

        #     fig_price_trend.update_layout(
        #         xaxis_tickangle=-45,
        #         showlegend=False,
        #         height=400,
        #         margin=dict(t=50, b=100)
        #     )

        #     st.plotly_chart(fig_price_trend, use_container_width=True)

        #     st.subheader(f"Bảng giá theo thời gian - {selected_district}")
        #     st.dataframe(price_by_date_df_filtered, use_container_width=True)

        # with time_col2:
        #     price_per_square_by_date_df = price_per_square_by_date(estate_type_index, selected_district)

        #     price_per_square_by_date_df_filtered = price_per_square_by_date_df[
        #         price_per_square_by_date_df['Giá Trung Bình/m² (VNĐ)'] != 0]

        #     fig_price_per_square_trend = px.line(
        #         price_per_square_by_date_df_filtered,
        #         x='Ngày',
        #         y='Giá Trung Bình/m² (VNĐ)',
        #         title=f'Giá Trung Bình/m² {estate_type} Theo Thời Gian - {selected_district}',
        #         labels={'Ngày': 'Ngày',
        #                 'Giá Trung Bình/m² (VNĐ)': 'Giá Trung Bình/m² (VNĐ)'}
        #     )

        #     fig_price_per_square_trend.update_layout(
        #         xaxis_tickangle=-45,
        #         showlegend=False,
        #         height=400,
        #         margin=dict(t=50, b=100)
        #     )

        #     st.plotly_chart(fig_price_per_square_trend, use_container_width=True)

        #     st.subheader(f"Bảng giá/m² theo thời gian - {selected_district}")
        #     st.dataframe(price_per_square_by_date_df_filtered, use_container_width=True)

        st.markdown("---")
        st.subheader(f"📈 Biểu đồ biến động giá theo thời gian tại từng khu vực ở **{selected_province}**")

        selected_district = st.selectbox(
            "Chọn quận/huyện để xem lịch sử giá:",
            options=price_by_district_df['Quận/Huyện'].tolist()
        )
        
       # --- DÒNG 2: CHỌN NGÀY (Tách 2 ô riêng biệt trên cùng 1 dòng) ---
        date_col1, date_col2 = st.columns(2)
        
        # --- SỬA LỖI Ở ĐÂY ---
        # Dùng pd.Timestamp.now().date() thay vì datetime.date.today() để tránh lỗi import
        today = pd.Timestamp.now().date()
        first_day_of_month = today.replace(day=1)

        with date_col1:
            start_date = st.date_input(
                "📅 Từ ngày",
                value=first_day_of_month, # Mặc định là ngày mùng 1
                format="DD/MM/YYYY"
            )

        with date_col2:
            end_date = st.date_input(
                "📅 Đến ngày",
                value=today, # Mặc định là hôm nay
                format="DD/MM/YYYY"
            )

        # --- VALIDATION (KIỂM TRA LỖI) ---
        if start_date > end_date:
            st.error("⚠️ Lỗi: 'Từ ngày' không được lớn hơn 'Đến ngày'. Vui lòng chọn lại!")
            st.stop()

        # # Hiển thị thông báo xác nhận
        # st.info(
        #     f"📌 Dữ liệu: **{estate_type}** - **{selected_district}** "
        #     f"| Thời gian: **{start_date.strftime('%d/%m/%Y')}** ➡ **{end_date.strftime('%d/%m/%Y')}**"
        # )
        # Hiển thị thông báo nhẹ nhàng thay vì nhồi vào tiêu đề biểu đồ
        st.info(f"📌 Đang hiển thị dữ liệu phân tích cho: **{listing_type} {estate_type}** tại **{selected_district}**, **{selected_province}** từ ngày  **{start_date.strftime('%d/%m/%Y')}** đến ngày **{end_date.strftime('%d/%m/%Y')}**")


        # 1. Hàm xử lý dữ liệu thời gian và làm tròn giá
        def process_time_data(df, price_col):
            df_new = df.copy()
            
            # Lọc bỏ giá trị 0
            df_new = df_new[df_new[price_col] != 0]
            
            # Chuyển đổi cột Ngày sang kiểu datetime chuẩn
            df_new['Ngày'] = pd.to_datetime(df_new['Ngày'])
            
            # Sắp xếp theo ngày tăng dần
            df_new = df_new.sort_values(by='Ngày')
            
            # Làm tròn giá tới hàng nghìn (-3) và chuyển về Int
            df_new[price_col] = df_new[price_col].fillna(0).round(-3).astype(int)
            
            return df_new

        # 2. Hàm hiển thị (Vẽ biểu đồ + Bảng)
        def hien_thi_theo_thoi_gian(container, df, x_col, y_col, title_chart, title_table, color_line):
            with container:
                # --- PHẦN BIỂU ĐỒ ---
                # Với biểu đồ, ta giữ nguyên kiểu datetime để Plotly vẽ trục X chuẩn xác
                fig = px.line(
                    df, 
                    x=x_col, 
                    y=y_col,
                    title=title_chart,
                    labels={x_col: 'Ngày', y_col: 'Mức giá (VNĐ)'},
                    markers=True # Thêm điểm tròn trên line cho dễ nhìn
                )
                
                fig.update_traces(line_color=color_line) # Đổi màu line cho phân biệt

                fig.update_layout(
                    xaxis_tickangle=-45,
                    showlegend=False,
                    height=400,
                    margin=dict(t=50, b=50),
                    # Quan trọng: Format trục X chỉ hiển thị ngày-tháng-năm
                    xaxis=dict(
                        tickformat="%d-%m-%Y",
                        dtick="D1",
                    )
                )
                st.plotly_chart(fig, use_container_width=True)

                # --- PHẦN BẢNG DỮ LIỆU ---
                st.subheader(title_table)
                
                # Tạo bản sao để format hiển thị cho bảng (String format)
                df_display = df.copy()
                # Chuyển ngày sang string dd-mm-yyyy
                df_display[x_col] = df_display[x_col].dt.strftime('%d-%m-%Y')

                st.dataframe(
                    df_display, 
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        x_col: st.column_config.TextColumn(
                            "Ngày",
                            width="medium"
                        ),
                        y_col: st.column_config.NumberColumn(
                            "Giá Trị (VNĐ)",
                        )
                    }
                )

        # --- LOGIC CHÍNH ---
        time_col1, time_col2 = st.columns(2)

        # Lấy dữ liệu thô
        price_by_date_df = price_by_date(estate_type_index, selected_district, start_date, end_date, listing_type_index)
        price_per_square_by_date_df = price_per_square_by_date(estate_type_index, selected_district, start_date, end_date, listing_type_index)

        # Xử lý làm tròn và lọc 0
        df_total_price = process_time_data(price_by_date_df, 'Giá Trung Bình (VNĐ)')
        df_m2_price = process_time_data(price_per_square_by_date_df, 'Giá Trung Bình/m² (VNĐ)')

        # Hiển thị Cột 1: Tổng giá
        hien_thi_theo_thoi_gian(
            time_col1,
            df_total_price,
            'Ngày',
            'Giá Trung Bình (VNĐ)',
            f'Tổng Giá Trung Bình',
            f'Bảng giá theo ngày',
            '#1f77b4' # Màu xanh dương
        )

        # Hiển thị Cột 2: Giá/m2
        hien_thi_theo_thoi_gian(
            time_col2,
            df_m2_price,
            'Ngày',
            'Giá Trung Bình/m² (VNĐ)',
            f'Giá Trung Bình/m²',
            f'Bảng giá/m² theo ngày',
            '#ff7f0e' # Màu cam (cho khác biệt)
        )



        # PART3

        st.markdown("---")
        st.subheader(f"Bản đồ nhiệt giá **{estate_type}** theo quận/huyện tại **{selected_province}**")

        map_col1, map_col2 = st.columns(2)

        with map_col1:
            st.subheader("Bản đồ nhiệt giá trung bình")
            price_map = create_price_heatmap(price_by_district_df, selected_province)
            st.components.v1.html(price_map._repr_html_(), height=500)

        with map_col2:
            st.subheader("Bản đồ nhiệt giá trung bình/m²")
            price_per_square_map = create_price_per_square_heatmap(price_per_square_df, selected_province)
            st.components.v1.html(price_per_square_map._repr_html_(), height=500)

    except Exception as e:
        st.error(f"Có lỗi xảy ra khi kết nối đến Elasticsearch: {str(e)}")
        st.info("Vui lòng kiểm tra kết nối và thử lại sau.")

if __name__ == "__main__":
    st.write("")