from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, TIMESTAMP
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class KnowledgeBase(Base):
    __tablename__ = "knowledge_bases"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    chroma_collection_name = Column(String(100), nullable=False)
    files = relationship("KbFile", back_populates="kb", cascade="all, delete-orphan")

class KbFile(Base):
    __tablename__ = "kb_files"
    id = Column(Integer, primary_key=True, index=True)
    kb_id = Column(Integer, ForeignKey("knowledge_bases.id"), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    status = Column(String(20), default="processing")
    chunk_count = Column(Integer, default=0)
    kb = relationship("KnowledgeBase", back_populates="files")

class ChatSession(Base):
    __tablename__ = "chat_sessions"
    id = Column(String(64), primary_key=True, index=True)
    kb_id = Column(Integer, ForeignKey("knowledge_bases.id"), nullable=True)
    title = Column(String(200))
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(64), ForeignKey("chat_sessions.id"), nullable=False)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    sources = Column(JSON, nullable=True)
    session = relationship("ChatSession", back_populates="messages")