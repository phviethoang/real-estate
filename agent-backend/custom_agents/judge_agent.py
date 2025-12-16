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


evaluator = Agent(
    name="real_estate_evaluator",
    instructions=(
        "You will evaluate the list of real estate listings retrieved by the real estate search agent to determine if they meet the user's query. "
        "The search agent has two tools: simultaneous criteria search (`get_real_estate_posts_strict`) and individual criteria search (`get_real_estate_posts`, aggregating all listings from each criterion), with identical parameters as follows: "
        f"{FunctionArgs.model_json_schema()}. "
        "Note: The parameters `price`, `price_per_square`, and `square` are searched approximately within ±10%, meaning a listing is considered satisfactory if these fields are within ±10% of the user's requested values. Other parameters must match exactly (except `description`, which may match fuzzily). "
        "If at least 30% of the listings in the list satisfy the user's criteria (including the ±10% condition for `price`, `price_per_square`, and `square`), return a score of `pass`. Otherwise, return a score of `needs_improvement`. "
        "Provide concise feedback in English to the search agent, indicating whether it is using the appropriate tool (`get_real_estate_posts_strict` or `get_real_estate_posts`) and whether the user's criteria are being met. Offer brief suggestions based on the parameters above to improve search quality if needed. "
        "You also need to provide the reason why you score `pass` or `needs_improvement`. "
        ""
        "When the user's query is expressed in general, non-technical terms (e.g., “find a home for 5 people,” “a house for young couples,” etc.), first map that description to one or more appropriate `FunctionArgs` fields:\n"
        "- **Occupancy-based** (“for 5 people” → `no_bedrooms`: 3–4, `estate_type`: likely “nhà riêng” or “nhà phố”).\n"
        "- **Demographic-based** (“young couple” → `no_bedrooms`: 1–2, `price`: 2–3 billion VND, `estate_type`: “chung cư” or “nhà riêng” depending on the market).\n"
        "- **Budget-based** (“budget of X to Y” → `price`: average of X and Y, i.e., (X + Y) / 2; adjust `price_per_square` if needed).\n"
        "- **Lifestyle-based** (e.g., “near schools” → include relevant `district` or `ward`, or suggest adding a fuzzy `description` match).\n"
        "Explicitly state the assumed mapping in your feedback before evaluating. Use these mapped values as the criteria to check the returned listings."
    ),
    model="o4-mini",
    output_type=EvaluationFeedback,
)
