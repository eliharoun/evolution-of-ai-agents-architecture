"""
FAQ retrieval tool using RAG (Retrieval Augmented Generation).
Implements semantic search with ChromaDB for persistent vector storage.
Includes text chunking as best practice for document preprocessing.
"""

from pathlib import Path
from typing import List, Dict, Optional

from langchain_core.tools import tool
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings

from common.logging_config import get_logger
from common.data.faqs import FAQ_DATA

logger = get_logger(__name__)


class FAQRetriever:
    """
    FAQ retrieval system using semantic search with embeddings.
    Uses SentenceTransformer for embeddings and ChromaDB for persistent storage.
    Implements text chunking for optimal retrieval.
    """
    
    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        persist_directory: Optional[Path] = None,
        collection_name: str = "faq_collection",
        chunk_size: int = 200,
        chunk_overlap: int = 50
    ):
        """
        Initialize the FAQ retriever with ChromaDB.
        
        Args:
            model_name: Name of the sentence transformer model to use
            persist_directory: Directory for ChromaDB persistence
            collection_name: Name of the ChromaDB collection
            chunk_size: Maximum size of text chunks
            chunk_overlap: Overlap between chunks for context preservation
        """
        self.model_name = model_name
        self.collection_name = collection_name
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Set default persist directory in common/data/chroma_db/
        if persist_directory is None:
            persist_directory = Path(__file__).parent.parent / "data" / "chroma_db"
        
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(exist_ok=True, parents=True)
        
        logger.info(f"FAQ retriever initializing - model: {model_name}, persist_dir: {self.persist_directory}, collection: {collection_name}, chunk_size: {chunk_size}")
        
        # Initialize sentence transformer model with explicit device and trust_remote_code
        try:
            self.model = SentenceTransformer(model_name, device='cpu', trust_remote_code=True)
            # Ensure model is in eval mode
            self.model.eval()
            logger.info(f"Embedding model loaded successfully on CPU")
        except Exception as e:
            logger.error(f"Error loading embedding model: {str(e)}")
            # Fallback: try without trust_remote_code
            self.model = SentenceTransformer(model_name, device='cpu')
            self.model.eval()
            logger.info(f"Embedding model loaded with fallback configuration")
        
        # Initialize text splitter for chunking
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            is_separator_regex=False
        )
        
        # Initialize ChromaDB client with persistence
        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Get or create collection
        self.collection = self._get_or_create_collection()
        
        logger.info(f"FAQ retriever ready - {self.collection.count()} FAQs in collection '{collection_name}'")
    
    def _get_or_create_collection(self):
        """
        Get existing collection or create new one with FAQ data.
        
        Returns:
            ChromaDB collection
        """
        try:
            # Try to get existing collection
            collection = self.client.get_collection(name=self.collection_name)
            
            # Check if collection has data
            if collection.count() > 0:
                logger.info(f"Collection loaded: '{self.collection_name}' with {collection.count()} documents")
                return collection
            else:
                logger.info(f"Collection exists but empty: '{self.collection_name}', recreating")
                # Delete empty collection and recreate
                self.client.delete_collection(name=self.collection_name)
                
        except Exception as e:
            logger.info(f"Collection not found: '{self.collection_name}', creating new")
        
        # Create new collection and populate it
        return self._create_and_populate_collection()
    
    def _create_and_populate_collection(self):
        """
        Create a new collection and populate it with chunked FAQ data.
        
        Returns:
            ChromaDB collection with FAQ data
        """
        logger.info(f"Creating new collection: '{self.collection_name}'")
        
        # Create collection
        collection = self.client.create_collection(
            name=self.collection_name,
            metadata={"description": "FAQ knowledge base for clothing retailer"}
        )
        
        # Prepare documents for chunking and embedding
        documents = []
        metadatas = []
        ids = []
        chunk_counter = 0
        
        for i, faq in enumerate(FAQ_DATA):
            # Combine question and answer for richer context
            doc_text = f"{faq['category']}: {faq['question']} {faq['answer']}"
            
            # Chunk the text (even though FAQs are small, this demonstrates the pattern)
            chunks = self.text_splitter.split_text(doc_text)
            
            logger.debug(f"FAQ {i} chunked - original: {len(doc_text)} chars, chunks: {len(chunks)}")
            
            # Add each chunk to the collection
            for chunk_idx, chunk in enumerate(chunks):
                documents.append(chunk)
                
                # Store metadata with chunk information
                metadatas.append({
                    "category": faq["category"],
                    "question": faq["question"],
                    "answer": faq["answer"],
                    "faq_index": i,
                    "chunk_index": chunk_idx,
                    "total_chunks": len(chunks)
                })
                
                # Create unique ID for each chunk
                ids.append(f"faq_{i}_chunk_{chunk_idx}")
                chunk_counter += 1
        
        # Generate embeddings for all chunks
        logger.info(f"Generating embeddings for {len(documents)} documents ({chunk_counter} total chunks)")
        embeddings = self.model.encode(documents, convert_to_numpy=True).tolist()
        
        # Add to collection
        collection.add(
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )
        
        logger.info(f"Collection '{self.collection_name}' populated - {collection.count()} docs, {len(FAQ_DATA)} FAQs, {chunk_counter} chunks")
        
        return collection
    
    def search(self, query: str, top_k: int = 2) -> List[Dict]:
        """
        Search for relevant FAQs using semantic similarity.
        
        Args:
            query: User's question or query
            top_k: Number of top results to return
            
        Returns:
            List of relevant FAQ dictionaries with similarity scores
        """
        logger.info(f"FAQ search - query: '{query[:100]}...', top_k: {top_k}")
        
        try:
            # Generate query embedding
            query_embedding = self.model.encode([query], convert_to_numpy=True).tolist()
            
            # Query the collection
            results = self.collection.query(
                query_embeddings=query_embedding,
                n_results=top_k
            )
            
            # Format results and deduplicate by FAQ (since we chunked)
            seen_faq_indices = set()
            formatted_results = []
            
            if results and results['metadatas'] and len(results['metadatas']) > 0:
                for i, metadata in enumerate(results['metadatas'][0]):
                    faq_index = metadata["faq_index"]
                    
                    # Skip if we've already included this FAQ
                    if faq_index in seen_faq_indices:
                        continue
                    
                    seen_faq_indices.add(faq_index)
                    
                    result = {
                        "category": metadata["category"],
                        "question": metadata["question"],
                        "answer": metadata["answer"],
                        "distance": results['distances'][0][i] if results['distances'] else None,
                        "chunk_info": f"chunk {metadata['chunk_index']+1}/{metadata['total_chunks']}"
                    }
                    formatted_results.append(result)
                    
                    # Stop once we have enough unique FAQs
                    if len(formatted_results) >= top_k:
                        break
            
            chunks_examined = len(results['metadatas'][0]) if results['metadatas'] else 0
            logger.info(f"FAQ search complete - query: '{query[:100]}...', found: {len(formatted_results)}, examined: {chunks_examined} chunks")
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"FAQ search error for '{query[:100]}...': {str(e)}")
            return []


