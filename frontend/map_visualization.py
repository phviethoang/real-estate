# import folium
# from folium import plugins
# import pandas as pd
# import numpy as np
# import streamlit as st # Để dùng st.components

# # --- KHAI BÁO TỌA ĐỘ CỨNG (KHÔNG CẦN GỌI API NỮA) ---
# DISTRICT_COORDS = {
#     "Ba Đình": [21.0341, 105.8372],
#     "Hoàn Kiếm": [21.0285, 105.8542],
#     "Tây Hồ": [21.0596, 105.8299],
#     "Long Biên": [21.0381, 105.8856],
#     "Cầu Giấy": [21.0362, 105.7906],
#     "Đống Đa": [21.0152, 105.8267],
#     "Hai Bà Trưng": [21.0091, 105.8557],
#     "Hoàng Mai": [20.9754, 105.8617],
#     "Thanh Xuân": [20.9938, 105.8049],
#     "Sóc Sơn": [21.2618, 105.8459],
#     "Đông Anh": [21.1396, 105.8368],
#     "Gia Lâm": [21.0157, 105.9525],
#     "Nam Từ Liêm": [21.0128, 105.7609],
#     "Thanh Trì": [20.9443, 105.8476],
#     "Bắc Từ Liêm": [21.0632, 105.7663],
#     "Mê Linh": [21.1738, 105.7275],
#     "Hà Đông": [20.9636, 105.7630],
#     "Thị xã Sơn Tây": [21.1357, 105.5036],
#     "Ba Vì": [21.0963, 105.4190],
#     "Phúc Thọ": [21.0991, 105.5722],
#     "Đan Phượng": [21.0975, 105.6582],
#     "Hoài Đức": [21.0232, 105.7214],
#     "Quốc Oai": [20.9783, 105.6268],
#     "Thạch Thất": [21.0258, 105.5583],
#     "Chương Mỹ": [20.8876, 105.6297],
#     "Thanh Oai": [20.8753, 105.7725],
#     "Thường Tín": [20.8490, 105.8622],
#     "Phú Xuyên": [20.7356, 105.9189],
#     "Ứng Hòa": [20.7169, 105.7836],
#     "Mỹ Đức": [20.6756, 105.7533]
# }

# def get_district_coordinates(district):
#     """Lấy tọa độ từ Dictionary có sẵn, cực nhanh"""
#     # Xử lý cắt chuỗi nếu tên quận có dính chữ "Quận" (Ví dụ: "Quận Ba Đình" -> "Ba Đình")
#     clean_name = district.replace("Quận ", "").replace("Huyện ", "").strip()
#     return DISTRICT_COORDS.get(clean_name, DISTRICT_COORDS.get(district))

# def create_price_heatmap(price_by_district_df):
#     """Tạo bản đồ heatmap giá trung bình"""
#     # Tạo bản đồ nền Hà Nội
#     m = folium.Map(location=[21.0285, 105.8542], zoom_start=10, zoom_control=False)
    
#     # Lấy min/max để chuẩn hóa màu
#     if price_by_district_df.empty:
#          return m
         
#     max_price = price_by_district_df['Giá Trung Bình (VNĐ)'].max()
#     min_price = price_by_district_df['Giá Trung Bình (VNĐ)'].min()
    
#     heat_data = []
    
#     for _, row in price_by_district_df.iterrows():
#         coords = get_district_coordinates(row['Quận/Huyện'])
#         if coords:
#             # Chuẩn hóa giá trị về khoảng 0-1 cho heatmap
#             val = row['Giá Trung Bình (VNĐ)']
#             normalized = (val - min_price) / (max_price - min_price) if max_price > min_price else 0.5
            
#             # Thêm vào dữ liệu heatmap: [lat, lon, weight]
#             heat_data.append(coords + [normalized])
            
#             # Tạo popup hiển thị thông tin chi tiết
#             tooltip_text = f"{row['Quận/Huyện']}: {val:,.0f} VNĐ"
            
#             folium.Marker(
#                 coords,
#                 tooltip=tooltip_text, # Hover chuột vào sẽ hiện giá
#                 icon=folium.DivIcon(
#                     html=f'<div style="font-size: 10pt; font-weight: bold; color: black; text-shadow: 1px 1px 2px white;">{row["Quận/Huyện"]}</div>'
#                 )
#             ).add_to(m)
    
#     # Thêm lớp Heatmap
#     if heat_data:
#         plugins.HeatMap(heat_data, radius=25, blur=15).add_to(m)
    
#     return m

# def create_price_per_square_heatmap(price_per_square_df):
#     """Tạo bản đồ heatmap giá/m2"""
#     m = folium.Map(location=[21.0285, 105.8542], zoom_start=10, zoom_control=False)
    
