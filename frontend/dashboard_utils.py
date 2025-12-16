import requests
import pandas as pd
BASE_URL = "http://localhost:8000"
def price_by_date(estate_type_index: str, district: str):
    endpoint = f"{BASE_URL}/get_price_by_date/{estate_type_index}/{district}"
    response = requests.get(endpoint)
    response.raise_for_status()
    data = response.json()
    dates, avg_prices = data["dates"], data["avg_prices"]
    df = pd.DataFrame({
        "Ngày": dates,
        "Giá Trung Bình (VNĐ)": avg_prices
    })
    return df.sort_values("Ngày", ascending=True)


def price_per_square_by_date(estate_type_index: str, district: str):
    endpoint = f"{BASE_URL}/get_price_per_square_by_date/{estate_type_index}/{district}"
    response = requests.get(endpoint)
    response.raise_for_status()
    data = response.json()
    dates, avg_prices_per_square = data["dates"], data["avg_prices_per_square"]
    df = pd.DataFrame({
        "Ngày": dates,
        "Giá Trung Bình/m² (VNĐ)": avg_prices_per_square
    })
    return df.sort_values("Ngày", ascending=True)


def price_by_district(estate_type_index: str):
    endpoint = f"{BASE_URL}/get_price_by_district/{estate_type_index}"
    response = requests.get(endpoint)
    response.raise_for_status()
    data = response.json()
    districts, avg_prices = data["districts"], data["avg_prices"]
    df = pd.DataFrame({
        'Quận/Huyện': districts,
        'Giá Trung Bình (VNĐ)': avg_prices
    })
    return df.sort_values('Giá Trung Bình (VNĐ)', ascending=False)


def price_per_square_by_district(estate_type_index: str):
    endpoint = f"{BASE_URL}/get_price_per_square_by_district/{estate_type_index}"
    response = requests.get(endpoint)
    response.raise_for_status()
    data = response.json()
    districts, avg_prices_per_square = data["districts"], data["avg_prices_per_square"]
    df = pd.DataFrame({
        'Quận/Huyện': districts,
        'Giá Trung Bình/m² (VNĐ)': avg_prices_per_square
    })
    return df.sort_values('Giá Trung Bình/m² (VNĐ)', ascending=False)


def area_by_district(estate_type_index: str):
    endpoint = f"{BASE_URL}/get_area_by_district/{estate_type_index}"
    response = requests.get(endpoint)
    response.raise_for_status()
    data = response.json()
    districts, avg_areas = data["districts"], data["avg_areas"]
    df = pd.DataFrame({
        'Quận/Huyện': districts,
        'Diện tích trung bình (m²)': avg_areas
    })
    return df.sort_values('Diện tích trung bình (m²)', ascending=False)