from typing import Iterable
from langchain_classic.chains.combine_documents.stuff import create_stuff_documents_chain
from langchain_classic.chains.retrieval import create_retrieval_chain
from langchain_core.messages.ai import AIMessageChunk
from langchain_core.prompts.chat import ChatPromptTemplate
from langchain_core.runnables.utils import AddableDict
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from loguru import logger

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
    __chat_history = ChatMessageHistory()

    def get_chain(self, collection, model, max_length, temperature):
        """
        根据具体的对话场景，返回一个链
        :param collection: 用户选择的知识库
        :param model: 选择的model
        :param max_length: 模型参数，最大文本长度
        :param temperature: 模型参数，温度
        :return: 一个可以处理会话历史的链
        """
        retriever = None
        logger.info(f"collection: {collection}")
        if collection:
            retriever = self.get_retrievers(collection)
            logger.debug(f"[{collection}]检索器为: {retriever}")

        # 只保留3个记录
        logger.info(f"len: {self.__chat_history.messages}####:{len(self.__chat_history.messages)}")
        if len(self.__chat_history.messages) >= 6:
            self.__chat_history.messages = self.__chat_history.messages[-6:]
            logger.info(f"self.__chat_history.messages: {self.__chat_history.messages}")

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
            lambda session_id: self.__chat_history,
            input_messages_key="input",
            history_messages_key="chat_history",
            output_messages_key="answer",
        )
        ''' 需要注意：output_messages_key，如果是无知识库的情况下是从AIMessageChunk的Content取，
                    知识库是返回 AddableDict('answer') '''
        logger.debug(f"当前的处理链: {chain_with_history}")
        return chain_with_history

    def invoke(self, question, collection, model=ALI_TONGYI_MAX_MODEL, max_length=256, temperature=1):
        return self.get_chain(collection, model, max_length, temperature).invoke(
            {"input": question},
            {"configurable": {"session_id": "unused"}},
        )

    def stream(self, question, collection, model=ALI_TONGYI_MAX_MODEL, max_length=256, temperature=1):
        return self.get_chain(collection, model, max_length, temperature).stream(
            {"input": question},
            {"configurable": {"session_id": "unused"}},
        )

    def clear_history(self) -> None:
        self.__chat_history.clear()

    def get_history_message(self):
        return self.__chat_history.messages