#     if price_per_square_df.empty:
#         return m

#     max_price = price_per_square_df['Giá Trung Bình/m² (VNĐ)'].max()
#     min_price = price_per_square_df['Giá Trung Bình/m² (VNĐ)'].min()
    
#     heat_data = []
    
#     for _, row in price_per_square_df.iterrows():
#         coords = get_district_coordinates(row['Quận/Huyện'])
#         if coords:
#             val = row['Giá Trung Bình/m² (VNĐ)']
#             normalized = (val - min_price) / (max_price - min_price) if max_price > min_price else 0.5
            
#             heat_data.append(coords + [normalized])
            
#             tooltip_text = f"{row['Quận/Huyện']}: {val:,.0f} VNĐ/m²"
            
#             folium.Marker(
#                 coords,
#                 tooltip=tooltip_text,
#                 icon=folium.DivIcon(
#                     html=f'<div style="font-size: 10pt; font-weight: bold; color: black; text-shadow: 1px 1px 2px white;">{row["Quận/Huyện"]}</div>'
#                 )
#             ).add_to(m)
            
#     if heat_data:
#         plugins.HeatMap(heat_data, radius=25, blur=15).add_to(m)
    
#     return m

import folium
from folium import plugins
import pandas as pd
import json
import os

# 1. LOAD DATA TỌA ĐỘ TỪ FILE JSON
COORD_DB = {}
try:
    with open("district_coords_full.json", "r", encoding="utf-8") as f:
        COORD_DB = json.load(f)
except Exception:
    # Fallback nhẹ nếu chưa có file (chỉ demo Hà Nội)
    print("Cảnh báo: Chưa có file district_coords.json")

def get_district_coordinates(district_name, province_name):
    """
    Lấy tọa độ dựa trên Tên Quận VÀ Tên Tỉnh (để tránh trùng tên quận giữa các tỉnh)
    """
    if province_name in COORD_DB:
        return COORD_DB[province_name].get(district_name)
    return None

def create_price_heatmap(price_df, current_province):
    """
    Phiên bản đã tối ưu: Xử lý an toàn huyện thiếu tọa độ & Fix lỗi m_temp
    """
    # Mặc định là Hà Nội (Dùng khi không tìm thấy bất kỳ tọa độ nào)
    center_lat, center_lon = 21.0285, 105.8542 
    zoom_level = 10
    
    # Kiểm tra dữ liệu đầu vào rỗng
    if price_df.empty:
         return folium.Map(location=[center_lat, center_lon], zoom_start=zoom_level)

    # Các biến lưu trữ tạm
    lat_list = []
    lon_list = []
    heat_data = []
    marker_data = [] # Lưu thông tin để vẽ marker sau khi tạo map

    # Tính toán min/max để chuẩn hóa màu
    max_price = price_df['Giá Trung Bình (VNĐ)'].max()
    min_price = price_df['Giá Trung Bình (VNĐ)'].min()

    # --- VÒNG LẶP 1: THU THẬP DỮ LIỆU HỢP LỆ ---
    for _, row in price_df.iterrows():
        dist_name = row['Quận/Huyện']
        # Lấy tọa độ (Nếu không có sẽ trả về None)
        coords = get_district_coordinates(dist_name, current_province)
        
        # [QUAN TRỌNG] Chỉ xử lý khi CÓ tọa độ
        if coords:
            lat, lon = coords
            lat_list.append(lat)
            lon_list.append(lon)
            
            val = row['Giá Trung Bình (VNĐ)']
            
            # Chuẩn hóa giá (0-1)
            if max_price > min_price:
                normalized = (val - min_price) / (max_price - min_price)
            else:
                normalized = 0.5
            
            # Lưu dữ liệu Heatmap
            heat_data.append([lat, lon, normalized])
            
            # Lưu dữ liệu Marker để vẽ sau (vì chưa có object Map 'm')
            marker_data.append({
                "coords": coords,
                "name": dist_name,
                "value": val
            })

    # --- TÍNH TÂM BẢN ĐỒ DỰA TRÊN DỮ LIỆU THU ĐƯỢC ---
    if lat_list and lon_list:
        center_lat = sum(lat_list) / len(lat_list)
        center_lon = sum(lon_list) / len(lon_list)
    
    # Khởi tạo bản đồ
    m = folium.Map(location=[center_lat, center_lon], zoom_start=10, zoom_control=False)

    # --- VẼ HEATMAP & MARKER TỪ DỮ LIỆU ĐÃ LỌC ---
    if heat_data:
        plugins.HeatMap(heat_data, radius=25, blur=15).add_to(m)

    for item in marker_data:
        val = item["value"]
        dist_name = item["name"]
        
        # folium.Marker(
        #     item["coords"],
        #     tooltip=f"{dist_name}: {val:,.0f} VNĐ",
        #     icon=folium.DivIcon(
        #         html=f'<div style="font-size: 9pt; font-weight: bold; color: black; text-shadow: 1px 1px 2px white; white-space: nowrap;">{dist_name}</div>'
        #     )
        # ).add_to(m)
        folium.CircleMarker(
            location=item["coords"],
            radius=4,             # Bán kính nhỏ (4px) để không rối mắt
            color='black',        # Viền đen nhẹ
            weight=1,
            fill=True,
            fill_color='white',   # Nhân trắng cho dễ nhìn trên nền heatmap
            fill_opacity=0.7,
            tooltip=f"{dist_name}: {val:,.0f} VNĐ" # Tooltip gốc của bạn
        ).add_to(m)

    # Tự động zoom
    if lat_list:
        m.fit_bounds([[min(lat_list), min(lon_list)], [max(lat_list), max(lon_list)]])

    return m

