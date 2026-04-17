import os
import re
import pandas as pd
import markdown
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

_llm = None
_agent_executor = None
_session_history = []

def _init_agent():
    """Ленивая инициализация агента - только когда реально нужен"""
    global _llm, _agent_executor
    
    if _agent_executor is not None:
        return True
    
    try:
        # Импортируем только внутри функции
        from langchain_groq import ChatGroq
        from langchain_classic.agents import create_tool_calling_agent, AgentExecutor
        from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
        from langchain_classic.tools import Tool
        
        api_key = os.environ.get('GROQ_API_KEY')
        if not api_key:
            logger.error("GROQ_API_KEY not found in environment")
            return False
        
        _llm = ChatGroq(
            temperature=0,
            groq_api_key=api_key,
            model_name="llama-3.3-70b-versatile"
        )
        
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
                "1. Эгер колдонуучу учурашса же жалпы суроо берсе, "
                "аспапты колдонбостон, дароо кыргызча жылуу жооп бериңиз.\n"
                "2. Эгер колдонуучу конкреттүү товарды сураса гана 'product_search' аспабын колдонуңуз.\n\n"
                "ТОВАР ТАБЫЛГАНДАГЫ ФОРМАТ:\n"
                "📦 **[Аты]**\n"
                "Баасы: [Баасы] сом\n"
                "ID: [ID]"
            )),
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        agent = create_tool_calling_agent(_llm, tools, agent_prompt)
        _agent_executor = AgentExecutor(
            agent=agent, 
            tools=tools, 
            verbose=False,
            handle_parsing_errors=True
        )
        
        logger.info("✅ Agent initialized successfully")
        return True
        
    except ImportError as e:
        logger.error(f"Import error: {e}.")
        return False
    except Exception as e:
        logger.error(f"Failed to initialize agent: {e}")
        return False

def search_csv_directly(query):
    """Поиск товаров в CSV"""
    csv_path = os.path.join(settings.BASE_DIR, 'products.csv')
    
    if not os.path.exists(csv_path):
        logger.error(f"CSV not found: {csv_path}")
        return "Ката: Товарлар базасы табылган жок."
    
    try:
        df = pd.read_csv(csv_path)
        search_terms = str(query).lower().split()
        
        search_columns = [
            'productDisplayName', 'brand', 'articleType', 
            'subCategory', 'masterCategory', 'color'
        ]
        available_cols = [c for c in search_columns if c in df.columns]

        if not available_cols:
            return "Ката: CSV форматы туура эмес."

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
        logger.error(f"CSV search error: {e}")
        return f"CSV окууда ката: {e}"

def format_with_buttons(text):
    """Добавляет кнопки к ответу"""
    match = re.search(r"ID[:\s]*(\d+)", text, re.IGNORECASE)
    id = match.group(1) if match else None

    html_content = markdown.markdown(text)

    if id:
        frontend_url = os.environ.get('FRONTEND_URL', 'https://kyrgyz-shop-diploma.vercel.app')
        button_html = f"""
        <div style="margin-top: 10px; display: flex; gap: 8px;">
            <a href="{frontend_url}/product/{id}" 
               target="_blank"
               style="text-decoration:none; background-color:#007bff; color:white; padding:8px 16px; border-radius:5px; font-weight:bold; font-size:13px;">
               Көрүү
            </a>
        </div>
        """
        return f"{html_content}{button_html}"
    
    return html_content

def get_shopping_response(message):
    """Получение ответа от чат-бота"""
    global _session_history
    
    # Пробуем инициализировать агента
    if not _init_agent():
        # Fallback если агент не доступен
        logger.warning("Using fallback response - agent not available")
        
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['салам', 'сalam', 'привет', 'hello']):
            return "Саламатсызбы! Мен сизге кандай жардам бере алам?"
        elif any(word in message_lower for word in ['рахмат', 'спасибо']):
            return "Эч нерсе эмес! Дагы суроолоруңуз болсо, жазыңыз."
        elif any(word in message_lower for word in ['кийим', 'көйнөк', 'шым']):
            search_result = search_csv_directly(message)
            if "ID:" in search_result:
                return format_with_buttons(f"Мына, сиз издеген товарлар:\n{search_result}")
            return search_result
        else:
            return "Кечириңиз, азыр техникалык тейлөө иштери жүрүп жатат. Кийинчерээк кайрылыңыз."
    
    try:
        result = _agent_executor.invoke({
            "input": message,
            "chat_history": _session_history 
        })
        output_text = result.get("output", "")

        _session_history.append({"role": "user", "content": message})
        _session_history.append({"role": "assistant", "content": output_text})

        if len(_session_history) > 10:
            _session_history = _session_history[-10:]

        return format_with_buttons(output_text)
    except Exception as e:
        logger.error(f"Agent error: {e}")
        return f"❌ Кечириңиз, ката кетти. Кайра аракет кылыңыз." 