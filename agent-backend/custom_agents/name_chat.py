from __future__ import annotations
import asyncio

from agents import Agent, Runner
INSTRUCTIONS = """
You are a conversation title generator. 
Given a full conversation between a user and an assistant, generate a clear, concise, and relevant title that summarizes the main topic or purpose of the conversation. 
The title should be short (3 to 8 words), descriptive, and specific enough to distinguish the conversation from others. Avoid generic titles like "Chat" or "Help Request." Focus on what the conversation is truly about. 
Return only the title—no explanation, no punctuation beyond what's necessary.
"""

name_agent = Agent(
    name="Name conversation agent",
    instructions=INSTRUCTIONS,
)

async def get_name(query):
    print(query)
    result = await  Runner.run(name_agent, query)
    return result.final_output
async def main():
    result = await Runner.run(name_agent, input="Cho tôi các bài đăng nhà phố mới nhất tại quận Hoàn Kiếm có 3 tầng")
    print(result.final_output)

if __name__ == "__main__":
    asyncio.run(main())