# Global FAQ retriever instance
_faq_retriever: Optional[FAQRetriever] = None


def get_faq_retriever() -> FAQRetriever:
    """
    Get the global FAQ retriever instance (lazy initialization).
    
    Returns:
        FAQRetriever instance
    """
    global _faq_retriever
    if _faq_retriever is None:
        _faq_retriever = FAQRetriever()
    return _faq_retriever


@tool
def search_faq(query: str) -> str:
    """
    Search the FAQ knowledge base for relevant information.
    
    Use this tool when customers ask general questions about policies, shipping,
    returns, payments, products, or account management. The tool uses semantic
    search to find the most relevant FAQ entries based on the customer's question.
    
    Args:
        query: The customer's question or search query
        
    Returns:
        A formatted string with relevant FAQ answers
        
    Example:
        >>> search_faq("How do I return an item?")
        "Here are the most relevant FAQs:\\n\\n1. Q: How do I return an item?\\n..."
    """
    logger.info(f"FAQ tool called with query: '{query[:100]}...'")
    
    try:
        retriever = get_faq_retriever()
        results = retriever.search(query, top_k=2)
        
        if not results:
            return "I couldn't find any relevant FAQs for your question. Please contact our customer support team for personalized assistance."
        
        # Format the results
        response = "Here are the most relevant FAQs:\n\n"
        
        for i, faq in enumerate(results, 1):
            response += f"{i}. **{faq['category']}**: {faq['question']}\n"
            response += f"   {faq['answer']}\n\n"
        
        logger.info(f"FAQ tool success - query: '{query[:100]}...', results: {len(results)}")
        
        return response.strip()
        
    except Exception as e:
        logger.error(f"FAQ tool error for '{query[:100]}...': {str(e)}")
        return "An error occurred while searching the FAQ. Please try rephrasing your question or contact our support team."
