# MLOps Integration Guide for Open-Books

## 1. Opik: For Prompt Versioning & RAG Tracing

**Use Case**: Track "Which prompt created this answer?" and "What exact context was retrieved?".
**Location**: `src/assistant` or `src/rag`

### Setup
Add `opik` to your project:
```bash
uv add opik
```

### Integration Code
Use the `opik.Prompt` object to manage versions and `@track` to trace execution.

```python
import opik
from opik import track

# 1. Define your prompt. 
# Opik will version this automatically when you change the template string.
# You can view/edit these versions in the Opik Dashboard.
response_prompt = opik.Prompt(
    name="book_assistant_response",
    prompt_template="""
    You are a helpful librarian assistant. Use the context below to answer detailed questions.
    
    Context:
    {{context}}
    
    Question:
    {{question}}
    """
)

@track(name="retrieve_context")
def retrieve_docs(query: str):
    # Your existing vector DB search logic here
    # Opik will trace how long this takes and what it returns
    # Example placeholder:
    results = ["(content of book page 10)", "(content of book page 11)"] 
    return results

@track(name="generate_answer")
def generate_response(question: str):
    # 2. Retrieve Context
    context_docs = retrieve_docs(question)
    context_str = "\n".join(context_docs)
    
    # 3. Build Prompt from versioned template
    # This logs which version of the prompt is being used for this specific run
    formatted_prompt = response_prompt.format(
        context=context_str, 
        question=question
    )
    
    # 4. Call LLM (standard code)
    # response = client.chat.completions.create(model="gpt-4", messages=[...])
    # return response.choices[0].message.content
    
    return "This is a placeholder answer from the LLM."
```

## 2. ZenML: For Ingestion Pipelines

**Use Case**: "I want to re-run embedding, but I don't want to re-parse 500 PDFs if the parser code hasn't changed."
**Location**: `src/ingestion`

### Setup
```bash
uv add zenml
zenml init
```

### Integration Code
Wrap your ingestion logic into "steps" and a "pipeline".

```python
from zenml import step, pipeline
from typing import List

# Define a simple data structure for passing data between steps
class Document:
    content: str
    metadata: dict

@step
def load_pdfs(pdf_dir: str) -> List[Document]:
    """Wraps your existing Docling/PDF parsing logic."""
    print(f"Loading PDFs from {pdf_dir}")
    # Call your existing code:
    # docs = ingestion.loader.load(pdf_dir)
    return [Document(content="sample text", metadata={"source": "book.pdf"})]

@step
def chunk_text(documents: List[Document]) -> List[str]:
    """Wraps your MarkdownChunker."""
    chunks = []
    for doc in documents:
        # Call your existing chunker
        # chunked = ingestion.chunker.split(doc.content)
        chunks.append(doc.content) 
    return chunks

@step
def embed_and_store(chunks: List[str]):
    """Wraps your Embedding and Redis/Chroma logic."""
    print(f"Embedding {len(chunks)} chunks...")
    # ingestion.embedder.embed(chunks)
    # ingestion.store.save(vectors)

@pipeline
def book_ingestion_pipeline(dir_path: str):
    # Connect the steps
    docs = load_pdfs(dir_path)
    chunks = chunk_text(docs)
    embed_and_store(chunks)

if __name__ == "__main__":
    # If you run this twice, ZenML will CACHE 'load_pdfs' if code/input hasn't changed.
    book_ingestion_pipeline(dir_path="/home/user/books")
```
