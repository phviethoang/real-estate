from __future__ import annotations
import asyncio

from agents import Agent, WebSearchTool, Runner
from agents.model_settings import ModelSettings


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

INSTRUCTIONS = (
    "You are a real estate research assistant. Given a search term about real estate, you search the web"
    "for that term and produce a concise summary of results. Focus on real estate info like real estate posts, market trends,"
    "price forecasts, project updates, amenities around the property. Summary must be 2-3 paragraphs, under 300 words. Capture main points."
    "Write succinctly, no complete sentences or good grammar needed. For someone synthesizing a real estate"
    "report, so focus on essence, ignore fluff. No extra commentary beyond summary. Just write about the query that you have the information about and ignore the query that you dont't have the information about. You must response in Vietnamese."
)

search_agent = Agent(
    name="Search agent",
    instructions=INSTRUCTIONS,
    tools=[WebSearchTool()],
    model_settings=ModelSettings(tool_choice="required"),
)

async def main():
    # user_id = "user123"  # Thay bằng ID người dùng thực tế
    # session_id = "b4871930-e95c-4955-9246-4513eccf180a"
    # with tracer.start_as_current_span("research-session1") as span:
    #     span.set_attribute("user_id", user_id)  # Thêm user_id
    #     span.set_attribute("session_id", session_id)  # Thêm session_id
        result = await Runner.run(search_agent, input="Cho tôi các bài đăng nhà phố mới nhất tại quận Hoàn Kiếm có 3 tầng")
        print(result.final_output)
        # span.set_attribute("input.value", "Cho tôi các bài đăng nhà phố mới nhất tại quận Hoàn Kiếm có 3 tầng")
        # span.set_attribute("output.value", result.final_output)

if __name__ == "__main__":
    asyncio.run(main())