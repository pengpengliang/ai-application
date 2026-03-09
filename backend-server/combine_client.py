from typing import Iterable,Dict
from langchain_classic.chains.combine_documents.stuff import create_stuff_documents_chain
from langchain_classic.chains.retrieval import create_retrieval_chain
from langchain_core.messages.ai import AIMessageChunk
from langchain_core.prompts.chat import ChatPromptTemplate
from langchain_core.runnables.utils import AddableDict
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from loguru import logger
from fastapi import HTTPException
from models import ChatSession, ChatMessage  # 新增导入
from database import get_db  # 新增导入
from sqlalchemy.orm import Session

from knowledge import MyKnowledge
from util import ALI_TONGYI_MAX_MODEL, get_lc_model_client

# 知识库问答指令
qa_system_prompt = """你是一名知识问答助手，
              你将使用检索到的上下文来回答问题。如果你不知道答案，就说你没有找到答案。 "
              "\n\n"
              "{context}"
        """

qa_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", qa_system_prompt),
        ("placeholder", "{chat_history}"),
        ("human", "{input}"),
    ]
)

normal_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "你是一个帮助人们解答各种问题的助手。"),
        ("placeholder", "{chat_history}"),
        ("human", "{input}"),
    ]
)

def streaming_parse(chunks: Iterable[AIMessageChunk]):
    for chunk in chunks:
        yield AddableDict({'answer': chunk.content})

class CombineClient(MyKnowledge):
    """
    负责和大模型进行交互，并支持聊天历史记录；负责和知识库进行交互
    """
    def __init__(self):
        self._session_history: Dict[str, ChatMessageHistory] = {}

    def _get_session_history(self, session_id: str,db: Session) -> ChatMessageHistory:
        """
        获取指定会话 ID 的聊天历史记录
        :param session_id: 会话 ID
        :return: 会话历史记录
        """
        if session_id not in self._session_history:
            """获取或创建会话历史（数据库持久化）"""
            history = ChatMessageHistory()
            messages = db.query(ChatMessage).filter(ChatMessage.session_id == session_id).order_by(ChatMessage.id).all()
            for message in messages:
                if message.role == 'human':
                    history.add_user_message(message.content)
                elif message.role == 'ai':
                    history.add_ai_message(message.content)
            self._session_history[session_id] = history
        return self._session_history[session_id]

    def _save_messages_to_db(self, session_id: str, input_msg: str, output_msg: str, db: Session):
        """保存消息到数据库"""
        # 保存用户消息
        user_msg = ChatMessage(session_id=session_id, role="human", content=input_msg)
        db.add(user_msg)

        # 保存 AI 回复
        ai_msg = ChatMessage(session_id=session_id, role="ai", content=output_msg)
        db.add(ai_msg)

        db.commit()

    def get_chain_by_knowledge_base_id(self, knowledge_base_id,db, model, max_length, temperature,session_id):
        """
        根据具体的对话场景，返回一个链
        :param knowledge_base_id: 用户选择的知识库ID
        :param db: 数据库连接
        :param model: 选择的model
        :param max_length: 模型参数，最大文本长度
        :param temperature: 模型参数，温度
        :return: 一个可以处理会话历史的链
        """
        def get_history():
            return self._get_session_history(session_id, db)
        retriever = None
        logger.info(f"knowledge_base_id: {knowledge_base_id}")
        if knowledge_base_id:
            retriever = self.get_retrievers_by_knowledge_base_id(knowledge_base_id,db)
            logger.debug(f"[{knowledge_base_id}]检索器为: {retriever}")

        chat = get_lc_model_client(model=model, max_tokens=max_length, temperature=temperature)

        if retriever:
            # 创建一个问答链
            question_answer_chain = create_stuff_documents_chain(chat, qa_prompt)
            # 创建一个检索增强生成链（RAG），将检索器和问答链结合，使得模型在生成回答时可以参考检索到的内容。
            rag_chain = create_retrieval_chain(retriever, question_answer_chain)
            logger.info(f"产生一个RAG链......")
            logger.debug(f"rag_chain: {rag_chain}")
        else:
            # 如果没有检索器，则采用普通的提示（prompt），通过聊天和流式解析来生成回答。
            rag_chain = normal_prompt | chat | streaming_parse
            logger.info(f"产生一个普通问答链......")
            logger.debug(f"normal_chain: {rag_chain}")

        # 创建对话历史链
        chain_with_history = RunnableWithMessageHistory(
            rag_chain,
            get_history,
            input_messages_key="input",
            history_messages_key="chat_history",
            output_messages_key="answer",
        )
        ''' 需要注意：output_messages_key，如果是无知识库的情况下是从AIMessageChunk的Content取，
                    知识库是返回 AddableDict('answer') '''
        logger.debug(f"当前的处理链: {chain_with_history}")
        return chain_with_history

    def invoke(self, question, knowledge_base_id,db,session_id, model=ALI_TONGYI_MAX_MODEL, max_length=256, temperature=1):
        if not session_id:
            raise HTTPException(status_code=400, detail="会话ID不能为空")
            # session_id = str(uuid.uuid4().hex[:8])  # 生成临时会话ID
        chain = self.get_chain_by_knowledge_base_id(knowledge_base_id, db, model, max_length, temperature, session_id)
        result = chain.invoke(
            {"input": question},
            {"configurable": {"session_id": session_id}},
        )

        # 保存到数据库
        self._save_messages_to_db(session_id, question, result['answer'], db)

        return {"session_id": session_id, **result}
        # return self.get_chain_by_knowledge_base_id(knowledge_base_id,db, model, max_length, temperature).invoke(
        #     {"input": question},
        #     {"configurable": {"session_id": session_id}},
        # )

    def stream(self, question, knowledge_base_id,db,session_id, model=ALI_TONGYI_MAX_MODEL, max_length=256, temperature=1):
        if not session_id:
            raise HTTPException(status_code=400, detail="会话ID不能为空")
        chain = self.get_chain_by_knowledge_base_id(knowledge_base_id, db, model, max_length, temperature, session_id)
        result = chain.stream(
            {"input": question},
            {"configurable": {"session_id": session_id}},
        )
        # 保存到数据库
        self._save_messages_to_db(session_id, question, result['answer'], db)
        return {"session_id": session_id, **result}
        # return self.get_chain_by_knowledge_base_id(knowledge_base_id,db, model, max_length, temperature).stream(
        #     {"input": question},
        #     {"configurable": {"session_id": session_id}},
        # )

    def clear_session_history(self, session_id: str):
        """清理指定会话的内存历史"""
        if session_id in self._session_history:
            self._session_history[session_id].clear()
            del self._session_history[session_id]
            logger.info(f"已清理内存历史: {session_id}")

    def clear_all_histories(self):
        """清理所有会话历史（慎用）"""
        for session_id in self._session_history.keys():
            self._session_history[session_id].clear()
            del self._session_history[session_id]
        logger.info("已清理所有内存历史")