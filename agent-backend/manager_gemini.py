from __future__ import annotations

import asyncio
import time

from rich.console import Console

from agents import Runner, gen_trace_id, trace

from custom_agents.agent_type import *
from custom_agents.planner_gemini import planner_agent
from custom_agents.search_db_gemini import GeminiSearchAgent
from custom_agents.search_web_gemini import search_agent
from custom_agents.bds_writer_gemini import RealEstateAdvice, GeminiWriterAgent
from custom_agents.judge_agent_gemini import evaluator
from printer import Printer
import json
from typing import Any

from dotenv import load_dotenv, find_dotenv
import os
load_dotenv(dotenv_path=find_dotenv())


# from zep_cloud.client import AsyncZep
# from zep_cloud.types import Message
# API_KEY = os.environ.get("ZEP_API_KEY") or "YOUR_API_KEY"

# import base64
# import uuid
# from opentelemetry.sdk.trace import TracerProvider
# from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
# from opentelemetry.sdk.trace.export import SimpleSpanProcessor
# from opentelemetry import trace
# import logfire

# # Cấu hình Langfuse và OTLP
# os.environ["LANGFUSE_PUBLIC_KEY"] = "pk-lf-2fba610e-a5c8-4afd-8002-2d5e73995fdf"
# os.environ["LANGFUSE_SECRET_KEY"] = "sk-lf-5958e907-7d6e-49ab-8e2b-ca9b5d30510f"
# os.environ["LANGFUSE_HOST"] = "http://34.27.27.12:3000"
# LANGFUSE_AUTH = base64.b64encode(
#     f"{os.environ.get('LANGFUSE_PUBLIC_KEY')}:{os.environ.get('LANGFUSE_SECRET_KEY')}".encode()
# ).decode()

# os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = os.environ.get("LANGFUSE_HOST") + "/api/public/otel"
# os.environ["OTEL_EXPORTER_OTLP_HEADERS"] = f"Authorization=Basic {LANGFUSE_AUTH}"

# # Cấu hình OpenTelemetry
# trace_provider = TracerProvider()
# trace_provider.add_span_processor(SimpleSpanProcessor(OTLPSpanExporter()))
# trace.set_tracer_provider(trace_provider)
# tracer = trace.get_tracer(__name__)

# # Cấu hình Logfire
# logfire.configure(
#     service_name='my_agent_service',
#     send_to_logfire=False,
# )
# logfire.instrument_openai_agents()



