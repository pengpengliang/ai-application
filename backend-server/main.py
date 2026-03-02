#自动会话历史管理组件RunnableWithMessageHistory
#以及如何流式处理大模型的应答
from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.stores import InMemoryStore
from langchain_chroma import Chroma
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_classic.retrievers  import MultiVectorRetriever
import uuid
from langchain_core.documents import Document
from langchain_core.runnables import RunnableMap
from util import get_lc_ali_all_clients,validate_file,save_uploaded_file,ALLOWED_EXTENSIONS,ID_KEY
from langserve import add_routes
from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import JSONResponse,StreamingResponse
import os
import tempfile
from pathlib import Path
import shutil
import json
from datetime import datetime
from typing import List, Dict, Optional
from pydantic import BaseModel
# 允许的文件类型
# ALLOWED_EXTENSIONS = {'.txt', '.doc', '.docx'}
# MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
# client,embeddings_model = get_lc_ali_all_clients()
# vectorstore = Chroma(
#     collection_name="summaries",
#     embedding_function=embeddings_model
# )
#
# store = InMemoryStore()
#
# id_key = "doc_id"
#
# retriever = MultiVectorRetriever(
#     vectorstore=vectorstore,
#     docstore=store,
#     id_key=id_key,
# )
# temp_doc = None


# def create_adaptive_prompt():
#     return ChatPromptTemplate.from_messages([
#         # 动态系统提示词
#         ("system", """{system_role}
#
#         {role_instruction}"""),
#         # 动态用户提示词
#         ("human", """{user_prompt}"""),
#         MessagesPlaceholder(variable_name="history"),
#     ])
#
#
# # 使用示例
# adaptive_prompt = create_adaptive_prompt()
# print(adaptive_prompt)
# def get_adaptive_inputs(question):
#     if temp_doc:
#         # 有文档的情况
#         return {
#             "system_role": "你是一个文档总结专家",
#             "role_instruction": "基于提供的文档内容准确回答用户问题，如果文档中没有相关信息，请明确说明",
#             "user_prompt": "根据下面的文档回答问题:\n\n{doc}\n\n问题: {question}，如果文档里没有相关内容，则回答文档没有相关内容",
#             "question": question
#         }
#     else:
#         # 无文档的情况
#         return {
#             "system_role": "你是一个智能聊天助手",
#             "role_instruction": "请以友好和专业的方式回答用户问题",
#             "user_prompt": question,
#             "question": question
#         }


# 以链的形式
# chain = prompt_template | client | StrOutputParser()

#有一个东西，保存所有用户的所有聊天记录
# store={}

#根据每个用户自己的session_id，去获取这个用户的聊天记录
'''这里我们是将用户的会话历史保存在本机内存中，在实际业务中一般会保存到Redis缓存,
代码一般如下所示，注意代码未经测试，只做示范：
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
def get_redis_history(session_id: str) -> BaseChatMessageHistory:
    return RedisChatMessageHistory(session_id, redis_url=REDIS_URL)'''
# def get_session(session_id:str):
#     if session_id not in store:
#         store[session_id] = ChatMessageHistory()
#     return store[session_id]

