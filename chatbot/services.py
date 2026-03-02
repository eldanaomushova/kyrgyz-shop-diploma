import os
import time
from django.conf import settings
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_community.document_loaders import CSVLoader
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_classic.chains import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_classic.chains import create_retrieval_chain
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

def get_chatbot_chain():
    current_file_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 2. Go up one level to the project root (Diploma-Project/)
    project_root = os.path.dirname(current_file_dir)
    # Use BASE_DIR to ensure it works inside the Django environment
    csv_path = os.path.join(settings.BASE_DIR, 'DIPLOMA-PROJECT/data', 'products.csv')
    
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Could not find products.csv at: {csv_path}")

    loader = CSVLoader(file_path=csv_path, encoding='utf-8')
    documents = loader.load()

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=600, chunk_overlap=50)
    texts = text_splitter.split_documents(documents)

    embeddings = HuggingFaceEmbeddings(model_name='sentence-transformers/all-MiniLM-L6-v2')
    
    # Path for vector database
    persist_dir = os.path.join(settings.BASE_DIR, "vector_db")
    
    vector_db = Chroma.from_documents(
        documents=texts, 
        embedding=embeddings, 
        persist_directory=persist_dir
    )

    llm = ChatGroq(
        temperature=0.2, 
        groq_api_key=os.getenv("GROQ_API_KEY"), 
        model_name="llama-3.3-70b-versatile"
    )

    system_prompt = (
        "Сиз Кыргызстандагы интернет-дүкөндүн сылык соода ассистентисиз. "
        "Контекстти колдонуп, кардардын суроосуна КЫСКА жана ТАК жооп бериңиз. "
        
        "Эрежелер: "
        "1. Жоопту колдонуучунун тилинде бериңиз. "
        "2. Эгерде товар табылса, ТӨМӨНКҮ форматта гана жооп бериңиз:\n"
        "   * **Аты:** [Продукттун аты]\n"
        "   * **Бренди:** [Бренд]\n"
        "   * **Баасы:** [Баасы] сом\n"
        "3. Ар бир товарды өзүнчө блок кылып бөлүп көрсөтүңүз. "
        "4. Эгерде продукт жок болсо, кыскача: 'Тилекке каршы, бул товар учурда жок. Бирок бизде башка варианттар бар:' деп башка товарларды сунуштаңыз. "
        "5. Ашыкча сөздөрдү (мисалы: 'Мен сизге жардам бере алам', 'Бул жерде маалымат') кошпоңуз. "
        "\n\n"
        "Контекст: {context}"
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", "{input}"), 
        ]
    )
    question_answer_chain = create_stuff_documents_chain(llm, prompt)

    return create_retrieval_chain(
        vector_db.as_retriever(search_kwargs={"k": 1}), 
        question_answer_chain
    )

qa_chain = get_chatbot_chain()

def get_shopping_response(message):
    try:
        response = qa_chain.invoke({"input": message})
        return response["answer"]
    except Exception as e:
        return f"System Error: {str(e)}"