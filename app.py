from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
import os
from chatbot.chatbot import ChatBot

# Load environment variables from .env file
load_dotenv()

# Get the OpenAI API key from environment variables
api_key = os.environ.get("OPENAI_API_KEY")
if not api_key:
  raise ValueError("OpenAI API key is not set. Please check your .env file.")

knowledge_source = './knowledgebase/sample_data.json'
general_context = "We are a customer support service for an online retail store. We handle inquiries related to our return policy, shipping information, product details, and other customer service issues."

chatbot = ChatBot(knowledge_source, api_key, general_context)

app = Flask(__name__, static_folder='static', template_folder='templates')


@app.route('/')
def home():
  return render_template('index.html')

@app.route('/support', methods=['POST'])
def support():
  user_message = request.json.get('message')
  response = chatbot.generate_response(user_message)
  return jsonify({'response': response})

if __name__ == '__main__':
  app.run(debug=True, port=5001)
