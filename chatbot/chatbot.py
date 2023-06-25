import openai
import json

import pywhatkit
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from colorama import init, Fore, Style

init()

class ChatBot:
    def __init__(self, keys_file, command_objs):
        with open(keys_file) as f:
            api_keys = json.load(f)

        openai.api_key = api_keys["openai"]

        self.messages = [{
                            "role": "system",
                            "content": """
                            You are MUSE (Machine Utilized Synthetic Entity).
                            You are Nicolas Gatien's personal assistant.
                            Your goal is to learn as many skills as you possibly can and to be as helpful as possible.
                            If there is a skill that would be useful for you to know, that you do not currently have access to, ask Nicolas to implement it.
                            You were created by Nicolas Gatien.
                            """
                        }]
        
        self.commands = {command_obj.name: command_obj for command_obj in command_objs}

    def get_response(self, prompt):
        # Add user's prompt to messages
        self.messages.append({"role": "user", "content": prompt})

        functions = [command_obj.metadata for command_obj in self.commands.values()]

        while True:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo-0613",
                messages=self.messages,
                functions=functions,
                function_call="auto",  # auto is default, but we'll be explicit
            )

            response_message = response["choices"][0]["message"]

            if response_message.get("function_call"):
                function_name = response_message["function_call"]["name"]
                function_to_call = self.commands.get(function_name)

                if function_to_call:
                    function_args = json.loads(response_message["function_call"]["arguments"])
                    function_response = function_to_call.execute(**function_args)
                    
                    self.messages.append(response_message)
                    self.messages.append(
                        {
                            "role": "function",
                            "name": function_name,
                            "content": function_response,
                        }
                    )
                    print(Fore.BLUE + f"Command Used: {function_name}\nArguments: {function_args}\nResponse: {function_response}" + Style.RESET_ALL)
                else:
                    raise ValueError(f"No function '{function_name}' available.")

            else:
                self.messages.append(response_message)
                return response_message["content"]
