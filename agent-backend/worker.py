from elasticsearch_queries import get_price_by_district, get_price_per_square_by_district, get_area_by_district, get_price_by_date, get_price_per_square_by_date, update_all_global_districts
from manager_gemini import ResearchManager
from custom_agents.name_chat_gemini import get_name
import asyncio


def get_price_district(estate_type_index: str, listing_type: str):
    return get_price_by_district(estate_type_index, listing_type)

def get_price_per_square_district(estate_type_index: str, listing_type: str):
    return get_price_per_square_by_district(estate_type_index, listing_type)

def get_area_district(estate_type_index: str, listing_type: str):
    return get_area_by_district(estate_type_index, listing_type)

def get_price_date(estate_type_index: str, selected_district: str, start_date, end_date, listing_type: str):
    return get_price_by_date(estate_type_index, selected_district, start_date, end_date, listing_type)

def get_price_per_square_date(estate_type_index: str, selected_district: str, start_date, end_date, listing_type: str):
    return get_price_per_square_by_date(estate_type_index, selected_district, start_date, end_date, listing_type)

def update_global_districts(province: str):
    state = update_all_global_districts(province)
    return state

async def get_name_conversation(query):
    name = await get_name(query)
    return name