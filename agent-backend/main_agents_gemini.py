import asyncio
from manager_gemini import ResearchManager
import json
import time
# import os
# import base64
# import uuid
# from opentelemetry.sdk.trace import TracerProvider
# from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
# from opentelemetry.sdk.trace.export import SimpleSpanProcessor
# from opentelemetry import trace
# import logfire
#
# # Cấu hình Langfuse và OTLP
# os.environ["LANGFUSE_PUBLIC_KEY"] = "pk-lf-6f38353e-2d42-4b43-9444-72ed6d214b0d"
# os.environ["LANGFUSE_SECRET_KEY"] = "sk-lf-b5333de4-d1d1-4a9c-b6b4-3af5b5a1873a"
# os.environ["LANGFUSE_HOST"] = "http://localhost:3000"
# LANGFUSE_AUTH = base64.b64encode(
#     f"{os.environ.get('LANGFUSE_PUBLIC_KEY')}:{os.environ.get('LANGFUSE_SECRET_KEY')}".encode()
# ).decode()
#
# os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = os.environ.get("LANGFUSE_HOST") + "/api/public/otel"
# os.environ["OTEL_EXPORTER_OTLP_HEADERS"] = f"Authorization=Basic {LANGFUSE_AUTH}"
#
# # Cấu hình OpenTelemetry
# trace_provider = TracerProvider()
# trace_provider.add_span_processor(SimpleSpanProcessor(OTLPSpanExporter()))
# trace.set_tracer_provider(trace_provider)
# tracer = trace.get_tracer(__name__)
#
# # Cấu hình Logfire
# logfire.configure(
#     service_name='my_agent_service',
#     send_to_logfire=False,
# )
# logfire.instrument_openai_agents()

async def main() -> None:
    # 1. Khởi tạo Manager MỘT LẦN duy nhất
    # use_judge=True để test khả năng tự sửa lỗi
    print("⏳ Initializing Research Manager...")
    manager = ResearchManager(use_judge=True)
    
    user_id = "user123"
    session_id = "test-session-01"

    # 2. Load câu hỏi test
    try:
        with open('./custom_agents/synthetic_data/data/agent_manager_test_cases_extended.json', 'r', encoding='utf-8') as file:
            data = json.load(file)
        
        # Lấy danh sách câu hỏi
        queries = [d["question"] for d in data]
        
        # Test thử 2 câu đầu thôi cho đỡ tốn quota
        queries = queries[:3] 
        # Hoặc dùng slice như bạn muốn: queries = queries[58:]
        
        # Mock query nếu không có file json
        if not queries:
            queries = [
            "Tìm nhà riêng tại Hoài Đức giá dưới 4 tỷ",
            "Chung cư 2 phòng ngủ quận Thanh Xuân"
        ]

    except FileNotFoundError:
        print("⚠️ Không tìm thấy file JSON test case. Dùng query mẫu.")
        queries = [
            "Tìm nhà riêng tại Hoài Đức giá dưới 4 tỷ",
            "Chung cư 2 phòng ngủ quận Thanh Xuân"
        ]

    print(f"🚀 Bắt đầu test {len(queries)} câu hỏi...")

    # 3. Chạy vòng lặp test
    for i, query in enumerate(queries, 1):
        print(f"\n\n================ TEST CASE {i} ================")
        print(f"❓ Query: {query}")
        
        try:
            # Gọi hàm run
            report, answer = await manager.run(query, user_id, session_id)
            
            print(f"✅ Đã xong Test Case {i}")
            print("💡 Answer Preview:", answer)
            
        except Exception as e:
            print(f"❌ Lỗi Test Case {i}: {e}")
        
        # Nghỉ 2s để tránh rate limit của Google Gemini
        time.sleep(2)

if __name__ == "__main__":
    asyncio.run(main())