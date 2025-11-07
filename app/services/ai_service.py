import os
import json
import pickle
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import mimetypes
import logging
from datetime import datetime
from sqlalchemy.orm import Session

# AI and text processing imports
import openai
from openai import OpenAI

# Optional dependencies for better functionality
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    # Fallback to basic Python lists for vector operations
    
try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    
try:
    import docx
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SimpleVectorDB:
    """
    Simple in-memory vector database with file persistence
    Can be easily replaced with ChromaDB, Pinecone, or other vector databases
    """
    
    def __init__(self, storage_path: str = "vector_db"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)
        
        self.embeddings = {}  # id -> embedding vector
        self.metadata = {}    # id -> metadata dict
        self.index_file = self.storage_path / "index.pkl"
        self.metadata_file = self.storage_path / "metadata.json"
        
        self._load_data()
    
    def _load_data(self):
        """Load existing data from disk"""
        try:
            if self.index_file.exists():
                with open(self.index_file, 'rb') as f:
                    self.embeddings = pickle.load(f)
            
            if self.metadata_file.exists():
                with open(self.metadata_file, 'r') as f:
                    self.metadata = json.load(f)
        except Exception as e:
            logger.error(f"Error loading vector DB data: {e}")
            self.embeddings = {}
            self.metadata = {}
    
    def _save_data(self):
        """Save data to disk"""
        try:
            with open(self.index_file, 'wb') as f:
                pickle.dump(self.embeddings, f)
            
            with open(self.metadata_file, 'w') as f:
                json.dump(self.metadata, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving vector DB data: {e}")
    
    def add_embedding(self, doc_id: str, embedding: List[float], metadata: Dict[str, Any]):
        """Add or update an embedding"""
        if NUMPY_AVAILABLE:
            self.embeddings[doc_id] = np.array(embedding)
        else:
            self.embeddings[doc_id] = embedding
        self.metadata[doc_id] = metadata
        self._save_data()
    
    def search(self, query_embedding: List[float], top_k: int = 5, min_similarity: float = 0.7) -> List[Tuple[str, float, Dict[str, Any]]]:
        """Search for similar embeddings"""
        if not self.embeddings:
            return []
        
        results = []
        
        for doc_id, doc_embedding in self.embeddings.items():
            # Cosine similarity calculation
            if NUMPY_AVAILABLE:
                query_vec = np.array(query_embedding)
                doc_vec = np.array(doc_embedding) if isinstance(doc_embedding, list) else doc_embedding
                similarity = np.dot(query_vec, doc_vec) / (
                    np.linalg.norm(query_vec) * np.linalg.norm(doc_vec)
                )
            else:
                # Fallback cosine similarity calculation without numpy
                similarity = self._cosine_similarity_fallback(query_embedding, doc_embedding)
            
            if similarity >= min_similarity:
                results.append((doc_id, float(similarity), self.metadata[doc_id]))
        
        # Sort by similarity and return top_k
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]
    
    def _cosine_similarity_fallback(self, vec1: List[float], vec2: List[float]) -> float:
        """Fallback cosine similarity without numpy"""
        try:
            # Ensure vec2 is a list if it was stored as numpy array
            if hasattr(vec2, 'tolist'):
                vec2 = vec2.tolist()
            
            # Dot product
            dot_product = sum(a * b for a, b in zip(vec1, vec2))
            
            # Magnitudes
            magnitude1 = sum(a * a for a in vec1) ** 0.5
            magnitude2 = sum(b * b for b in vec2) ** 0.5
            
            if magnitude1 == 0 or magnitude2 == 0:
                return 0.0
            
            return dot_product / (magnitude1 * magnitude2)
        except Exception:
            return 0.0
    
    def remove_embedding(self, doc_id: str):
        """Remove an embedding"""
        if doc_id in self.embeddings:
            del self.embeddings[doc_id]
        if doc_id in self.metadata:
            del self.metadata[doc_id]
        self._save_data()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        return {
            "total_documents": len(self.embeddings),
            "total_size_mb": len(pickle.dumps(self.embeddings)) / (1024 * 1024)
        }


