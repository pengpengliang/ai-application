from loguru import logger
# from sqlalchemy.orm.collections import collection
# 从llm模块中导入MyLLM类，这是自定义的大型语言模型接口
from combine_client import CombineClient
from logger import setup_logger
from util import validate_file,ALLOWED_EXTENSIONS,ALI_TONGYI_MAX_MODEL, ALI_TONGYI_DEEPSEEK_R1, ALI_TONGYI_DEEPSEEK_V3
from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import JSONResponse,StreamingResponse
app = FastAPI(title="知识库管理API", description="支持知识库增删改查服务")
# 实例化MyLLM类，用于后续的模型调用和处理
llm = CombineClient()
setup_logger()

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    # 验证文件
    if not validate_file(file):
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型。仅支持: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    try:
        result = llm.upload_knowledge(file)

        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"文件上传失败: {str(e)}"
        )


@app.get("/test-load-knowledge")
async def test_load_knowledge():
    """测试加载知识库接口"""
    try:
        res = llm.load_knowledge()
        return JSONResponse(content={"status": "healthy","res": res})
    except Exception as e:
        return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)


@app.get("/test-chat")
async def test_chat():
    """测试聊天接口"""
    collections = llm.load_knowledge()
    res = llm.invoke('DeepSeek开源大模型DeepSeek-V2的关键开发者是谁？',collections[0],ALI_TONGYI_MAX_MODEL,256,1)
    return JSONResponse(content={"status": "healthy","res": res['answer']})



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
