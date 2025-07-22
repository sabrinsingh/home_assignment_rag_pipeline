from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import chromadb
from langchain_ollama import OllamaLLM
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="RAG API", description="Ask questions and get answers using RAG!", version="1.0")

CHROMA_PATH = "./data/gold/chroma"

# Initialize persistent chromadb client and collection
try:
    logger.info("📦 Connecting to Chroma vector DB...")
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = client.get_collection(name="rag_docs")
    # collection = chroma_client.get_or_create_collection(name="rag_docs")
    logger.info("🧠 Loading local language model...")
    llm = OllamaLLM(model="phi3")
except Exception as e:
    logger.error("❌ Failed to initialize models/vector store", exc_info=True)
    raise RuntimeError("Initialization failed. Check logs.") from e

class Question(BaseModel):
    query: str

@app.get("/")
def read_root():
    return {"message": "👋 Welcome! Your RAG API is up and running."}

@app.post("/query/")
def ask_question(question: Question):
    logger.info(f"Received query: {question.query}")

    try:
        # Query the vector store for top 3 docs
        results = collection.query(
            query_texts=[question.query],
            n_results=3,
            include=["documents", "metadatas", "distances"]
        )
        docs = results["documents"][0]
        if not docs:
            return {"question": question.query, "answer": "No relevant documents found.", "context": ""}

        # Prepare context by joining docs
        context = "\n\n".join(docs)

        prompt = f"""Answer the following question using the context below:

Context:
{context}

Question:
{question.query}

Answer:"""

        # Generate answer using the LLM
        response = llm.invoke(prompt)

        logger.info("LLM response generated")
        return {
            "question": question.query,
            "answer": response.strip(),
            "context": context
        }

    except Exception as e:
        logger.error("Error processing query", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error")