class AIService:
    """
    AI Service for college knowledge management and intelligent search
    """
    
    def __init__(self, openai_api_key: str):
        self.client = OpenAI(api_key=openai_api_key)
        self.vector_db = SimpleVectorDB()
        self.embedding_model = "text-embedding-ada-002"
        self.chat_model = "gpt-3.5-turbo"
    
    def extract_text_from_file(self, file_path: str, mime_type: str) -> str:
        """Extract text content from various file types"""
        try:
            if mime_type.startswith('text/') or file_path.endswith('.txt'):
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read()
            
            elif mime_type == 'application/pdf' and PDF_AVAILABLE:
                text = ""
                with open(file_path, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    for page in reader.pages:
                        text += page.extract_text() + "\n"
                return text
            
            elif mime_type in ['application/vnd.openxmlformats-officedocument.wordprocessingml.document'] and DOCX_AVAILABLE:
                doc = docx.Document(file_path)
                text = ""
                for paragraph in doc.paragraphs:
                    text += paragraph.text + "\n"
                return text
            
            else:
                # For unsupported file types, return filename and basic info
                return f"File: {Path(file_path).name}"
                
        except Exception as e:
            logger.error(f"Error extracting text from {file_path}: {e}")
            return f"File: {Path(file_path).name} (content extraction failed)"
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using OpenAI"""
        try:
            # Truncate text if too long (OpenAI has token limits)
            if len(text) > 8000:
                text = text[:8000] + "... [truncated]"
            
            response = self.client.embeddings.create(
                model=self.embedding_model,
                input=text
            )
            return response.data[0].embedding
        
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise
    
    def index_file(self, file_id: int, file_path: str, original_filename: str, 
                   mime_type: str, description: str, department: str, 
                   college_name: str, uploader_name: str) -> bool:
        """Index a file for AI search"""
        try:
            # Extract text content
            content = self.extract_text_from_file(file_path, mime_type)
            
            # Create comprehensive text for embedding
            full_text = f"""
            Filename: {original_filename}
            Department: {department}
            College: {college_name}
            Uploaded by: {uploader_name}
            Description: {description or 'No description'}
            
            Content:
            {content}
            """
            
            # Generate embedding
            embedding = self.generate_embedding(full_text.strip())
            
            # Create metadata
            metadata = {
                "id": file_id,
                "type": "file",
                "filename": original_filename,
                "department": department,
                "college": college_name,
                "uploader": uploader_name,
                "description": description,
                "mime_type": mime_type,
                "content_preview": content[:500] + "..." if len(content) > 500 else content,
                "indexed_at": datetime.utcnow().isoformat()
            }
            
            # Store in vector database
            doc_id = f"file_{file_id}"
            self.vector_db.add_embedding(doc_id, embedding, metadata)
            
            logger.info(f"Successfully indexed file: {original_filename}")
            return True
            
        except Exception as e:
            logger.error(f"Error indexing file {file_id}: {e}")
            return False
    
    def index_post(self, post_id: int, title: str, content: str, post_type: str,
                   department: str, college_name: str, author_name: str) -> bool:
        """Index a post for AI search"""
        try:
            # Create comprehensive text for embedding
            full_text = f"""
            Post Title: {title}
            Type: {post_type}
            Department: {department}
            College: {college_name}
            Author: {author_name}
            
            Content:
            {content}
            """
            
            # Generate embedding
            embedding = self.generate_embedding(full_text.strip())
            
            # Create metadata
            metadata = {
                "id": post_id,
                "type": "post",
                "title": title,
                "post_type": post_type,
                "department": department,
                "college": college_name,
                "author": author_name,
                "content_preview": content[:500] + "..." if len(content) > 500 else content,
                "indexed_at": datetime.utcnow().isoformat()
            }
            
            # Store in vector database
            doc_id = f"post_{post_id}"
            self.vector_db.add_embedding(doc_id, embedding, metadata)
            
            logger.info(f"Successfully indexed post: {title}")
            return True
            
        except Exception as e:
            logger.error(f"Error indexing post {post_id}: {e}")
            return False
    
    def index_college_info(self, college_id: int, college_name: str, 
                          departments: List[str], stats: Dict[str, Any]) -> bool:
        """Index general college information"""
        try:
            # Create college info text
            full_text = f"""
            College: {college_name}
            Departments: {', '.join(departments)}
            Statistics: {json.dumps(stats, indent=2)}
            
            This is general information about {college_name} college, including 
            available departments and current statistics about files, posts, and users.
            """
            
            # Generate embedding
            embedding = self.generate_embedding(full_text.strip())
            
            # Create metadata
            metadata = {
                "id": college_id,
                "type": "college_info",
                "college": college_name,
                "departments": departments,
                "stats": stats,
                "indexed_at": datetime.utcnow().isoformat()
            }
            
            # Store in vector database
            doc_id = f"college_{college_id}"
            self.vector_db.add_embedding(doc_id, embedding, metadata)
            
            logger.info(f"Successfully indexed college info: {college_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error indexing college {college_id}: {e}")
            return False
    
    def search_knowledge_base(self, query: str, college_filter: Optional[str] = None, 
                            content_type: Optional[str] = None, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search the knowledge base with optional filters"""
        try:
            # Generate query embedding
            query_embedding = self.generate_embedding(query)
            
            # Search vector database
            results = self.vector_db.search(query_embedding, top_k=top_k * 2)  # Get more to allow filtering
            
            # Apply filters
            filtered_results = []
            for doc_id, similarity, metadata in results:
                # College filter
                if college_filter and metadata.get('college', '').lower() != college_filter.lower():
                    continue
                
                # Content type filter
                if content_type and metadata.get('type') != content_type:
                    continue
                
                filtered_results.append({
                    "doc_id": doc_id,
                    "similarity": similarity,
                    "metadata": metadata
                })
            
            return filtered_results[:top_k]
        
        except Exception as e:
            logger.error(f"Error searching knowledge base: {e}")
            return []
    
    def generate_ai_response(self, query: str, context_docs: List[Dict[str, Any]], 
                           college_name: str) -> str:
        """Generate AI response using retrieved context"""
        try:
            # Build context from retrieved documents
            context_text = ""
            for doc in context_docs:
                metadata = doc['metadata']
                similarity = doc['similarity']
                
                if metadata['type'] == 'file':
                    context_text += f"\n[File: {metadata['filename']} - Department: {metadata['department']} - Similarity: {similarity:.2f}]\n"
                    context_text += f"{metadata.get('content_preview', '')}\n"
                
                elif metadata['type'] == 'post':
                    context_text += f"\n[Post: {metadata['title']} - Type: {metadata['post_type']} - Author: {metadata['author']} - Similarity: {similarity:.2f}]\n"
                    context_text += f"{metadata.get('content_preview', '')}\n"
                
                elif metadata['type'] == 'college_info':
                    context_text += f"\n[College Information - Similarity: {similarity:.2f}]\n"
                    context_text += f"Departments: {', '.join(metadata.get('departments', []))}\n"
            
            # Create system prompt
            system_prompt = f"""
            You are an AI assistant for {college_name} college community. You have access to information about:
            - Academic files and documents from various departments
            - Posts and announcements from students and faculty  
            - College information including departments and statistics
            - Rewards and recognition programs
            
            Your role is to help students, faculty, and staff by providing accurate information based on the available knowledge.
            Be helpful, informative, and maintain a professional yet friendly tone.
            
            If you don't find relevant information in the provided context, politely say so and suggest they might want to:
            - Check for more recent posts or files
            - Contact their department directly
            - Upload relevant documents to help others
            
            Always cite your sources when referencing specific files or posts.
            """
            
            # Create user message with context
            user_message = f"""
            Question: {query}
            
            Available Context:
            {context_text}
            
            Please provide a helpful response based on the available information.
            """
            
            # Generate response using OpenAI
            response = self.client.chat.completions.create(
                model=self.chat_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=1000,
                temperature=0.7
            )
            
            return response.choices[0].message.content
        
        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            return "I'm sorry, I encountered an error while processing your question. Please try again later."
    
    def remove_from_index(self, doc_type: str, doc_id: int):
        """Remove a document from the index"""
        doc_key = f"{doc_type}_{doc_id}"
        self.vector_db.remove_embedding(doc_key)
    
    def get_index_stats(self) -> Dict[str, Any]:
        """Get indexing statistics"""
        return self.vector_db.get_stats()


# Global AI service instance
_ai_service = None

def get_ai_service() -> AIService:
    """Get or create AI service instance"""
    global _ai_service
    if _ai_service is None:
        # Try to get API key from config first, then environment
        try:
            from ..core.config import settings
            openai_api_key = settings.openai_api_key
        except ImportError:
            openai_api_key = os.getenv("OPENAI_API_KEY")
        
        if not openai_api_key or openai_api_key == "sk-your-openai-api-key-here":
            raise ValueError("OpenAI API key not properly configured. Please set it in config.py or .env file")
        _ai_service = AIService(openai_api_key)
    return _ai_service