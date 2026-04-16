import os
import re
import pandas as pd
import markdown
from django.conf import settings
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_classic.agents import create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_classic.tools import Tool
from langchain_classic.agents import AgentExecutor
from langchain_core.prompts import MessagesPlaceholder

# Load .env file from multiple possible locations
load_dotenv()  # Current directory
load_dotenv(os.path.join(settings.BASE_DIR, '.env'))  # Project root
load_dotenv(os.path.join(settings.BASE_DIR, 'chatbot', '.env'))  # App directory

# Try multiple ways to get the API key
api_key = os.environ.get('GROQ_API_KEY')

# If not found, try reading from .env file directly
if not api_key:
    env_paths = [
        os.path.join(settings.BASE_DIR, '.env'),
        os.path.join(settings.BASE_DIR, 'chatbot', '.env'),
        '/app/.env',  # Docker path
    ]
    
    for env_path in env_paths:
        if os.path.exists(env_path):
            with open(env_path, 'r') as f:
                for line in f:
                    if line.startswith('GROQ_API_KEY='):
                        api_key = line.split('=', 1)[1].strip().strip('"').strip("'")
                        if api_key:
                            break
            if api_key:
                break

# Last resort - check if it's in Google Cloud Secret Manager or environment
if not api_key:
    # For Google Cloud Run/App Engine
    api_key = os.environ.get('GROQ_API_KEY')
    
if not api_key:
    raise ValueError("GROQ_API_KEY not set. Please ensure .env file exists with GROQ_API_KEY=your_key")

# Initialize LLM with explicit API key
llm = ChatGroq(
    temperature=0,
    groq_api_key=api_key,  # Explicitly pass the key
    model_name="llama-3.3-70b-versatile"
)

session_history = []

def search_csv_directly(query):
    csv_path = os.path.join(settings.BASE_DIR, 'products.csv')
    
    if not os.path.exists(csv_path):
        return f"Ката: Файл табылган жок."

    try:
        df = pd.read_csv(csv_path)
        search_terms = str(query).lower().split()
        
        search_columns = [
            'productDisplayName', 'brand', 'articleType', 
            'subCategory', 'masterCategory', 'color'
        ]
        available_cols = [c for c in search_columns if c in df.columns]

        if not available_cols:
            return "Ката: CSV файлында тиешелүү колонкалар табылган жок."

        combined_text = df[available_cols].fillna('').astype(str).agg(' '.join, axis=1).str.lower()

        mask = pd.Series([True] * len(df))
        for term in search_terms:
            mask &= combined_text.str.contains(term, na=False)
        
        results = df[mask]
        
        if results.empty:
            return "Кечириңиз, базада мындай товар табылган жок."
        
        context = ""
        for _, row in results.head(1).iterrows():
            p_id = row.get('id') or "N/A"
            p_name = row.get('productDisplayName') or "Товар"
            p_price = row.get('price') or "Келишимдүү"
            context += f"ID: {p_id} | Аты: {p_name} | Баасы: {p_price} сом\n"
        
        return context
    except Exception as e:
        print(f"--- DEBUG ERROR: {e} ---") 
        return f"CSV окууда ката: {e}"

tools = [
    Tool(
        name="product_search",
        func=search_csv_directly,
        description="Дүкөндөн товарларды издөө үчүн. Параметр: товардын аты."
    )
]

agent_prompt = ChatPromptTemplate.from_messages([
    ("system", (
        "Сиз Кыргызстандагы интернет-дүкөндүн соода ассистентисиз. "
        "Жоопту дайыма КЫРГЫЗ тилинде бериңиз.\n\n"
        
        "ЛОГИКА:\n"
        "1. Эгер колдонуучу учурашса (мисалы: 'салам', 'кандай') же жалпы суроо берсе, "
        "аспапты (tool) колдонбостон, дароо кыргызча жылуу жооп бериңиз.\n"
        "2. Эгер колдонуучу конкреттүү товарды сураса гана 'product_search' аспабын колдонуңуз.\n\n"
        
        "ТОВАР ТАБЫЛГАНДАГЫ ФОРМАТ:\n"
        "📦 **[Аты]**\n"
        "Баасы: [Баасы] сом\n"
        "ID: [ID]\n"
        "3. Эгер товар табылбаса, кыскача 'Кечириңиз, табылган жок' деп айтыңыз."
    )),
    MessagesPlaceholder(variable_name="chat_history", optional=True),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

agent = create_tool_calling_agent(llm, tools, agent_prompt)
agent_executor = AgentExecutor(
    agent=agent, 
    tools=tools, 
    verbose=True, 
    handle_parsing_errors=True
)

def format_with_buttons(text):
    match = re.search(r"ID[:\s]*(\d+)", text, re.IGNORECASE)
    id = match.group(1) if match else None

    html_content = markdown.markdown(text)

    if id:
        button_html = f"""
        <div style="margin-top: 10px; display: flex; gap: 8px;">
            <a href="http://localhost:3000/product/{id}" 
               target="_blank"
               style="text-decoration:none; background-color:#007bff; color:white; padding:8px 16px; border-radius:5px; font-weight:bold; font-size:13px;">
               Көрүү
            </a>
        </div>
        """
        return f"{html_content}{button_html}"
    
    return html_content

def get_shopping_response(message):
    global session_history
    try:
        result = agent_executor.invoke({
            "input": message,
            "chat_history": session_history 
        })
        output_text = result.get("output", "")

        session_history.append({"role": "user", "content": message})
        session_history.append({"role": "assistant", "content": output_text})

        if len(session_history) > 10:
            session_history = session_history[-10:]

        return format_with_buttons(output_text)
    except Exception as e:
        return f"❌ Ката: {str(e)}"