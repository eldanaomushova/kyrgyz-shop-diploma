import os
import re
import pandas as pd
import markdown
from django.conf import settings
from dotenv import load_dotenv
from langchain_groq import ChatGroq
# from langchain_community.document_loaders import CSVLoader
# from langchain_community.vectorstores import Chroma
from langchain_classic.agents import create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_classic.tools import Tool
from langchain_classic.agents import AgentExecutor, create_openai_functions_agent
from langchain_core.prompts import MessagesPlaceholder

load_dotenv()

llm = ChatGroq(
    temperature=0,
    groq_api_key=os.getenv("GROQ_API_KEY"),
    model_name="llama-3.3-70b-versatile"
)

def search_csv_directly(query):
    csv_path = os.path.join(settings.BASE_DIR, 'DIPLOMA-PROJECT', 'data', 'products.csv')
    
    if not os.path.exists(csv_path):
        return f"Ката: Файл табылган жок."

    try:
        df = pd.read_csv(csv_path)
        query = str(query).lower()
        
        search_columns = ['productDisplayName', 'name', 'title', 'description']
        available_cols = [c for c in search_columns if c in df.columns]
        
        if not available_cols:
            return "Ката: CSV файлында издөө үчүн тиешелүү колонкалар жок."

        mask = df[available_cols].apply(
            lambda row: row.astype(str).str.lower().str.contains(query).any(), axis=1
        )
        
        results = df[mask]
        
        if results.empty:
            return "Кечириңиз, базада мындай товар табылган жок."
        
        context = ""
        for _, row in results.head(1).iterrows():
            p_id = row.get('id') or row.get('product_id') or "N/A"
            p_name = row.get('productDisplayName') or row.get('name') or "Товар"
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
        "Жоопту дайыма КЫРГЫЗ тилинде бериңиз. "
        "Эрежелер:\n"
        "1. Ашыкча сөздөрдү кошпоңуз (мисалы: 'издеп жатам', 'таптым').\n"
        "2. Дароо товардын маалыматын төмөнкү форматта бериңиз:\n"
        "📦 **[Аты]**\n"
        "💰 Баасы: [Баасы] сом\n"
        "🆔 ID: [ID]\n"
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
    match = re.search(r"ID:\s*(\d+)", text)
    product_id = match.group(1) if match else None

    html_content = markdown.markdown(text)

    if product_id:
        button_html = f"""
        <div style="margin-top: 10px; display: flex; gap: 8px;">
            <a href="http://localhost:3000/product/{product_id}" 
               target="_blank"
               style="text-decoration:none; background-color:#007bff; color:white; padding:8px 16px; border-radius:5px; font-weight:bold; font-size:13px;">
               👁 Көрүү
            </a>
        </div>
        """
        return f"{html_content}{button_html}"
    
    return html_content

def get_shopping_response(message):
    try:
        result = agent_executor.invoke({"input": message})
        return format_with_buttons(result.get("output", ""))
    except Exception as e:
        return f"❌ Ката: {str(e)}"