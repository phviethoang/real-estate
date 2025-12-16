from __future__ import annotations

import asyncio
import time

from rich.console import Console

from agents import Runner, gen_trace_id, trace
from custom_agents.planner import planner_agent
from custom_agents.search_db import Post, ListPosts, database_search_agent
from custom_agents.search_web import search_agent
from custom_agents.bds_writer import RealEstateAdvice, writer_agent
from custom_agents.judge_agent import evaluator
from printer import Printer
import json
from typing import Any

from zep_cloud.client import AsyncZep
from zep_cloud.types import Message
from dotenv import load_dotenv, find_dotenv
import os
load_dotenv(dotenv_path=find_dotenv())
API_KEY = os.environ.get("ZEP_API_KEY") or "YOUR_API_KEY"

import base64
import uuid
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry import trace
import logfire

# Cấu hình Langfuse và OTLP
os.environ["LANGFUSE_PUBLIC_KEY"] = "pk-lf-2fba610e-a5c8-4afd-8002-2d5e73995fdf"
os.environ["LANGFUSE_SECRET_KEY"] = "sk-lf-5958e907-7d6e-49ab-8e2b-ca9b5d30510f"
os.environ["LANGFUSE_HOST"] = "http://34.27.27.12:3000"
LANGFUSE_AUTH = base64.b64encode(
    f"{os.environ.get('LANGFUSE_PUBLIC_KEY')}:{os.environ.get('LANGFUSE_SECRET_KEY')}".encode()
).decode()

os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = os.environ.get("LANGFUSE_HOST") + "/api/public/otel"
os.environ["OTEL_EXPORTER_OTLP_HEADERS"] = f"Authorization=Basic {LANGFUSE_AUTH}"

# Cấu hình OpenTelemetry
trace_provider = TracerProvider()
trace_provider.add_span_processor(SimpleSpanProcessor(OTLPSpanExporter()))
trace.set_tracer_provider(trace_provider)
tracer = trace.get_tracer(__name__)

# Cấu hình Logfire
logfire.configure(
    service_name='my_agent_service',
    send_to_logfire=False,
)
logfire.instrument_openai_agents()

class ResearchManager:
    def __init__(self):
        self.console = Console()
        self.printer = Printer(self.console)
        self.client = AsyncZep(api_key=API_KEY)

    def reset_memory(self, messages):
        pass

    async def add_memory(self, messages, chat_id):
        append_memories = []
        for m in messages:
            append_memories.append({"role": m["role"], "role_type": m["role"], "content": m["content"]})
        for m in append_memories:
            await self.client.memory.add(session_id=chat_id, messages=[Message(**m)])

    async def run(self, query: Any, user_id: None, session_id: None) -> None:
        user_query = query if type(query) == str else query[-1]["content"]
        with tracer.start_as_current_span("Real estate research trace") as span:
            span.set_attribute("langfuse.user.id", user_id)  # Thêm user_id
            span.set_attribute("langfuse.session.id", session_id)  # Thêm session_id
            self.printer.update_item(
                "trace_id",
                f"View trace: http://localhost:3000",  # Cập nhật URL nếu cần
                is_done=True,
                hide_checkmark=True,
            )

            self.printer.update_item(
                "starting",
                "Starting research...",
                is_done=True,
                hide_checkmark=True,
            )
            posts = None
            findings = None
            tool_choices = await self._decide_tool(query)
            print(tool_choices)
            if "search_db" in tool_choices:
                posts = await self._perform_search_db(query)
            if "search_web" in tool_choices:
                findings = await self._perform_searches(query)

            report = await self._write_report(query, posts, findings)

            final_report = f"Findings\n\n{report.real_estate_findings}"
            # self.printer.update_item("final_report", final_report, is_done=True)

            self.printer.end()

            # print("\n\n=====REPORT=====\n\n")
            # print(f"Analytics: {report.analytics_and_advice}")
            # print("\n\n=====FOLLOW UP QUESTIONS=====\n\n")
            follow_up_questions = "\n".join(report.follow_up_questions)
            # print(f"Follow up questions: {follow_up_questions}")
            answer = report.real_estate_findings + "\n\n Phân tích:" + report.analytics_and_advice
            span.set_attribute("input.value", user_query)
            span.set_attribute("output.value", answer)

        return report, answer

    async def _decide_tool(self, query):
        user_query = query if type(query) == str else query[-1]["content"]
        with tracer.start_as_current_span("Decide tool") as span:
            # print(query)
            # print("==============================================================================")
            result = await Runner.run(planner_agent, query)
            print(result.final_output)
            span.set_attribute("input.value", user_query)
            span.set_attribute("output.value", str(result.final_output.tools))
            return result.final_output.tools

    async def _perform_search_db(self, query):
        with tracer.start_as_current_span("Search the database") as span:
            input_items = query if type(query) != str else [{"content": query, "role": "user"}]
            user_query = query if type(query) == str else query[-1]["content"]
            posts = []
            for i in range(1):
                result = await Runner.run(database_search_agent, input_items)
                posts = result.final_output_as(ListPosts)
            return posts

    async def _perform_searches(self, query: Any) -> list[str]:
        user_query = query if type(query) == str else query[-1]["content"]
        with tracer.start_as_current_span("Search the web") as span:
            self.printer.update_item("searching", "Searching...")
            num_completed = 0
            tasks = [asyncio.create_task(self._search(query))]
            results = []
            for task in asyncio.as_completed(tasks):
                result = await task
                if result is not None:
                    results.append(result)
                num_completed += 1
                self.printer.update_item(
                    "searching", f"Searching... {num_completed}/{len(tasks)} completed"
                )
            self.printer.mark_item_done("searching")
            span.set_attribute("input.value", user_query)
            span.set_attribute("output.value", str(results))
            return results

    async def _search(self, query: Any) -> str | None:
        input = query
        try:
            result = await Runner.run(
                search_agent,
                input,
            )
            return str(result.final_output)
        except Exception:
            return None

    async def _write_report(self, query: Any, posts: Any = None, findings: list[str] = None) -> RealEstateAdvice:
        self.printer.update_item("writing", "Thinking about report...")
        input_list = query if type(query) != str else [{"content": query, "role": "user"}]
        user_query = query if type(query) == str else query[-1]["content"]
        input = f"Original query: {user_query}"
        if posts != None:
            input += f"\nReal estate listings: {posts}"
        if findings != None:
            input += f"\nWeb-sourced data: {findings}"
        input_list.append({"content": input, "role": "user"})
        result = Runner.run_streamed(
            writer_agent,
            input_list,
        )
        update_messages = [
            "Thinking about report...",
            "Planning report structure...",
            "Writing outline...",
            "Creating sections...",
            "Cleaning up formatting...",
            "Finalizing report...",
            "Finishing report...",
        ]

        last_update = time.time()
        next_message = 0
        async for _ in result.stream_events():
            if time.time() - last_update > 5 and next_message < len(update_messages):
                self.printer.update_item("writing", update_messages[next_message])
                next_message += 1
                last_update = time.time()

        self.printer.mark_item_done("writing")
        return result.final_output_as(RealEstateAdvice)