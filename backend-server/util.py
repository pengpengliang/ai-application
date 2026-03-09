ALI_TONGYI_API_KEY_OS_VAR_NAME = "DASHSCOPE_API_KEY"
ALI_TONGYI_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
ALI_TONGYI_MAX_MODEL = "qwen-max-latest"
ALI_TONGYI_DEEPSEEK_R1 = "deepseek-r1"
ALI_TONGYI_DEEPSEEK_V3 = "deepseek-v3"
ALI_TONGYI_REASONER_MODEL = "qwq-plus"
ALI_TONGYI_EMBEDDING_MODEL = "text-embedding-v3"
ALI_TONGYI_EMBEDDING_MODEL_V4 = "text-embedding-v4"
ALI_TONGYI_RERANK_MODEL = "gte-rerank-v2"
TENCENT_HUNYUAN_URL = "https://api.hunyuan.cloud.tencent.com/v1"
ALI_TONGYI_3 = "qwen3-235b-a22b"
ALLOWED_EXTENSIONS = {'.txt', '.doc', '.docx'}
ID_KEY = "doc_id"
import os
from langchain_openai import ChatOpenAI
import inspect
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_community.document_compressors.dashscope_rerank import DashScopeRerank
from fastapi import UploadFile
from pathlib import Path
import tempfile
import uuid
import shutil

DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': 'mysql123',
    'database': 'rag_knowledge_db'
}

def get_lc_model_client(api_key=os.getenv(ALI_TONGYI_API_KEY_OS_VAR_NAME), base_url=ALI_TONGYI_URL
                        , model=ALI_TONGYI_MAX_MODEL, temperature=0.7, max_tokens=8000,verbose=False, debug=False):
    """
        通过LangChain获得指定平台和模型的客户端，设定的默认平台和模型为阿里百炼qwen-max-latest
        也可以通过传入api_key，base_url，model三个参数来覆盖默认值
        verbose，debug两个参数，分别控制是否输出调试信息，是否输出详细调试信息，默认不打印
    """
    function_name = inspect.currentframe().f_code.co_name
    if (verbose):
        print(f"{function_name}-平台：{base_url},模型：{model},温度：{temperature}")
    if (debug):
        print(f"{function_name}-平台：{base_url},模型：{model},温度：{temperature},key：{api_key}")
    return ChatOpenAI(api_key=api_key, base_url=base_url, model=model, temperature=temperature,max_tokens=max_tokens)

def get_ali_embeddings():
    """通过LangChain获得一个阿里通义千问嵌入模型的实例"""
    return DashScopeEmbeddings(
        model=ALI_TONGYI_EMBEDDING_MODEL_V4, dashscope_api_key=os.getenv(ALI_TONGYI_API_KEY_OS_VAR_NAME)
    )

def get_ali_rerank(top_n=10):
    '''
    通过LangChain获得一个阿里重排序模型的实例
    :return: 阿里通义千问嵌入模型的实例
    '''
    return DashScopeRerank(
        model=ALI_TONGYI_RERANK_MODEL, dashscope_api_key=os.getenv(ALI_TONGYI_API_KEY_OS_VAR_NAME),
        top_n=top_n
)


def get_lc_ali_embeddings():
    '''
    通过LangChain获得一个阿里通义千问嵌入模型的实例
    :return: 阿里通义千问嵌入模型的实例，目前为text-embedding-v4
    '''
    return DashScopeEmbeddings(
        model=ALI_TONGYI_EMBEDDING_MODEL_V4, dashscope_api_key=os.getenv(ALI_TONGYI_API_KEY_OS_VAR_NAME)
)

def get_lc_o_model_client(api_key=os.getenv(ALI_TONGYI_API_KEY_OS_VAR_NAME), base_url=TENCENT_HUNYUAN_URL
                          , model=ALI_TONGYI_3, temperature = 0.7, verbose=False, debug=False):
    '''
    以OpenAI兼容的方式，通过LangChain获得指定平台和模型的客户端
    可以通过传入api_key，base_url，model，temperature四个参数来覆盖默认值
    verbose，debug两个参数，分别控制是否输出调试信息，是否输出详细调试信息，默认不打印
    :return: 指定平台和模型的客户端，默认平台和模型为阿里百炼qwen3-235b-a22b，温度=0.7
    '''
    function_name = inspect.currentframe().f_code.co_name
    if(verbose):
        print(f"{function_name}-平台：{base_url},模型：{model},温度：{temperature}")
    if(debug):
        print(f"{function_name}-平台：{base_url},模型：{model},温度：{temperature},key：{api_key}")
    return ChatOpenAI(api_key=api_key, base_url=base_url,model=model,temperature=temperature)

def get_lc_o_ali_model_client(model=ALI_TONGYI_MAX_MODEL, temperature = 0.7, verbose=False, debug=False):
    '''
    以OpenAI兼容的方式，通过LangChain获得阿里大模型的客户端
    可以通过传入model，temperature 两个参数来覆盖默认值
    verbose，debug两个参数，分别控制是否输出调试信息，是否输出详细调试信息，默认不打印
    :return: 指定平台和模型的客户端，默认模型为阿里百炼里的qwen-max-latest，温度=0.7
    '''
    return get_lc_o_model_client(api_key=os.getenv(ALI_TONGYI_API_KEY_OS_VAR_NAME), base_url=ALI_TONGYI_URL
                                 , model=model, temperature =temperature, verbose=verbose, debug=debug)

def get_lc_ali_all_clients():
    '''
    以OpenAI兼容的方式，同时产生阿里大模型客户端和嵌入模型的客户端
    :return: 阿里大模型客户端和嵌入模型的客户端
    '''
    return get_lc_o_ali_model_client(),get_lc_ali_embeddings()

def validate_file(file: UploadFile) -> bool:
    """验证文件类型和大小"""
    # 检查文件扩展名
    file_extension = Path(file.filename).suffix.lower()
    if file_extension not in ALLOWED_EXTENSIONS:
        return False

    # 检查文件大小（可以通过文件头信息或其他方式）
    # 这里简化处理，实际应用中可以在上传过程中检查

    return True

def save_uploaded_file(file: UploadFile) -> str:
    """保存上传的文件并返回文件路径"""
    # 创建临时目录
    temp_dir = tempfile.mkdtemp()

    # 生成唯一文件名
    file_extension = Path(file.filename).suffix
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(temp_dir, unique_filename)

    # 保存文件
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return file_path