# chatbot_with_his = RunnableWithMessageHistory(
#     chain,
#     get_session,
#     history_messages_key="history"
# )
#
# def load_document(file_path: str, file_extension: str) -> List[Document]:
#     """根据文件类型加载文档"""
#     try:
#         if file_extension == '.txt':
#             loader = TextLoader(file_path, encoding='utf-8')
#         elif file_extension in ['.doc', '.docx']:
#             # loader = UnstructuredWordDocumentLoader(file_path)
#             print(file_path)
#         else:
#             raise ValueError(f"不支持的文件类型: {file_extension}")
#
#         return loader.load()
#     except Exception as e:
#         raise HTTPException(status_code=400, detail=f"文档加载失败: {str(e)}")
#
# def summary_doc_by_file_path():
#
#     text_splitter = RecursiveCharacterTextSplitter(chunk_size=1024, chunk_overlap=100)
#     docs = text_splitter.split_documents(temp_doc)
#
#     doc_ids = [str(uuid.uuid4()) for _ in docs]
#     chain4 = (
#         {"doc": lambda x: x.page_content}
#         | ChatPromptTemplate.from_template("总结下面的文档：{doc}")
#         | client
#         | StrOutputParser()
#     )
#
#     summaries = chain4.batch(docs, {"max_concurrency": 5,})
#     summary_docs = [
#         Document(page_content=s, metadata={id_key: doc_ids[i]}) for i, s in enumerate(summaries)
#     ]
#     retriever.vectorstore.add_documents(summary_docs)
#     retriever.docstore.mset(list(zip(doc_ids, docs)))
#
# def query_doc_by_summary(question: str):
#     prompt =  ChatPromptTemplate.from_template("根据下面的文档回答问题:\n\n{doc}\n\n问题: {question}，如果文档里没有相关内容，则回答文档没有相关内容")
#     chain2 = RunnableMap({
#         "doc": lambda x: retriever.invoke(x["question"]),
#         "question": lambda x: x["question"]
#     }) | prompt | client | StrOutputParser()
#     answer = chain2.invoke({"question": question})
#     return answer
#
# def validate_file(file: UploadFile) -> bool:
#     """验证文件类型和大小"""
#     # 检查文件扩展名
#     file_extension = Path(file.filename).suffix.lower()
#     if file_extension not in ALLOWED_EXTENSIONS:
#         return False
#
#     # 检查文件大小（可以通过文件头信息或其他方式）
#     # 这里简化处理，实际应用中可以在上传过程中检查
#
#     return True
#
# def save_uploaded_file(file: UploadFile) -> str:
#     """保存上传的文件并返回文件路径"""
#     # 创建临时目录
#     temp_dir = tempfile.mkdtemp()
#
#     # 生成唯一文件名
#     file_extension = Path(file.filename).suffix
#     unique_filename = f"{uuid.uuid4()}{file_extension}"
#     file_path = os.path.join(temp_dir, unique_filename)
#
#     # 保存文件
#     with open(file_path, "wb") as buffer:
#         shutil.copyfileobj(file.file, buffer)
#
#     return file_path

# #从业务角度来说，每个的Session_id遵循某种算法
# config_chn = {'configurable':{'session_id':"yunfang_chinese"}}
#
# resp = chatbot_with_his.invoke(
#     {
#         "input": [HumanMessage(content="你好，我是云帆。")],
#         "language": "中文"
#     },
#     config = config_chn
# )
# print(resp)
#
# resp = chatbot_with_his.invoke(
#     {
#         "input": [HumanMessage(content="请问我的名字是什么？")],
#         "language": "中文"
#     },
#     config = config_chn
# )
#
# print(resp)
#流式处理
# for respon in chatbot_with_his.stream(
#     {
#         "input": [HumanMessage(content="请给我说5个有趣的笑话")],
#         "language": "中文"
#     },
#     config = config_chn
# ):
#     print(respon,end="-")

app = FastAPI(title="文档上传处理API", description="支持txt、doc、docx文件上传的FastAPI服务")

# 1.新会话需要一个给前端create接口 创建sessionId
# 2.创建一个给前端的传输入的接口 需要记住会话 记住文档 记住对话历史
# 3.创建一个接口给前端 根据sessionId 获取对话历史
# 4.创建一个接口给前端 获取所有会话列表
client,embeddings_model = get_lc_ali_all_clients()
# 保存单个对话的store
chat_history_store  = {}
# 保存单个对话里文档的store
doc_store = {}
# 创建一个保存所有会话的store
chat_list_store = []

def load_document(file_path: str, file_extension: str) -> List[Document]:
    """根据文件类型加载文档"""
    try:
        if file_extension == '.txt':
            loader = TextLoader(file_path, encoding='utf-8')
        elif file_extension in ['.doc', '.docx']:
            # loader = UnstructuredWordDocumentLoader(file_path)
            print(file_path)
        else:
            raise ValueError(f"不支持的文件类型: {file_extension}")

        return loader.load()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"文档加载失败: {str(e)}")

