import os
import json
import fitz  # PyMuPDF
import chromadb
from sentence_transformers import SentenceTransformer
from google import genai
from google.genai import types

# ── Setup ──────────────────────────────────────────────────────────────────
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

SYSTEM_PROMPT = """You are Priya, an expert ESG analyst specialising in Indian 
sustainability reporting — GRI Standards, BRSR, SASB, GHG Protocol.

CRITICAL RULE: Answer ONLY using the document excerpts provided in <context> tags.
If the answer is not in the provided context, say exactly:
"I couldn't find specific information about that in the loaded documents. 
Please check the source document directly or rephrase your question."

Always cite which section of the document your answer comes from.
Be specific, direct, and actionable."""

# ── Step 1: Load and chunk the PDF ────────────────────────────────────────
def load_and_chunk_pdf(pdf_path, chunk_size=500, overlap=50):
    """
    Loads a PDF and splits it into overlapping chunks.
    chunk_size: number of words per chunk
    overlap: words shared between consecutive chunks (preserves context)
    """
    print(f"Loading PDF: {pdf_path}")
    doc = fitz.open(pdf_path)
    
    full_text = ""
    for page_num, page in enumerate(doc):
        text = page.get_text()
        full_text += f"\n[Page {page_num + 1}]\n{text}"
    
    # Split into words
    words = full_text.split()
    chunks = []
    
    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i:i + chunk_size])
        if chunk:
            chunks.append({
                "text": chunk,
                "chunk_id": f"chunk_{i}",
                "source": pdf_path
            })
    
    print(f"Created {len(chunks)} chunks from {len(doc)} pages")
    return chunks

# ── Step 2: Create embeddings and store in ChromaDB ───────────────────────
def build_vector_store(chunks, collection_name="esg_documents"):
    """
    Converts chunks to embeddings and stores in ChromaDB.
    """
    print("Loading embedding model...")
    embedder = SentenceTransformer("all-MiniLM-L6-v2")
    
    print("Creating embeddings and building vector store...")
    chroma_client = chromadb.Client()
    
    # Delete collection if it exists (fresh start)
    try:
        chroma_client.delete_collection(collection_name)
    except:
        pass
    
    collection = chroma_client.create_collection(collection_name)
    
    # Add chunks in batches
    texts = [c["text"] for c in chunks]
    ids = [c["chunk_id"] for c in chunks]
    
    embeddings = embedder.encode(texts).tolist()
    
    collection.add(
        documents=texts,
        embeddings=embeddings,
        ids=ids
    )
    
    print(f"Vector store built with {len(chunks)} chunks")
    return collection, embedder

# ── Step 3: Search for relevant chunks ────────────────────────────────────
def search_documents(query, collection, embedder, n_results=4):
    """
    Finds the most relevant document chunks for a given query.
    """
    query_embedding = embedder.encode([query]).tolist()
    
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=n_results
    )
    
    return results["documents"][0]  # Returns list of relevant chunks

# ── Step 4: Answer with RAG ───────────────────────────────────────────────
def ask_priya_rag(question, collection, embedder):
    """
    Retrieves relevant document sections then answers using Priya.
    """
    # Find relevant chunks
    relevant_chunks = search_documents(question, collection, embedder)
    
    # Build context from chunks
    context = "\n\n---\n\n".join(relevant_chunks)
    
    # Build prompt with context
    prompt = f"""
<context>
The following excerpts are from official ESG/BRSR documents:

{context}
</context>

<question>
{question}
</question>

Answer based only on the context provided above.
"""
    
    response = client.models.generate_content(
        model="models/gemini-2.5-flash",
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT
        ),
        contents=prompt
    )
    
    return response.text

# ── Main: Build and run ───────────────────────────────────────────────────
def main():
    # Check for PDF
    pdf_path = "brsr.pdf"
    if not os.path.exists(pdf_path):
        pdf_path = "document.pdf"
        if not os.path.exists(pdf_path):
            print("ERROR: No PDF found.")
            print("Please save a BRSR or GRI PDF as 'brsr.pdf' in this folder.")
            print(f"Current folder: {os.getcwd()}")
            return
    
    # Build the RAG system
    chunks = load_and_chunk_pdf(pdf_path)
    collection, embedder = build_vector_store(chunks)
    
    print("\n" + "="*60)
    print("Priya is now reading from your documents.")
    print("Every answer will be grounded in the actual source text.")
    print("="*60)
    
    # Show one example
    example_q = "What are the key environmental disclosures required?"
    print(f"\nExample question: {example_q}")
    print(f"\nPriya: {ask_priya_rag(example_q, collection, embedder)}")
    print("\n" + "-"*60)
    print("Now ask your own questions. Type 'quit' to exit.\n")
    
    # Interactive loop
    while True:
        question = input("You: ")
        if question.lower() == "quit":
            print("Goodbye!")
            break
        answer = ask_priya_rag(question, collection, embedder)
        print(f"\nPriya: {answer}\n")

if __name__ == "__main__":
    main()
    