def create_price_per_square_heatmap(price_per_square_df, current_province):
    """
    Tạo bản đồ heatmap giá/m2 (Phiên bản tối ưu & Dynamic Center)
    """
    # Mặc định là Hà Nội (Dùng khi không tìm thấy bất kỳ tọa độ nào)
    center_lat, center_lon = 21.0285, 105.8542 
    zoom_level = 10
    
    # Kiểm tra dữ liệu đầu vào rỗng
    if price_per_square_df.empty:
         return folium.Map(location=[center_lat, center_lon], zoom_start=zoom_level)

    # Các biến lưu trữ tạm
    lat_list = []
    lon_list = []
    heat_data = []
    marker_data = [] 

    # Tên cột dữ liệu (Lưu vào biến cho gọn)
    col_name = 'Giá Trung Bình/m² (VNĐ)'

    # Tính toán min/max để chuẩn hóa màu
    max_price = price_per_square_df[col_name].max()
    min_price = price_per_square_df[col_name].min()

    # --- VÒNG LẶP THU THẬP DỮ LIỆU ---
    for _, row in price_per_square_df.iterrows():
        dist_name = row['Quận/Huyện']
        # Lấy tọa độ theo Tỉnh hiện tại
        coords = get_district_coordinates(dist_name, current_province)
        
        # [QUAN TRỌNG] Chỉ xử lý khi CÓ tọa độ
        if coords:
            lat, lon = coords
            lat_list.append(lat)
            lon_list.append(lon)
            
            val = row[col_name]
            
            # Chuẩn hóa giá (0-1)
            if max_price > min_price:
                normalized = (val - min_price) / (max_price - min_price)
            else:
                normalized = 0.5
            
            # Lưu dữ liệu Heatmap
            heat_data.append([lat, lon, normalized])
            
            # Lưu dữ liệu Marker
            marker_data.append({
                "coords": coords,
                "name": dist_name,
                "value": val
            })

    # --- TÍNH TÂM BẢN ĐỒ ---
    if lat_list and lon_list:
        center_lat = sum(lat_list) / len(lat_list)
        center_lon = sum(lon_list) / len(lon_list)
    
    # Khởi tạo bản đồ
    m = folium.Map(location=[center_lat, center_lon], zoom_start=10, zoom_control=False)

    # --- VẼ HEATMAP & MARKER ---
    if heat_data:
        plugins.HeatMap(heat_data, radius=25, blur=15).add_to(m)

    for item in marker_data:
        val = item["value"]
        dist_name = item["name"]
        
        # folium.Marker(
        #     item["coords"],
        #     tooltip=f"{dist_name}: {val:,.0f} VNĐ/m²", # Đơn vị là VNĐ/m²
        #     icon=folium.DivIcon(
        #         html=f'<div style="font-size: 9pt; font-weight: bold; color: black; text-shadow: 1px 1px 2px white; white-space: nowrap;">{dist_name}</div>'
        #     )
        # ).add_to(m)
        folium.CircleMarker(
            location=item["coords"],
            radius=4,             # Bán kính nhỏ (4px) để không rối mắt
            color='black',        # Viền đen nhẹ
            weight=1,
            fill=True,
            fill_color='white',   # Nhân trắng cho dễ nhìn trên nền heatmap
            fill_opacity=0.7,
            tooltip=f"{dist_name}: {val:,.0f} VNĐ/m²" # Tooltip gốc của bạn
        ).add_to(m)
        
    # Tự động zoom
    if lat_list:
        m.fit_bounds([[min(lat_list), min(lon_list)], [max(lat_list), max(lon_list)]])

    return m