from loguru import logger
# from sqlalchemy.orm.collections import collection
# 从llm模块中导入MyLLM类，这是自定义的大型语言模型接口
from combine_client import CombineClient
from logger import setup_logger
from util import validate_file,ALLOWED_EXTENSIONS,ALI_TONGYI_MAX_MODEL, ALI_TONGYI_DEEPSEEK_R1, ALI_TONGYI_DEEPSEEK_V3
from fastapi import FastAPI, File, UploadFile, HTTPException,Depends, Form
from fastapi.responses import JSONResponse,StreamingResponse
from sqlalchemy.orm import Session
from database import get_db, engine, Base
from models import KnowledgeBase
import uuid

print(Base,'BASE')
# 自动创建表（如果第一步手动建了表，这行可以注释掉，但留着也没坏处，作为双重保险）
Base.metadata.create_all(bind=engine)
app = FastAPI(title="知识库管理API", description="支持知识库增删改查服务")
# 实例化MyLLM类，用于后续的模型调用和处理
llm = CombineClient()
setup_logger()

@app.get("/test-chat")
async def test_chat():
    """测试聊天接口"""
    collections = llm.load_knowledge()
    logger.info(f"加载知识库: {collections}")
    res = llm.invoke('DeepSeek开源大模型DeepSeek-V2的关键开发者是谁？',collections[0],ALI_TONGYI_MAX_MODEL,256,1)
    return JSONResponse(content={"status": "healthy","res": res['answer']})

@app.post("/api/v1/knowledge-base/create")
def create_knowledge_base(name: str, description: str = "", db: Session = Depends(get_db)):
    # 1. 生成 Chroma 集合名 (简单起见用 UUID)
    collection_name = f"kb_{uuid.uuid4().hex}"

    # 2. 创建 ORM 对象
    new_kb = KnowledgeBase(
        name=name,
        description=description,
        chroma_collection_name=collection_name
    )
    logger.info(f"创建知识库: {new_kb.id} {new_kb.name} {new_kb.description} {new_kb.chroma_collection_name}")
    # 3. 添加到数据库
    db.add(new_kb)
    db.commit()
    db.refresh(new_kb)

    # client = chromadb.Client()
    # client.create_collection(name=collection_name)

    return {"id": new_kb.id, "name": new_kb.name, "status": "created"}

@app.post("/api/v1/knowledge-base/delete")
def delete_knowledge_base(knowledge_base_id: int, db: Session = Depends(get_db)):
    """
    删除指定知识库, 并删除该知识库下所有文件, 包括索引文件, 并从内存中移除
    """
    try:
        status = llm.delete_knowledge_base(knowledge_base_id, db)
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除知识库失败: {str(e)}")

@app.post("/api/v1/knowledge-base/update")
def update_knowledge_base(
    knowledge_base_id: int,
    name: str = Form(...),
    description: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    更新指定知识库的信息
    """
    kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == knowledge_base_id).first()
    if not kb:
        raise HTTPException(status_code=404, detail="知识库不存在")
    kb.name = name
    kb.description = description
    db.commit()
    db.refresh(kb)
    return {"status": "updated", "knowledge_base": kb}

@app.get("/api/v1/knowledge-base/list")
def list_knowledge_bases(db: Session = Depends(get_db)):
    """
    获取所有知识库
    """
    kbs = db.query(KnowledgeBase).all()
    return {"knowledge_bases": kbs}

@app.get("/api/v1/knowledge-base/{knowledge_base_id}")
def get_knowledge_base(knowledge_base_id: int, db: Session = Depends(get_db)):
    """
    获取指定知识库的详细信息
    """
    kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == knowledge_base_id).first()
    if not kb:
        raise HTTPException(status_code=404, detail="知识库不存在")
    return kb

@app.post("/api/v1/knowledge-base/upload-file")
async def upload_file_to_knowledge_base(
    knowledge_base_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    将文件上传到指定的知识库 (knowledge_base_id)
    """
    # 1. 获取知识库信息
    logger.info(f"上传文件到知识库: {knowledge_base_id} {db.query(KnowledgeBase).all()}")
    kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == knowledge_base_id).first()
    logger.info(f"上传文件到知识库: {knowledge_base_id} {kb}")
    if not kb:
        raise HTTPException(status_code=404, detail="知识库不存在")
    try:
        result = llm.upload_file_to_knowledge_base(file, knowledge_base_id,db)
        return {"status": "success", "data": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"上传失败详情：{e}")
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")

@app.post("/api/v1/knowledge-base/delete-file")
def delete_file_from_knowledge_base(
    knowledge_base_id: int,
    file_id: int,
    db: Session = Depends(get_db)
):
    """
    删除知识库中指定文件 ID 的文件及其索引
    """
    try:
        kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == knowledge_base_id).first()
        if not kb:
            raise HTTPException(status_code=404, detail="知识库不存在")

        result = llm.delete_file(knowledge_base_id, file_id, db)
        return result
    except Exception as e:
        logger.error(f"删除文件失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")

@app.post("/api/v1/knowledge-base/chat")
async def chat_with_knowledge_base(
    knowledge_base_id: int = Form(...),
    query: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    与指定知识库 (knowledge_base_id) 进行聊天
    """
    # 1. 获取知识库信息
    kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == knowledge_base_id).first()
    if not kb:
        raise HTTPException(status_code=404, detail="知识库不存在")
    try:
        result = llm.invoke(query, knowledge_base_id, db, ALI_TONGYI_MAX_MODEL, 256, 1)
        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"聊天失败详情：{e}")
        raise HTTPException(status_code=500, detail=f"聊天失败: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
