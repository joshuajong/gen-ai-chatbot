from openai import OpenAI
from dotenv import load_dotenv
import os
import pandas as pd
import csv
from chatbot.chatbot import *

# Load environment variables from .env file
load_dotenv()

# Get the OpenAI API key from environment variables
api_key = os.environ.get("OPENAI_API_KEY")
if not api_key:
  raise ValueError("OpenAI API key is not set. Please check your .env file.")

knowledge_source = './knowledgebase/sample_data.json'
general_context = "We are a customer support service for an online retail store. We handle inquiries related to our return policy, shipping information, product details, and other customer service issues."

chatbot = ChatBot(knowledge_source, api_key, general_context)

def main():
  print("Welcome to the Customer Support Chatbot!")
  print("Type 'exit' to end the conversation.")
  
  while True:
    user_input = input("You: ")
    if user_input.lower() == 'exit':
      print("Chatbot: Thank you for using our customer support. Have a great day!")
      break
    
    response = chatbot.generate_response(user_input)
    print(f"Chatbot: {response}")

if __name__ == "__main__":
  main()