class ResearchManager:
    def __init__(self, use_judge: bool = True):
        self.console = Console()
        self.printer = Printer(self.console)
        # self.client = AsyncZep(api_key=API_KEY)

        self.use_judge = use_judge #THÊM MỚI
        self.db_agent = GeminiSearchAgent()
        self.writer_agent = GeminiWriterAgent()

    def reset_memory(self, messages):
        pass

    async def add_memory(self, messages, chat_id):
        # append_memories = []
        # for m in messages:
        #     append_memories.append({"role": m["role"], "role_type": m["role"], "content": m["content"]})
        # for m in append_memories:
        #     await self.client.memory.add(session_id=chat_id, messages=[Message(**m)])
        pass #tạm thời bỏ qua

    # async def run(self, query: Any, user_id: None, session_id: None) -> None:
    #     user_query = query if type(query) == str else query[-1]["content"]
    #     with tracer.start_as_current_span("Real estate research trace") as span:
    #         span.set_attribute("langfuse.user.id", user_id)  # Thêm user_id
    #         span.set_attribute("langfuse.session.id", session_id)  # Thêm session_id
    #         self.printer.update_item(
    #             "trace_id",
    #             f"View trace: http://localhost:3000",  # Cập nhật URL nếu cần
    #             is_done=True,
    #             hide_checkmark=True,
    #         )

    #         self.printer.update_item(
    #             "starting",
    #             "Starting research...",
    #             is_done=True,
    #             hide_checkmark=True,
    #         )

    #         posts = None
    #         findings = None

    #         # 1. QUYẾT ĐỊNH TOOL (Planner)
    #         tool_choices = await self._decide_tool(query)
    #         print(tool_choices)

    #         # 2. THỰC THI TOOL
    #         if "search_db" in tool_choices:
    #             posts = await self._perform_search_db(query)
    #         if "search_web" in tool_choices:
    #             findings = await self._perform_searches(query)
            
    #         # 3. VIẾT BÁO CÁO (Writer)
    #         report = await self._write_report(query, posts, findings)

    #         self.printer.end()
    #         answer = report.real_estate_findings + "\n\n Phân tích:" + report.analytics_and_advice
    #         span.set_attribute("input.value", user_query)
    #         span.set_attribute("output.value", answer)

    #     return report, answer

    async def run(self, query: Any, user_id: None, session_id: None) -> None:
        user_query = query if type(query) == str else query[-1]["content"]
        print(f"Bắt đầu xử lý: {user_query}")

        self.printer.update_item(
            "starting",
            "Starting research...",
            is_done=True,
            hide_checkmark=True,
        )

        posts = None
        findings = None

        # 1. QUYẾT ĐỊNH TOOL (Planner)
        tool_choices = await self._decide_tool(query)
        print(tool_choices)

        print("Tôi đang tìm kiếm!")
        # 2. THỰC THI TOOL
        if "search_db" in tool_choices:
            posts = await self._perform_search_db(query)
        if "search_web" in tool_choices:
            findings = await self._perform_searches(query)
        
        # 3. VIẾT BÁO CÁO (Writer)
        print("Tôi đang viết báo cáo!")
        report = await self._write_report(query, posts, findings)

        self.printer.end()
        answer = report.real_estate_findings + "\n\n Phân tích:" + report.analytics_and_advice

        return report, answer

    async def _decide_tool(self, query):
        user_query = query if type(query) == str else query[-1]["content"]
        result = await planner_agent.run(user_query)
  
        # Trả về list tools (ví dụ: ['search_db'])
        # span.set_attribute("input.value", user_query)
        # span.set_attribute("output.value", str(result.tools))
   
        return result.tools
    


    async def _perform_search_db(self, query):
        """
        Hàm Search DB thông minh với 2 chế độ:
        1. Fast Mode (No Judge)
        2. Reasoning Mode (With Judge Loop)
        """
        user_query = query if type(query) == str else query[-1]["content"]
        
        # with tracer.start_as_current_span("Search the database") as span:
            
        # --- TRƯỜNG HỢP 1: KHÔNG DÙNG JUDGE ---
        if not self.use_judge:
            self.printer.update_item("searching", "Searching DB (Fast Mode)...")
            try:
                # Gọi trực tiếp Gemini Search Agent
                posts = self.db_agent.run(user_query)
                self.printer.mark_item_done("searching")
                return posts
            except Exception as e:
                print(f"❌ Search Error: {e}")
                self.printer.mark_item_done("searching") # Nhớ mark done để tắt spinner
                return []

        # --- TRƯỜNG HỢP 2: CÓ DÙNG JUDGE (SELF-CORRECTION) ---
        self.printer.update_item("searching", "Searching DB (Smart Mode)...")
        
        current_query = user_query
        final_posts = []
        max_retries = 2
        
        for attempt in range(max_retries):
            # Bước 1: Search
            try:
                # Nếu là lần 2 trở đi, current_query đã kèm Feedback
                posts = self.db_agent.run(current_query)
            except Exception as e:
                print(f"Search Error: {e}")
                posts = []

            # Bước 2: Judge
            self.printer.update_item("evaluating", f"Judging results (Attempt {attempt+1})...")
            
            # Gọi Evaluator
            try:
                evaluation = evaluator.run(user_query, posts)
                print(f"\n👨‍⚖️ JUDGE: {evaluation.score} | Reason: {evaluation.reason}")
            except Exception as e:
                print(f"❌ Judge Error: {e}. Accepting results automatically.")
                # Nếu Judge lỗi thì coi như Pass để không kẹt
                self.printer.mark_item_done("evaluating")
                self.printer.mark_item_done("searching")
                return posts

            if evaluation.score == "pass":
                self.printer.mark_item_done("evaluating")
                self.printer.mark_item_done("searching")
                return posts # Thành công -> Return ngay
            
            else: # needs_improvement
                if attempt < max_retries - 1:
                    # Feedback loop: Sửa query để thử lại
                    self.printer.update_item("searching", f"Retrying with feedback...")
                    # Thêm feedback vào query để Gemini Search hiểu
                    current_query = f"Yêu cầu gốc: {user_query}. \nLƯU Ý ĐIỀU CHỈNH (FEEDBACK): {evaluation.feedback}"
                else:
                    print("🛑 Hết lượt thử lại. Dùng kết quả hiện tại.")
                    final_posts = posts

        self.printer.mark_item_done("evaluating")
        self.printer.mark_item_done("searching")
        return final_posts
        

    async def _perform_searches(self, query: Any) -> list[str]:
        user_query = query if type(query) == str else query[-1]["content"]
        # with tracer.start_as_current_span("Search the web") as span:
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
        # span.set_attribute("input.value", user_query)
        # span.set_attribute("output.value", str(results))
        return results

    async def _search(self, query: Any) -> str | None:
        input = query
        try:
            result = await search_agent.run(input)
            return str(result)
        except Exception:
            return None

    async def _write_report(self, query: Any, posts: Any = None, findings: list[str] = None) -> RealEstateAdvice:
        """
        Tổng hợp dữ liệu và viết báo cáo bằng GeminiWriterAgent.
        """
        # 1. Cập nhật UI
        self.printer.update_item("writing", "Gemini is analyzing & writing report...")
        
        # 2. Chuẩn bị Query
        user_query = query if type(query) == str else query[-1]["content"]
        
        # 3. Chuẩn bị Context Data
        context_parts = []

        if posts:
            posts_clean_str = ""
            if isinstance(posts, list):
                # Nếu là list object, ta format đẹp để tiết kiệm token và giúp AI dễ đọc
                for idx, p in enumerate(posts, 1):
                    # Kiểm tra xem p là dict hay object để lấy dữ liệu
                    p_data = p if isinstance(p, dict) else p.__dict__
                    
                    # Tạo chuỗi tóm tắt cho từng căn nhà
                    posts_clean_str += f"\n#{idx}. {p_data.get('title', 'N/A')}\n"
                    posts_clean_str += f"   - Giá: {p_data.get('price', 0):,} VNĐ\n"
                    posts_clean_str += f"   - Đ/C: {p_data.get('address', {})}\n"
                    posts_clean_str += f"   - Link: {p_data.get('link', '')}\n"
            else:
                # Nếu posts đã là string hoặc dạng khác
                posts_clean_str = str(posts)
                
            context_parts.append(f"=== DỮ LIỆU TỪ DATABASE ===\n{posts_clean_str}")
        else:
            context_parts.append("=== DỮ LIỆU TỪ DATABASE ===\n(Không tìm thấy dữ liệu trong DB)")

        # --- Xử lý Findings từ Web ---
        if findings:
            # findings thường là list[str], ta join lại
            findings_str = "\n".join(findings) if isinstance(findings, list) else str(findings)
            context_parts.append(f"=== DỮ LIỆU TỪ INTERNET ===\n{findings_str}")
        
        # Ghép lại thành 1 khối văn bản hoàn chỉnh
        full_data_context = "\n\n".join(context_parts)

        # 4. Gọi Writer Agent
        try:
            # Gọi hàm run của class GeminiWriterAgent (Đã chốt)
            result = await self.writer_agent.run(user_query, full_data_context)
            
            if result:
                self.printer.mark_item_done("writing")
                return result
            else:
                raise ValueError("Gemini trả về kết quả rỗng (None).")

        except Exception as e:
            print(f"❌ Writer Error: {e}")
            self.printer.mark_item_done("writing")
            
            # Fallback an toàn
            return RealEstateAdvice(
                real_estate_findings="Đã xảy ra lỗi trong quá trình tạo báo cáo.",
                summary_real_estate_findings="Hệ thống gặp sự cố kết nối với mô hình ngôn ngữ.",
                analytics_and_advice="Vui lòng thử lại sau giây lát.",
                follow_up_questions=[]
            )