def process_document_for_session(session_id: str, file_path: str, file_extension: str):
    """为特定会话处理文档"""
    try:
        # 加载文档
        docs = load_document(file_path, file_extension)

        # 分割文档
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1024, chunk_overlap=100)
        split_docs = text_splitter.split_documents(docs)
        doc_ids = [str(uuid.uuid4()) for _ in docs]
        chain4 = (
            {"doc": lambda x: x.page_content}
            | ChatPromptTemplate.from_template("总结下面的文档：{doc}")
            | client
            | StrOutputParser()
        )
        summaries = chain4.batch(docs, {"max_concurrency": 5, })
        summary_docs = [
            Document(page_content=s, metadata={ID_KEY: doc_ids[i]}) for i, s in enumerate(summaries)
        ]
        # 创建向量存储
        vectorstore = Chroma(
            collection_name=f"session_{session_id}",
            embedding_function=embeddings_model
        )

        # 存储文档内容供后续检索使用
        doc_store[session_id] = {
            "summary_docs": summary_docs,
            "doc_ids": doc_ids,
            "documents": split_docs,
            "vectorstore": vectorstore,
            "processed": True,
            "file_path": file_path
        }

        return len(split_docs)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文档处理失败: {str(e)}")

def get_session(session_id:str):
    if session_id not in chat_history_store:
        chat_history_store[session_id] = ChatMessageHistory()
    return chat_history_store[session_id]

@app.post("/chat_session/create")
def create_session():
    session_id = str(uuid.uuid4())
    return {"session_id": session_id}


