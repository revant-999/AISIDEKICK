from playwright.async_api import async_playwright
from langchain_community.agent_toolkits import PlayWrightBrowserToolkit
from dotenv import load_dotenv
import os
import serial
import time
import subprocess
from langchain_core.tools import Tool, StructuredTool
from langchain_community.agent_toolkits import FileManagementToolkit
from langchain_community.tools.wikipedia.tool import WikipediaQueryRun
from langchain_experimental.tools import PythonREPLTool
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_community.utilities.wikipedia import WikipediaAPIWrapper
from presentation_tool import read_presentation

load_dotenv(override=True)
serper = GoogleSerperAPIWrapper()

async def playwright_tools():
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=False)
    toolkit = PlayWrightBrowserToolkit.from_browser(async_browser=browser)
    return toolkit.get_tools(), browser, playwright


def push(text: str):
    """Send a push notification to the user"""
    print(f"NOTIFICATION to user: {text}")
    return "success"


def get_file_tools():
    toolkit = FileManagementToolkit(root_dir="sandbox")
    return toolkit.get_tools()


def interact_with_arduino(command: str):
    """
    Control testing hardware - Arduino Uno R4 WiFi over USB Serial.
    Allowed commands: 
    - 'thinking', 'processing', 'greeting' (updates LED matrix)
    - 'pomodoro_<minutes>' (starts a timer for X minutes, e.g. 'pomodoro_25')
    - 'pomodoro_sec_<seconds>' (starts a timer for X seconds, e.g. 'pomodoro_sec_30' for testing)
    - 'fan_on', 'fan_off' (turns the motor/fan on or off)
    """
    port = os.getenv("ARDUINO_PORT", "/dev/ttyACM0")
    
    try:
        # Connect to Arduino over USB, send the command, and eagerly close the connection
        ser = serial.Serial(port, 115200, timeout=2)
        # Give the serial connection a tiny moment to stabilize
        time.sleep(0.5) 
        
        # Send text command over USB
        ser.write((command + "\n").encode('utf-8'))
        
        # Optionally, read back acknowledgment
        response = ser.readline().decode('utf-8').strip()
        ser.close()
        
        if "ACK" in response:
            return f"Successfully executed {command} on Arduino. (Response: {response})"
        return f"Command sent to Arduino, but no proper acknowledgment was received. (Got: {response})"
    except Exception as e:
        return f"Failed to communicate with Arduino over USB port {port}. Error: {str(e)}"

def schedule_notification(message: str, time_str: str) -> str:
    """
    Schedules a desktop notification to appear at a specific time.
    Args:
        message: The text of the notification to show the user.
        time_str: When to show it. Must be a format accepted by the linux 'at' command (e.g. '14:30', '10:00 AM', 'now + 5 minutes', 'tomorrow 2pm').
    """
    try:
        command = f"DISPLAY=:0 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$(id -u)/bus notify-send 'AI Sidekick' '{message}'"
        result = subprocess.run(
            ["at", time_str],
            input=command + "\n",
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            return f"Successfully scheduled notification for {time_str}.\nDetails: {result.stderr.strip()}"
        else:
            return f"Failed to schedule notification. Error: {result.stderr.strip()}"
    except Exception as e:
        return f"Error executing 'at' command: {str(e)}. (Is 'at' installed?)"

async def other_tools():
    push_tool = Tool(name="send_push_notification", func=push, description="Use this tool when you want to send a push notification")
    file_tools = get_file_tools()

    tool_search =Tool(
        name="search",
        func=serper.run,
        description="Use this tool when you want to get the results of an online web search"
    )

    wikipedia = WikipediaAPIWrapper()
    wiki_tool = WikipediaQueryRun(api_wrapper=wikipedia)

    python_repl = PythonREPLTool()
    
    arduino_tool = Tool(
        name="interact_with_arduino",
        func=interact_with_arduino,
        description="Use this to control the physical Arduino LED matrix status ('thinking', 'processing', 'greeting', 'pomodoro_X') or manage the study light with 'light_on'/'light_off'."
    )
    
    notification_tool = StructuredTool.from_function(
        name="schedule_notification",
        func=schedule_notification,
        description="Use this tool to schedule a desktop push notification for the future (e.g. reminders). Provide the message and the time_str in linux 'at' format (e.g., '14:30', 'now + 5 minutes')."
    )
    
    return file_tools + [push_tool, tool_search, python_repl, wiki_tool, arduino_tool, notification_tool, read_presentation]