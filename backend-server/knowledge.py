import hashlib
import os
import shutil
from typing import Optional
from sqlalchemy.orm import Session

from langchain_classic.indexes import SQLRecordManager
from langchain_classic.retrievers.contextual_compression import ContextualCompressionRetriever
from langchain_classic.retrievers.re_phraser import  RePhraseQueryRetriever
from langchain_classic.retrievers.ensemble import EnsembleRetriever
from langchain_classic.retrievers.document_compressors.chain_filter import LLMChainFilter
from langchain_classic.retrievers.document_compressors.cross_encoder_rerank import CrossEncoderReranker
from langchain_core.document_loaders.base import BaseLoader
from langchain_core.embeddings.embeddings import Embeddings
from langchain_core.indexing import index
from langchain_core.documents import Document
from langchain_chroma.vectorstores import Chroma
from langchain_community.retrievers.bm25 import BM25Retriever

from models import KnowledgeBase, KbFile
from custom_loader import MyCustomLoader
from util import get_lc_model_client, get_ali_embeddings, get_ali_rerank,ALLOWED_EXTENSIONS
from loguru import logger

# 设置知识库 向量模型 重排序模型的路径
KNOWLEDGE_DIR = './chroma/knowledge/'
# 确保 SQLite 目录存在
os.makedirs('./db', exist_ok=True)
SQLITE_DB_URL = "sqlite:///./db/record_manager_cache.db"
embedding_model = get_ali_embeddings()

def langchain_key_encoder(document: Document) -> str:
    """
    生成文档的唯一键。
    策略：源文件路径 + 文档内容前 500 字符的哈希 (防止内容变了但路径没变导致不更新)
    """
    source = document.metadata.get('source', 'unknown')
    content = document.page_content

    # 为了性能，只哈希部分内容，通常足够区分变化
    # 如果文档很短，就哈希全部
    content_sample = content[:500] if len(content) > 500 else content

    unique_str = f"{source}::{content_sample}"
    return hashlib.md5(unique_str.encode('utf-8')).hexdigest()