@app.post("/chat/stream")
async def stream_chat_endpoint(
        session_id: str = Form(...),
        input_text: str = Form(...)
):
    """
    流式聊天接口 - 实时返回AI回复

    参数:
    - session_id: 会话ID (FormData)
    - input_text: 用户输入内容 (FormData)
    """
    try:
        # 检查会话是否存在
        # if session_id not in chat_history_store:
        #     raise HTTPException(status_code=404, detail="会话不存在")

        # 检查是否有文档
        has_document = session_id in doc_store and doc_store[session_id].get("processed", False)

        async def generate_stream():
            try:
                if not has_document:
                    # 普通聊天模式 - 流式处理
                    prompt_template = ChatPromptTemplate.from_messages([
                        SystemMessagePromptTemplate.from_template(
                            "你是一个智能聊天助手，请以友好和专业的方式回答用户问题"),
                        MessagesPlaceholder(variable_name="history"),
                        ("human", "{input}"),
                    ])

                    chain = prompt_template | client | StrOutputParser()
                    chatbot_with_his = RunnableWithMessageHistory(
                        chain,
                        get_session,
                        history_messages_key="history"
                    )

                    # 流式处理并返回JSON
                    async for chunk in chatbot_with_his.astream(
                            {"input": input_text},
                            config={'configurable': {'session_id': session_id}}
                    ):
                        # 使用ensure_ascii=False避免Unicode转义
                        response_data = {
                            "content": chunk,
                            "mode": "chat"
                        }
                        yield f"data: {json.dumps(response_data, ensure_ascii=False)}\n\n"

                else:
                    # 文档问答模式
                    summary_docs = doc_store[session_id]["summary_docs"]
                    docs = doc_store[session_id]["documents"]
                    doc_ids = doc_store[session_id]["doc_ids"]
                    vectorstore = doc_store[session_id]["vectorstore"]
                    store = InMemoryStore()
                    ID_KEY = "doc_id"

                    retriever = MultiVectorRetriever(
                        vectorstore=vectorstore,
                        docstore=store,
                        id_key=ID_KEY,
                    )

                    retriever.vectorstore.add_documents(summary_docs)
                    retriever.docstore.mset(list(zip(doc_ids, docs)))

                    prompt_template = ChatPromptTemplate.from_messages([
                        SystemMessagePromptTemplate.from_template(
                            "你是一个文档总结专家，基于提供的文档内容准确回答用户问题，如果文档中没有相关信息，请明确说明"),
                        ("human",
                         "根据下面的文档回答问题:\n\n{doc}\n\n问题: {question}，如果文档里没有相关内容，则回答文档没有相关内容"),
                    ])
                    chain = RunnableMap({
                        "doc": lambda x: retriever.invoke(x["input"]),
                        "question": lambda x: x["input"]
                    }) | prompt_template | client | StrOutputParser()
                    chatbot_with_his = RunnableWithMessageHistory(
                        chain,
                        get_session,
                        history_messages_key="history"
                    )
                    print(chatbot_with_his, 'chatbot_with_his')

                    async for chunk in chatbot_with_his.astream(
                            {"input": input_text},
                            config={'configurable': {'session_id': session_id}}
                    ):
                        # 使用ensure_ascii=False避免Unicode转义
                        print(chunk, "chunk")
                        response_data = {
                            "content": chunk,
                            "mode": "document_qa"
                        }
                        yield f"data: {json.dumps(response_data, ensure_ascii=False)}\n\n"

                    # 对于文档问答，由于涉及检索，可能需要先处理完再流式返回
                    # 这里简化处理，一次性返回结果
                    # resp = chatbot_with_his.invoke(
                    #     {"input": input_text},
                    #     config={'configurable': {'session_id': session_id}}
                    # )
                    # print(resp, "resp")
                    # response_data = {
                    #     "content": resp,
                    #     "mode": "document_qa"
                    # }
                    # yield f"data: {json.dumps(response_data, ensure_ascii=False)}\n\n"


            except Exception as e:
                print(str(e))
                error_data = {
                    "error": str(e),
                    "mode": "error"
                }
                yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"

        # 返回SSE流
        return StreamingResponse(
            generate_stream(),
            media_type="text/event-stream; charset=utf-8",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Content-Type": "text/event-stream; charset=utf-8"
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理聊天请求时出错: {str(e)}")

@app.post("/upload/")
async def upload_file(
        file: UploadFile = File(...),
        session_id: str = Form(...),
        process_method: str = Form(...)
):
    """
    上传文件接口

    参数:
    - file: 上传的文件 (txt/doc/docx格式)
    - process_method: 处理方法 ("basic" 或其他自定义方法)
    """

    # 验证文件
    if not validate_file(file):
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型。仅支持: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    try:
        # 保存文件
        file_path = save_uploaded_file(file)
        file_extension = Path(file.filename).suffix.lower()
        doc_count = process_document_for_session(session_id, file_path, file_extension)

        result = {
            "filename": file.filename,
            "file_size": os.path.getsize(file_path),
            "message": "文档上传并处理成功",
            "doc_count": doc_count
        }

        # 清理临时文件
        # shutil.rmtree(os.path.dirname(file_path))

        return JSONResponse(content=result)

    except Exception as e:
        # 如果出现错误，清理临时文件
        if 'file_path' in locals():
            try:
                shutil.rmtree(os.path.dirname(file_path))
            except:
                pass
        raise HTTPException(status_code=500, detail=f"处理文件时出错: {str(e)}")


class MessageItem(BaseModel):
    content: str
    type: str  # human, ai, system
    timestamp: Optional[str] = None


class ChatHistoryResponse(BaseModel):
    session_id: str
    message_count: int
    has_document: bool
    messages: List[MessageItem]
    created_at: Optional[str] = None


@app.get("/chat-history/{session_id}", response_model=ChatHistoryResponse)
async def get_chat_history(session_id: str):
    """获取指定会话的聊天记录"""
    history = get_session(session_id)
    if history is None:
        raise HTTPException(status_code=404, detail="会话不存在")

    # 格式化消息
    messages = []
    for msg in history.messages:
        message_item = MessageItem(
            content=msg.content,
            type=msg.type,
            timestamp=getattr(msg, 'additional_kwargs', {}).get('timestamp',datetime.now().isoformat())
        )
        messages.append(message_item)

    # 检查文档状态
    has_document = session_id in doc_store and doc_store[session_id].get("processed", False)

    return ChatHistoryResponse(
        session_id=session_id,
        message_count=len(messages),
        has_document=has_document,
        messages=messages,
        created_at=getattr(history, 'created_at', datetime.now().isoformat())
    )

@app.get("/test-chat")
async def test_chat():
    """测试聊天接口"""
    id = create_session()
    session_id = id["session_id"]
    res = stream_chat_endpoint(session_id, "你好,你是谁")
    print(chat_history_store)
    current_history = get_session(session_id)
    print(f"当前历史条数: {len(current_history.messages)}")
    for m in current_history.messages:
        print(f"- {m.type}: {m.content}")
    return JSONResponse(content={"status": "healthy","res": res,"session_id":session_id})



@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)