import asyncio
from manager import ResearchManager
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
    # Tạo user_id và session_id
    user_id = "user123"  # Thay bằng ID người dùng thực tế
    session_id = "b4871930-e95c-4955-9246-4513eccf180a"
    with open('agent_manager_test_cases_extended.json', 'r', encoding='utf-8') as file:
        data = json.load(file)
    queries = [d["question"] for d in data]
    queries = queries[58:]

    # Bắt đầu một span và thêm user_id, session_id làm attribute
    # with tracer.start_as_current_span("research-session1") as span:
    #     span.set_attribute("user_id", user_id)  # Thêm user_id
    #     span.set_attribute("session_id", session_id)  # Thêm session_id
    for query in queries:
        report, answer = await ResearchManager().run(query, user_id, session_id)
        time.sleep(1)

        # span.set_attribute("input.value", query)
        # span.set_attribute("output.value", answer)

if __name__ == "__main__":
    asyncio.run(main())