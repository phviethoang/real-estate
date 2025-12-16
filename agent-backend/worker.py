from elasticsearch_queries import get_price_by_district, get_price_per_square_by_district, get_area_by_district, get_price_by_date, get_price_per_square_by_date
from manager import ResearchManager
from custom_agents.name_chat import get_name
import asyncio


def get_price_district(estate_type_index: str):
    return get_price_by_district(estate_type_index)

def get_price_per_square_district(estate_type_index: str):
    return get_price_per_square_by_district(estate_type_index)

def get_area_district(estate_type_index: str):
    return get_area_by_district(estate_type_index)

def get_price_date(estate_type_index: str, selected_district: str):
    return get_price_by_date(estate_type_index, selected_district)

def get_price_per_square_date(estate_type_index: str, selected_district: str):
    return get_price_per_square_by_date(estate_type_index, selected_district)


async def get_name_conversation(query):
    name = await get_name(query)
    return name