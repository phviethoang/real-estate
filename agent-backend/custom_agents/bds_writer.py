from __future__ import annotations
import asyncio
from typing import Optional, List, Any, Literal
from pydantic import BaseModel
from elasticsearch_queries import search_posts  # Giả định đây là module chứa hàm search_posts
from openai import AsyncOpenAI
from dotenv import load_dotenv
from agents import (
    Agent,
    Runner,
    function_tool,
    set_default_openai_api,
    set_default_openai_client,
    set_tracing_disabled,
    ToolsToFinalOutputFunction,
    ToolsToFinalOutputResult,
    FunctionToolResult,
    ModelSettings,
    RunContextWrapper,
    TResponseInputItem,
    ItemHelpers,
    FunctionTool,
    AsyncOpenAI,
    OpenAIChatCompletionsModel,
    ModelSettings
)
from agents.run import RunConfig
from agents.items import ToolCallOutputItem
import os
import json
load_dotenv()

# BASE_URL = os.getenv("EXAMPLE_BASE_URL") or ""
# API_KEY = os.getenv("EXAMPLE_API_KEY") or ""
# MODEL_NAME = os.getenv("EXAMPLE_MODEL_NAME") or ""
#
# if not BASE_URL or not API_KEY or not MODEL_NAME:
#     raise ValueError(
#         "Please set EXAMPLE_BASE_URL, EXAMPLE_API_KEY, EXAMPLE_MODEL_NAME via env var or code."
#     )
#
#
# """This example uses a custom provider for all requests by default. We do three things:
# 1. Create a custom client.
# 2. Set it as the default OpenAI client, and don't use it for tracing.
# 3. Set the default API as Chat Completions, as most LLM providers don't yet support Responses API.
#
# Note that in this example, we disable tracing under the assumption that you don't have an API key
# from platform.openai.com. If you do have one, you can either set the `OPENAI_API_KEY` env var
# or call set_tracing_export_api_key() to set a tracing specific key.
# """
#
# client = AsyncOpenAI(
#     base_url=BASE_URL,
#     api_key=API_KEY,
# )
# set_default_openai_client(client=client, use_for_tracing=False)
# set_default_openai_api("chat_completions")
# set_tracing_disabled(disabled=True)

class RealEstateAdvice(BaseModel):
    real_estate_findings: str
    """A markdown-formatted summary of listings and web-sourced information."""

    summary_real_estate_findings: str
    """A concise summary of real_estate_findings, excluding links, with a maximum of 2000 characters."""

    analytics_and_advice: str
    """Detailed analysis and investment recommendations provided by the advisor."""

    follow_up_questions: list[str]
    """Suggested follow-up research topics or questions."""


PROMPT = (
    "Bạn là một cố vấn đầu tư chuyên nghiệp chuyên về thị trường bất động sản. "
    "Bạn sẽ nhận được một câu hỏi đầu tư ban đầu cùng với dữ liệu sơ bộ, chẳng hạn như danh sách bất động sản "
    "hoặc thông tin từ web do một trợ lý tổng hợp.\n\n"
    "Nhiệm vụ của bạn là phân tích dữ liệu này, cung cấp một bản tóm tắt có cấu trúc về các phát hiện, và đưa ra "
    "lời khuyên đầu tư có thể thực hiện dựa trên câu hỏi được đưa ra. Sử dụng chuyên môn của bạn để đánh giá các cơ hội tiềm năng, "
    "so sánh các danh sách nếu có, đánh giá rủi ro, và làm nổi bật các yếu tố đầu tư quan trọng. "
    "Nếu có danh sách bất động sản, hãy trích dẫn liên kết của chúng và tóm tắt thông số kỹ thuật cùng các đặc điểm nổi bật của bất động sản ở định dạng markdown.\n\n"
    "Kết quả đầu ra phải được tổ chức tốt và bao gồm:\n"
    "1. Một phần markdown tóm tắt tất cả các phát hiện (danh sách và thông tin bên ngoài)\n"
    "2. Một phần tóm tắt ngắn gọn của real_estate_findings, không bao gồm liên kết, tối đa 2000 characters\n"
    "3. Một phần phân tích chi tiết và lời khuyên cá nhân hóa\n"
    "4. Một danh sách các câu hỏi tiếp theo để nghiên cứu thêm\n\n"
    "Chỉ trả lời bằng tiếng Việt.\n"
    "Chỉ xuất ra JSON. Không bao gồm bất kỳ văn bản giải thích nào ngoài JSON. Đầu ra phải tuân theo lược đồ JSON Pydantic này:\n"
    f"{RealEstateAdvice.model_json_schema()}"
)


writer_agent = Agent(
    name="WriterAgent",
    instructions=PROMPT,
    model="gpt-4o-mini",
    output_type=RealEstateAdvice
)
