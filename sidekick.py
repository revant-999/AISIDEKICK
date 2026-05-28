from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from dotenv import load_dotenv
from langgraph.prebuilt import ToolNode
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from typing import List, Any, Optional, Dict
from pydantic import BaseModel, Field
from sidekick_tools import playwright_tools, other_tools
import uuid
import os
import asyncio
from datetime import datetime

load_dotenv(override=True)


class State(TypedDict):
    messages: Annotated[List[Any], add_messages]
    success_criteria: str


class Sidekick:
    def __init__(self):
        self.worker_llm_with_tools = None
        self.tools = None
        self.graph = None
        self.sidekick_id = str(uuid.uuid4())
        self.memory = MemorySaver()
        self.browser = None
        self.playwright = None

    async def setup(self):
        self.tools, self.browser, self.playwright = await playwright_tools()
        self.tools += await other_tools()
        
        # Configure OpenRouter using the OpenAI library wrapper
        worker_llm = ChatOpenAI(
            model="anthropic/claude-sonnet-4-6", 
            temperature=0.7,
            api_key=os.environ.get("OPENROUTER_API_KEY"),
            base_url="https://openrouter.ai/api/v1"
        )
        
        self.worker_llm_with_tools = worker_llm.bind_tools(self.tools)
        await self.build_graph()

    def worker(self, state: State) -> Dict[str, Any]:
        sandbox_path = os.path.abspath("sandbox")
        system_message = f"""You are a helpful assistant that can use tools to complete tasks.
    You keep working on a task until either you have a question or clarification for the user, or the success criteria is met.
    You have many tools to help you, including tools to browse the internet, navigating and retrieving web pages.
    You have a tool to run python code, but note that you would need to include a print() statement if you wanted to receive output.
    
    SPECIAL CAPABILITY - NOTE SUMMARIZATION FOR LEARNING:
    If the user asks you to read or review their notes, use your file management tools to locate and read their notes in the sandbox/ directory.
    You MUST structure your summary specifically to optimize for human learning:
    - Distill the core concepts into simple, concise bullet points.
    - Avoid jargon where possible, or briefly explain it if necessary.
    - Group related points logically so the information is easy to digest.
    CRITICAL: After generating the summary, you MUST use your file management tools to create a new file in the sandbox/ directory (e.g., "study_notes.txt") containing this optimized summary. Return a message confirming the file was created.

    SPECIAL CAPABILITY - YOUTUBE VIDEO HELPER & LOCAL FILES:
    If the user asks you to find a video explaining a concept (like physics, math, etc.) or if they are struggling to understand a concept:
    1. DO NOT hallucinate or guess a YouTube URL, as they are often taken down or unavailable.
    2. Instead, use Playwright to directly open the YouTube search page for that concept. For example: navigate to `https://www.youtube.com/results?search_query=[concept_with_plus_signs]`
    3. Return a message telling the user that you have opened the search results for that video on their screen.
    
    If the user asks you to literally "open a file" (like a PPTX, PDF, etc.) visually in the browser/Playwright:
    1. Use the Playwright tool `navigate_browser` to open the file URL.
    2. The URL must be in absolute file URI format: `file://{sandbox_path}/[filename]` 
    3. Be aware that standard browsers usually download PPTX files instead of rendering them in-tab, but you should still execute the navigation command.
    
    SPECIAL CAPABILITY - ARDUINO HARDWARE INTEGRATION:
    You have physical presence via an Arduino Uno R4 WiFi.
    - If you are determining an answer for a complex question, use the tool to set the state to 'thinking' or 'processing'.
    - If you say hello or start a session, you can set the state to 'greeting'. 
    - If the user asks for studying help or a timer, set the state to 'pomodoro_<minutes>' (replace <minutes> with the number, e.g. 'pomodoro_25' for 25 minutes).
    - CRITICAL: If the user needs a study light, asks for illumination, or says it's dark, use the tool with 'light_on' to turn on the study LED. Use 'light_off' to turn it off.

    SPECIAL CAPABILITY - CALENDAR & REMINDERS:
    You have a tool to schedule future background notifications using `schedule_notification` (powered by Linux 'at' & 'notify-send').
    - When the user asks to schedule a reminder, set an alarm, or add something to their calendar/schedule, use this tool.
    - Provide a time in the format accepted by the 'at' command (e.g. '14:30', 'now + 5 minutes', 'tomorrow 2pm').

    The current date and time is {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

    This is the success criteria:
    {state["success_criteria"]}
    You should reply either with a question for the user about this assignment, or with your final response.
    If you have a question for the user, you need to reply by clearly stating your question. An example might be:

    Question: please clarify whether you want a summary or a detailed answer

    If you've finished, reply with the final answer, and don't ask a question; simply reply with the answer.
    """

        # Add in the system message

        found_system_message = False
        messages = state["messages"]
        for message in messages:
            if isinstance(message, SystemMessage):
                message.content = system_message
                found_system_message = True

        if not found_system_message:
            messages = [SystemMessage(content=system_message)] + messages

        # Invoke the LLM with tools
        response = self.worker_llm_with_tools.invoke(messages)

        # Return updated state
        return {
            "messages": [response],
        }

    def worker_router(self, state: State) -> str:
        last_message = state["messages"][-1]

        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        else:
            return "END"

    def format_conversation(self, messages: List[Any]) -> str:
        conversation = "Conversation history:\n\n"
        for message in messages:
            content = message.content
            if isinstance(content, list):
                content = "".join([item.get("text", "") for item in content if isinstance(item, dict)])
                
            if isinstance(message, HumanMessage):
                conversation += f"User: {content}\n"
            elif isinstance(message, AIMessage):
                text = content or "[Tools use]"
                conversation += f"Assistant: {text}\n"
        return conversation

    async def build_graph(self):
        # Set up Graph Builder with State
        graph_builder = StateGraph(State)

        # Add nodes
        graph_builder.add_node("worker", self.worker)
        graph_builder.add_node("tools", ToolNode(tools=self.tools))

        # Add edges
        graph_builder.add_conditional_edges(
            "worker", self.worker_router, {"tools": "tools", "END": END}
        )
        graph_builder.add_edge("tools", "worker")
        graph_builder.add_edge(START, "worker")

        # Compile the graph
        self.graph = graph_builder.compile(checkpointer=self.memory)

    async def run_superstep(self, message, success_criteria, history):
        config = {"configurable": {"thread_id": self.sidekick_id}}

        state = {
            "messages": message,
            "success_criteria": success_criteria or "The answer should be clear and accurate",
        }
        result = await self.graph.ainvoke(state, config=config)
        user = {"role": "user", "content": message}
        
        reply_content = result["messages"][-1].content
        if isinstance(reply_content, list):
            reply_content = "".join([item.get("text", "") for item in reply_content if isinstance(item, dict)])
            
        reply_content_str = str(reply_content).strip()
        if not reply_content_str:
            reply_content_str = "I have completed the task using the provided tools."
            
        reply = {"role": "assistant", "content": reply_content_str}
        return history + [user, reply]

    def cleanup(self):
        if self.browser:
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(self.browser.close())
                if self.playwright:
                    loop.create_task(self.playwright.stop())
            except RuntimeError:
                # If no loop is running, do a direct run
                asyncio.run(self.browser.close())
                if self.playwright:
                    asyncio.run(self.playwright.stop())