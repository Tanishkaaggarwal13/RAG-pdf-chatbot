from dotenv import load_dotenv

load_dotenv()  
import os
import streamlit as st

api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    api_key = st.secrets.get("GOOGLE_API_KEY")
st.write("API Key Loaded:", api_key is not None)

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI 
from langchain_community.vectorstores import InMemoryVectorStore
import streamlit as st
from time import sleep
import os

st.write("App started successfully")


llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash" , temperature=0.2, google_api_key=api_key)
if("vector_db" not in st.session_state):
    st.session_state.vector_db = None

print("Using model: gemini-3.5-flash")
st.write("Using model: gemini-3.5-flash")


def document_process(path):
    #document loading
    loader = PyPDFLoader(path)
    documents = loader.load()



    #splitting
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=20)
    splitted_docs = splitter.split_documents(documents)



#embedding and vectorstore
    embeddings = GoogleGenerativeAIEmbeddings( model="models/gemini-embedding-001", google_api_key=api_key)
    vector_db = InMemoryVectorStore.from_documents(
    documents=splitted_docs,
    embedding=embeddings
)
    
    st.session_state.vector_db = vector_db
    st.session_state.document_uploaded = True


st.subheader("Document Q&A Chatbot - Ask About Your PDF")

if "document_uploaded" not in st.session_state:
    st.session_state.document_uploaded = False

#document  upload 
if not st.session_state.document_uploaded:
    file = st.file_uploader("Upload a PDF document", type=["pdf"], key="document_uploader")
    if file :
        with open("uploaded_document.pdf", "wb") as f:
            f.write(file.getvalue())

        with  st.spinner("Processing.."):
            document_process("./uploaded_document.pdf")

        st.markdown("Document processed successfully! You can now ask questions about the content.")
        sleep(2)
        st.rerun()


if st.session_state.document_uploaded and st.session_state.vector_db :
    query = st.chat_input("Ask a question about the document:")

    if query:


        st.chat_message("user").markdown(query)

        docs = st.session_state.vector_db.similarity_search(query, k=2)
        context = ""


        for doc in docs:
            context += doc.page_content + "\n\n"

        prompt = f"""You are a helpful assistant. Use the following context to answer the question. If the answer is not in the context, say 'I don't know'.\n\nContext:\n{context}\n\nQuestion: {query}\nAnswer:"""
      
        result = llm.invoke(prompt)

        answer = ""

        if isinstance(result.content, list):
            for item in result.content:
                if isinstance(item, dict) and item.get("type") == "text":
                   answer += item.get("text", "")
        else:
            answer = result.content

        st.chat_message("assistant").markdown(answer)

#chatbot UI