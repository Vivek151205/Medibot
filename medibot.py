import streamlit as st
import os
from langchain_huggingface import HuggingFaceEndpoint
from langchain_core.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.embeddings import HuggingFaceEmbeddings
from langchain_core.prompts import PromptTemplate
from langchain_community.vectorstores import FAISS
HF_TOKEN=os.environ.get("HF_TOKEN")
HUGGINGFACE_REPO_ID="deepseek-ai/DeepSeek-R1-Distill-Qwen-32B"
DB_FAISS_PATH="vectorstore/db_faiss"

@st.cache_resource #loading the data into cache 
def get_vectorstore():
    embedding_model=HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    db=FAISS.load_local(DB_FAISS_PATH,embedding_model,allow_dangerous_deserialization=True)
    return db


def set_custom_prompt(custom_prompt_template):
    prompt=PromptTemplate(template=custom_prompt_template, input_variables=["context", "question"])
    return prompt

def load_llm(huggingface_repo_id):
    llm=HuggingFaceEndpoint(
        repo_id=huggingface_repo_id,
        temperature=0.5,
        model_kwargs={"token":HF_TOKEN,
                      }
    )
    return llm

def main():
    st.title("Ask Chatbot")
    if 'messages' not in st.session_state:
        st.session_state.messages=[]
    for message in st.session_state.messages:
        st.chat_message(message['role']).markdown(message['content'])
    prompt=st.chat_input("Pass youe prompt here ")
    if prompt:
        st.chat_message('user').markdown(prompt)
        st.session_state.messages.append({'role':'user', 'content': prompt})
        CUSTOM_PROMPT_TEMPLATE = """
            Use the pieces of information provided in the context to answer user's question.
            If you dont know the answer, just say that you dont know, dont try to make up an answer. 
            Dont provide anything out of the given context

            Context: {context}
            Question: {question}

            Start the answer directly. No small talk please.
            """
        
        try:

            vectorstore=get_vectorstore()
            if vectorstore is None:
                st.error("Failed to load the vector store")
            qa_chain=RetrievalQA.from_chain_type(
                llm=load_llm(HUGGINGFACE_REPO_ID),
                chain_type="stuff",
                retriever=vectorstore.as_retriever(search_kwargs={'k':3}),
                return_source_documents=True,
                chain_type_kwargs={'prompt':set_custom_prompt(CUSTOM_PROMPT_TEMPLATE)}
            )
            response=qa_chain.invoke({'query': prompt})
            result=response["result"]
            source_documents=response["source_documents"]

            result_to_show=result+"\n\nSource Documents: \n"+str(source_documents)
            st.chat_message('assistant').markdown(result_to_show)
            st.session_state.messages.append({'role':'assistant', 'content': result_to_show})
        except Exception as e:
            st.error(f"Error: {str(e)}")


if __name__=="__main__":
    main()