from __future__ import annotations
import asyncio
from typing import Literal
from pydantic import BaseModel
from agents import Agent, Runner
import json


# Define the structured output model
class ToolSelection(BaseModel):
    tools: list[Literal["search_db", "search_web"]]


# Define the prompt for the PlannerAgent
PROMPT = """You are a helpful real estate assistant. Given a user query in Vietnamese, choose from 2 tools based on their descriptions:
            - search_db: Retrieves real estate listings from the database relevant to the query.
            - search_web: Gathers general real estate information, such as price forecasts or project updates, based on the query.
            Select the appropriate tool(s) and return them as a list. Always choose at least 1 tool. Return only the list of tool names in the structured output format.
            You cannot and must not use or call the WebSearch tool, only return the tool names as specified.

            Examples:
            Input: Cho tôi các bài đăng chung cư mới nhất tại quận Thanh Xuân?
            Output: ["search_db"]

            Input: Tình hình dự án Vinhomes Smart City như thế nào rồi?
            Output: ["search_web"]

            Input: Lấy cho tôi các bài đăng nhà riêng có 2 phòng ngủ tại quận Thanh Xuân. Dự đoán giá nhà riêng tại khu vực Thanh Xuân trong 6 tháng tới.
            Output: ["search_db", "search_web"]
"""

# Configure the PlannerAgent with structured output
planner_agent = Agent(
    name="PlannerAgent",
    instructions=PROMPT,
    model="gpt-4o-mini",
    output_type=ToolSelection,  # Enforce structured output using Pydantic model
)


# Main function to run the agent
async def main():
    result = await Runner.run(
        planner_agent,
        input="Cho tôi các bài đăng nhà phố mới nhất tại quận Hoàn Kiếm có 3 tầng. Cho tôi thông tin về diện tích trung bình của các căn hộ Eco Park"
    )
    # The final_output should be a ToolSelection instance; convert to JSON for printing
    tool_selection = result.final_output
    print(json.dumps(tool_selection.dict()))  # Print the structured output as JSON
    print(tool_selection.tools[0])  # Print first tool
    print(tool_selection.tools[1])  # Print second tool (if exists)


if __name__ == "__main__":
    asyncio.run(main())