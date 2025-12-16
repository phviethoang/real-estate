from __future__ import annotations
import asyncio
from typing import Optional, List, Any, Literal
from pydantic import BaseModel, Field
from elasticsearch_queries import search_posts, search_posts_strict
from dotenv import load_dotenv
from agents import (
    Agent,
    Runner,
    RunContextWrapper,
    FunctionTool,
    ModelSettings
)
from agents.items import ToolCallOutputItem
from .agent_type import *
load_dotenv()


async def run_function(ctx: RunContextWrapper[Any], args: str) -> List[Post]:
    parsed = FunctionArgs.model_validate_json(args)
    print(parsed)

    search_results = search_posts(
        estate_type=parsed.estate_type,
        is_latest_posted=parsed.is_latest_posted,
        is_latest_created=parsed.is_latest_created,
        district=parsed.district,
        ward=parsed.ward,
        front_face=parsed.front_face,
        front_road=parsed.front_road,
        no_bathrooms=parsed.no_bathrooms,
        no_bedrooms=parsed.no_bedrooms,
        no_floors=parsed.no_floors,
        ultilization_square=parsed.ultilization_square,
        price=parsed.price,
        price_per_square=parsed.price_per_square,
        square=parsed.square,
        description=parsed.description
    )

    posts = []
    for result in search_results:
        try:
            post = Post(
                address=Address(
                    district=result["address"]["district"],
                    full_address=result["address"]["full_address"],
                    province=result["address"]["province"],
                    ward=result["address"]["ward"]
                ),
                contact_info=ContactInfo(
                    name=result["contact_info"]["name"],
                    phone=result["contact_info"]["phone"]
                ),
                description=result["description"],
                estate_type=result["estate_type"],
                extra_infos=ExtraInfos(
                    direction=result["extra_infos"].get("direction"),
                    front_face=result["extra_infos"].get("front_face"),
                    front_road=result["extra_infos"].get("front_road"),
                    no_bathrooms=result["extra_infos"].get("no_bathrooms"),
                    no_bedrooms=result["extra_infos"].get("no_bedrooms"),
                    no_floors=result["extra_infos"].get("no_floors"),
                    ultilization_square=result["extra_infos"].get("ultilization_square"),
                    yo_construction=result["extra_infos"].get("yo_construction")
                ),
                id=result["id"],
                link=result["link"],
                post_date=result["post_date"],
                created_at=result["created_at"],
                post_id=result["post_id"],
                price=result["price"],
                price_per_square=result["price/square"],
                square=result["square"],
                title=result["title"]
            )
            posts.append(post)
        except (KeyError, ValueError) as e:
            print(f"Error converting result to Post: {e}")
            continue

    print("no strict")
    return posts


async def run_function_strict(ctx: RunContextWrapper[Any], args: str) -> List[Post]:
    parsed = FunctionArgs.model_validate_json(args)
    print(parsed)

    search_results = search_posts_strict(
        estate_type=parsed.estate_type,
        is_latest_posted=parsed.is_latest_posted,
        is_latest_created=parsed.is_latest_created,
        district=parsed.district,
        ward=parsed.ward,
        front_face=parsed.front_face,
        front_road=parsed.front_road,
        no_bathrooms=parsed.no_bathrooms,
        no_bedrooms=parsed.no_bedrooms,
        no_floors=parsed.no_floors,
        ultilization_square=parsed.ultilization_square,
        price=parsed.price,
        price_per_square=parsed.price_per_square,
        square=parsed.square,
        description=parsed.description
    )

    posts = []
    for result in search_results:
        try:
            post = Post(
                address=Address(
                    district=result["address"]["district"],
                    full_address=result["address"]["full_address"],
                    province=result["address"]["province"],
                    ward=result["address"]["ward"]
                ),
                contact_info=ContactInfo(
                    name=result["contact_info"]["name"],
                    phone=result["contact_info"]["phone"]
                ),
                description=result["description"],
                estate_type=result["estate_type"],
                extra_infos=ExtraInfos(
                    direction=result["extra_infos"].get("direction"),
                    front_face=result["extra_infos"].get("front_face"),
                    front_road=result["extra_infos"].get("front_road"),
                    no_bathrooms=result["extra_infos"].get("no_bathrooms"),
                    no_bedrooms=result["extra_infos"].get("no_bedrooms"),
                    no_floors=result["extra_infos"].get("no_floors"),
                    ultilization_square=result["extra_infos"].get("ultilization_square"),
                    yo_construction=result["extra_infos"].get("yo_construction")
                ),
                id=result["id"],
                link=result["link"],
                post_date=result["post_date"],
                created_at=result["created_at"],
                post_id=result["post_id"],
                price=result["price"],
                price_per_square=result["price/square"],
                square=result["square"],
                title=result["title"]
            )
            posts.append(post)
        except (KeyError, ValueError) as e:
            print(f"Error converting result to Post: {e}")
            continue

    print("strict")
    if len(posts) == 0:
        print("No results from strict search, falling back to non-strict search")
        search_results = search_posts(
            estate_type=parsed.estate_type,
            is_latest_posted=parsed.is_latest_posted,
            is_latest_created=parsed.is_latest_created,
            district=parsed.district,
            ward=parsed.ward,
            front_face=parsed.front_face,
            front_road=parsed.front_road,
            no_bathrooms=parsed.no_bathrooms,
            no_bedrooms=parsed.no_bedrooms,
            no_floors=parsed.no_floors,
            ultilization_square=parsed.ultilization_square,
            price=parsed.price,
            price_per_square=parsed.price_per_square,
            square=parsed.square,
            description=parsed.description
        )

        for result in search_results:
            try:
                post = Post(
                    address=Address(
                        district=result["address"]["district"],
                        full_address=result["address"]["full_address"],
                        province=result["address"]["province"],
                        ward=result["address"]["ward"]
                    ),
                    contact_info=ContactInfo(
                        name=result["contact_info"]["name"],
                        phone=result["contact_info"]["phone"]
                    ),
                    description=result["description"],
                    estate_type=result["estate_type"],
                    extra_infos=ExtraInfos(
                        direction=result["extra_infos"].get("direction"),
                        front_face=result["extra_infos"].get("front_face"),
                        front_road=result["extra_infos"].get("front_road"),
                        no_bathrooms=result["extra_infos"].get("no_bathrooms"),
                        no_bedrooms=result["extra_infos"].get("no_bedrooms"),
                        no_floors=result["extra_infos"].get("no_floors"),
                        ultilization_square=result["extra_infos"].get("ultilization_square"),
                        yo_construction=result["extra_infos"].get("yo_construction")
                    ),
                    id=result["id"],
                    link=result["link"],
                    post_date=result["post_date"],
                    created_at=result["created_at"],
                    post_id=result["post_id"],
                    price=result["price"],
                    price_per_square=result["price/square"],
                    square=result["square"],
                    title=result["title"]
                )
                posts.append(post)
            except (KeyError, ValueError) as e:
                print(f"Error converting result to Post: {e}")
                continue
    return posts


