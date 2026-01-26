
---

## Phase 4: AI & Knowledge Ingestion
**Priority: HIGH | Estimated Effort: 16 hours**

### 4.1 Document Processor
#### Tasks:
- [ ] **4.1.1** Implement `DocumentProcessor` class for PDFs (PyMuPDF)
- [ ] **4.1.2** Implement `DrawingProcessor` class for DWGs (ezdxf)
- [ ] **4.1.3** create text chunking strategy (semantic splitting)

### 4.2 Vector Store
#### Tasks:
- [ ] **4.2.1** Implement `VectorStore` interface (abstract base)
- [ ] **4.2.2** Implement ChromaDB adapter (local storage)
- [ ] **4.2.3** Implement Pinecone adapter (optional cloud storage)

### 4.3 Embeddings
#### Tasks:
- [ ] **4.3.1** Implement `EmbeddingGenerator` using generic model output (e.g. OpenAI/Voyage via config)

### 4.4 RAG Engine
#### Tasks:
- [ ] **4.4.1** Implement `RAGEngine` to orchestrate retrieval
- [ ] **4.4.2** Connect RAG engine to Claude Bridge
