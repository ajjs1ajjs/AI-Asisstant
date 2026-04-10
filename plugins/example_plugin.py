# 🧩 AI Coding IDE Example Plugin
# This plugin demonstrates how to add custom tools for the AI agent.

import os
import datetime

def get_system_info():
    """Returns basic system information"""
    import platform
    return f"💻 OS: {platform.system()} {platform.release()}\n🐍 Python: {platform.python_version()}"

def get_current_time():
    """Returns the current local time"""
    return f"🕒 Current Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

def register_tools():
    """
    Required function for all plugins.
    Should return a dictionary of {tool_name: function_object}
    """
    return {
        "get_system_info": get_system_info,
        "get_current_time": get_current_time
    }