function_schema = FunctionArgs.model_json_schema()
function_schema["additionalProperties"] = False
function_schema_strict = FunctionArgs.model_json_schema()
function_schema_strict["additionalProperties"] = False
tool = FunctionTool(
    name="get_real_estate_posts",
    description=(
        "Search real estate posts that match **at least one** of the provided criteria. "
        "This tool is suitable when the user is asking about general suggestions or when get_real_estate_posts_strict tool did not return any results. If the user's query have the words: 'hoặc', 'hoặc là', 'hay', 'hay là' or other synonyms, this tool must be used"
    ),
    params_json_schema=function_schema,
    on_invoke_tool=run_function,
)
tool_strict = FunctionTool(
    name="get_real_estate_posts_strict",
    description=(
        "Search real estate posts that strictly match **all** of the provided criteria. "
        "Use this tool when the user's question requires that multiple conditions be satisfied at the same time, If the user's query do not have the words: 'hoặc', 'hoặc là', 'hay', 'hay là' or other synonyms, this tool must be used "
        "Examples that this tool should be used:"
        "Example 1: cho tôi các căn hộ 80 mét vuông tại quận Thanh Xuân"
        "Example 2: cho tôi các căn hộ tại quận Thanh Xuân rộng toàn bộ 80 mét vuông"
        "Example 3: cho tôi các căn hộ tầm 70 triệu một mét vuông và có 3 phòng ngủ tại quận Đống Đa"
    ),
    params_json_schema=function_schema,
    on_invoke_tool=run_function_strict,
)

database_search_agent = Agent(
    name="The agent searching real estate posts from database",
    model="gpt-4o-mini",
    instructions="""
    You are a real estate searching agent. You will be given an input in Vietnamese and you must respond in Vietnamese. Return exactly posts from any tool used without independently filtering or editing the information. If there is any feedback provided, use it to improve the search.

    In addition, you must be aware of and normalize any fields related to price such as "price", "price_per_square", etc. Normalize any price expression written in shorthand Vietnamese such as:
    - "triệu", "tr", "m" → 1,000,000 VND
    - "tỉ", "tỷ", "b", "T" → 1,000,000,000 VND
    
    For example, "10 triệu", "10tr", "10m", or "10T" must all be interpreted as 70,000,000 VND; "2 tỷ", "2tỉ", or "2b" must be 2,000,000,000 VND. Convert these into numeric values before processing.
    """,
    tools=[tool, tool_strict],
    output_type= ListPosts,
    model_settings=ModelSettings(tool_choice="required"),
    tool_use_behavior="stop_on_first_tool"
)

async def main():
    result = await Runner.run(database_search_agent, input="Cho tôi các căn hộ 3 phòng ngủ và 2 nhà tắm tại quận Thanh Xuân và Đống Đa")
    print(result.final_output)
    print(result.new_items[0].raw_item)
    tool_call_output_item = next(item for item in result.new_items if isinstance(item, ToolCallOutputItem))
    print(type(tool_call_output_item.output))
    print(type(tool_call_output_item.output[0]))


if __name__ == "__main__":
    asyncio.run(main())