class MyKnowledge:
    """
    知识库管理模块
    """
    # 向量化模型
    __embeddings = embedding_model
    logger.info(f"当前嵌入模型: {__embeddings.model}")
    __chroma_instances = {}
    __llm = get_lc_model_client()

    def upload_file_to_knowledge_base(self, file, knowledge_base_id: int,db: Session):
        """
        将文件上传到指定的知识库 (knowledge_base_id)
        逻辑：
        1. 获取知识库信息，确定 Chroma Collection 名称
        2. 保存物理文件到 knowledge_base_id 子目录
        3. 记录 KbFile 到数据库
        4. 将文件内容索引到该 knowledge_base_id 对应的 Chroma Collection 中
        """
        # 1. 获取知识库信息
        kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == knowledge_base_id).first()
        if not kb:
            raise HTTPException(status_code=404, detail="知识库不存在")

        collection_name = kb.chroma_collection_name
        logger.info(f"正在上传文件到知识库: {kb.name} (Collection: {collection_name})")

        # 2. 保存物理文件 (按 kb_id 分类存储，避免文件名冲突)
        kb_dir = os.path.join(KNOWLEDGE_DIR, str(knowledge_base_id))
        os.makedirs(kb_dir, exist_ok=True)
        file_name = os.path.basename(file.filename)
        file_path = os.path.join(kb_dir, file_name)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        new_kb_file = KbFile(
            kb_id=knowledge_base_id,
            file_name=file_name,
            file_path=file_path,
            status="processing"
        )
        db.add(new_kb_file)
        db.commit()
        db.refresh(new_kb_file)

        # 4. 执行索引 (关键变化：多个文件共享一个 collection_name)
        try:
            loader = MyCustomLoader(file_path)
            # 这里的 create_indexes 需要稍微调整，或者复用，关键是 collection_name 是 kb 级别的
            self._index_documents(collection_name, loader)

            # 更新状态
            new_kb_file.status = "completed"
            # 可选：统计 chunk 数量 (需要在 loader 或 index 过程中获取，这里简化)
            new_kb_file.chunk_count = 0
            db.commit()

            logger.info(f"文件 {file_name} 索引完成到知识库 {knowledge_base_id}")
        except Exception as e:
            logger.error(f"上传后索引失败: {e}")
            new_kb_file.status = "failed"
            db.commit()
            raise e

        return {
            "file_id": new_kb_file.id,
            "file_name": file_name,
            "kb_id": knowledge_base_id
        }

    def _index_documents(self, collection_name: str, loader: BaseLoader):
        """
        内部方法：将文档索引到指定的 collection
        支持增量索引：LangChain 的 index 函数配合 SQLRecordManager 会自动处理去重和更新
        """
        persist_dir = os.path.join('./chroma', collection_name)
        # 初始化Chroma数据库
        db = Chroma(collection_name=collection_name,
                    embedding_function=self.__embeddings,
                    persist_directory=persist_dir)

        record_manager = SQLRecordManager(
            f"chromadb/{collection_name}", db_url=SQLITE_DB_URL
        )
        logger.info(f"record_manager: {record_manager}")
        record_manager.create_schema()
        logger.info("准备进行文件的加载切分....")
        documents = loader.load()
        logger.info(f"文档切分数量：{len(documents)}....")
        if not documents:
            logger.warning("未加载到任何文档")
            return
        r = index(documents, record_manager, db, cleanup="full", source_id_key="source", key_encoder=langchain_key_encoder)
        logger.info(f"文档索引结果为：{r}")

    def get_retrievers_by_knowledge_base_id(self, knowledge_base_id: int, db: Session):
        """
        根据知识库 ID 获取检索器
        该检索器包含该知识库下所有已索引文件的内容
        """
        kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == knowledge_base_id).first()
        if not kb:
            raise HTTPException(status_code=404, detail="知识库不存在")
            return None

        collection_name = kb.chroma_collection_name
        logger.debug(f"请求检索器 for KB ID: {knowledge_base_id} (Collection: {collection_name})")
        # 1. 获取或加载 Chroma 实例
        if collection_name not in self.__chroma_instances:
            persist_dir = os.path.join('./chroma', collection_name)
            if not os.path.exists(persist_dir):
                logger.warning(f"向量库目录不存在：{persist_dir}")
                return None

            db_vector = Chroma(
                collection_name=collection_name,
                embedding_function=self.__embeddings,
                persist_directory=persist_dir
            )
            self.__chroma_instances[collection_name] = db_vector
        else:
            db_vector = self.__chroma_instances[collection_name]
        # 2. 构建 BM25 (注意：多文件情况下，动态构建 BM25 需要加载该 KB 下所有文件)
        # 优化建议：生产环境建议持久化 BM25 索引，这里为了演示逻辑，遍历该 KB 下所有成功索引的文件
        kb_files = db.query(KbFile).filter(KbFile.kb_id == knowledge_base_id, KbFile.status == "completed").all()
        logger.info(f"知识库 {knowledge_base_id} 下有 {len(kb_files)} 个文件")
        all_docs = []
        for kb_file in kb_files:
            if os.path.exists(kb_file.file_path):
                try:
                    temp_docs = MyCustomLoader(kb_file.file_path).load()
                    all_docs.extend(temp_docs)
                except Exception as e:
                    logger.warning(f"加载文件 {kb_file.file_name} 用于 BM25 失败：{e}")
        bm25_retriever = None
        if all_docs:
            bm25_retriever = BM25Retriever.from_documents(all_docs)
            logger.debug(f"BM25 构建完成，共 {len(all_docs)} 个文档片段")
        else:
            logger.warning(f"知识库 {knowledge_base_id} 下没有找到可构建 BM25 的文档")
        # 3. 构建基础检索器 (向量 或 混合)
        if bm25_retriever:
            base_retriever = EnsembleRetriever(
                retrievers=[db_vector.as_retriever(search_kwargs={"k": 5}), bm25_retriever],
                weights=[0.5, 0.5]
            )
        else:
            base_retriever = db_vector.as_retriever(search_kwargs={"k": 5})

        # 4. 构建压缩链 (LLM 过滤 + 重述)
        compression_retriever = ContextualCompressionRetriever(
            base_compressor=LLMChainFilter.from_llm(self.__llm),
            base_retriever=RePhraseQueryRetriever.from_llm(base_retriever, self.__llm)
        )
        # 5. 重排序 (Rerank)
        try:
            rerank_retriever = get_ali_rerank(top_n=3)
            final_retriever = ContextualCompressionRetriever(
                base_compressor=rerank_retriever,
                base_retriever=compression_retriever
            )
        except Exception as e:
            logger.error(f"初始化 Rerank 模型失败：{e}")
            final_retriever = compression_retriever

        return final_retriever

    def delete_knowledge_base(self, knowledge_base_id: int, db: Session):
        """
        彻底删除整个知识库，包括：
        - 数据库记录 (KnowledgeBase + KbFile)
        - 物理文件目录 (./chroma/knowledge/{kb_id})
        - Chroma 持久化目录 (./chroma/{collection_name})
        - SQLRecordManager 记录
        """
        kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == knowledge_base_id).first()
        if not kb:
            return {"status": "knowledge base not found"}

        collection_name = kb.chroma_collection_name
        persist_dir = os.path.join('./chroma', collection_name)
        kb_dir = os.path.join(KNOWLEDGE_DIR, str(knowledge_base_id))  # './chroma/knowledge/{kb_id}'

        try:
            db.rollback()  # 事务回滚保护
            import gc
            import time
            from sqlalchemy import create_engine, text

            # 1. 从内存中移除 Chroma 实例（避免文件锁）
            if collection_name in self.__chroma_instances:
                del self.__chroma_instances[collection_name]
                gc.collect()
                time.sleep(0.3)  # Windows 文件锁释放
                logger.info(f"已从内存移除 Chroma: {collection_name}")

            # 2. 删除知识文件目录（包含所有上传文件）
            if os.path.exists(kb_dir):
                shutil.rmtree(kb_dir, ignore_errors=True)
                logger.info(f"已删除文件目录: {kb_dir}")

            # 3. 删除 Chroma 持久化目录（向量索引）
            if os.path.exists(persist_dir):
                shutil.rmtree(persist_dir, ignore_errors=True)
                logger.info(f"已删除 Chroma 目录: {persist_dir}")

            # 4. 清理 SQLRecordManager（upsertion_record 表）
            engine = create_engine(SQLITE_DB_URL)
            with engine.connect() as conn:
                conn.execute(text("DELETE FROM upsertion_record WHERE namespace = :ns"),
                            {"ns": f"chromadb/{collection_name}"})
                conn.commit()
            logger.info(f"已清理 RecordManager: chromadb/{collection_name}")

            # 5. 删除数据库记录
            db.query(KbFile).filter(KbFile.kb_id == knowledge_base_id).delete()
            db.delete(kb)
            db.commit()

            logger.info(f"知识库 {knowledge_base_id} ({kb.name}) 删除完成")
            return {"status": "deleted successfully"}

        except Exception as e:
            db.rollback()
            logger.error(f"删除知识库失败 {knowledge_base_id}: {e}")
            return {"status": "error", "message": str(e)}

    def delete_knowledge_base_files_by_id(self, knowledge_base_id: int, file_id: int, db: Session):
        """
        删除知识库中的特定文件、物理文件、索引和记录
        """
        # 1. 获取文件记录并删除数据库记录 ，如果文件不存在，返回错误
        kb_file = db.query(KbFile).filter(KbFile.kb_id == knowledge_base_id, KbFile.id == file_id).first()
        if not kb_file:
            return {"status": "file not found"}

        file_path = kb_file.file_path
        file_name = kb_file.file_name
        collection_name = db.query(KnowledgeBase).filter(KnowledgeBase.id == knowledge_base_id).first().chroma_collection_name

        # 删除物理文件
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"已删除物理文件: {file_path}")

        db.delete(kb_file)
        db.commit()

        # 2. 重新索引 collection，cleanup="full" 会删除已不存在的文档
        persist_dir = os.path.join('./chroma', collection_name)
        chroma_db = Chroma(
            collection_name=collection_name,
            embedding_function=self.__embeddings,
            persist_directory=persist_dir
        )

        # 获取该 KB 下剩余所有文件，重新加载并索引
        remaining_files = db.query(KbFile).filter(
            KbFile.kb_id == knowledge_base_id,
            KbFile.status == "completed"
        ).all()

        all_docs = []
        for f in remaining_files:
            if os.path.exists(f.file_path):
                loader = MyCustomLoader(f.file_path)
                all_docs.extend(loader.load())

        if all_docs:
            record_manager = SQLRecordManager(
                f"chromadb/{collection_name}", db_url=SQLITE_DB_URL
            )
            index(all_docs, record_manager, chroma_db, cleanup="full",
                source_id_key="source", key_encoder=langchain_key_encoder)
            logger.info(f"重新索引 {collection_name}，已删除 {file_name} 的 chunks")
        else:
            # 如果没有剩余文件，清空 collection
            chroma_db.delete_collection()
            logger.info(f"清空空 collection: {collection_name}")

        # 3. 可选：清理 record_manager 旧记录（SQL 删除）
        from sqlalchemy import create_engine, text
        engine = create_engine(SQLITE_DB_URL)
        with engine.connect() as conn:
            conn.execute(text("DELETE FROM upsertion_record WHERE namespace = :ns"),
                        {"ns": f"chromadb/{collection_name}"})
            conn.commit()

        return {"status": "deleted", "file_id": file_id}
