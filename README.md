# Customer Support Chatbot
This is a simple customer support application using Flask and OpenAI's GPT. This guide will walk you through setting up and running the application.

## Prerequisites

- Python 3.x
- pip (Python package installer)

## Setup

### 1. Clone the Repository

Clone this repository to your local machine using:

```
git clone https://github.com/your-username/customer-support-app.git
cd customer-support-app
```

### 2. Create a Virtual Environment
Create a virtual environment to manage dependencies:

```
python -m venv venv
```
### 3. Activate the Virtual Environment
```
source venv/bin/activate
```

### 4. Install Dependencies
Install the necessary packages using pip:

```
pip install -r requirements.txt
```

### 5. Set Up Environment Variables
Create a .env file in the root directory of the project and add your OpenAI API key:

```
makefile
OPENAI_API_KEY=your_openai_api_key
```

### 6. Run the Flask Application
Run the following code and visit ```localhost:7000```:

```
python app.py
```
