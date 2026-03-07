from langchain_community.document_loaders.csv_loader import CSVLoader
from langchain_community.document_loaders.text import TextLoader
from langchain_community.document_loaders.word_document import UnstructuredWordDocumentLoader
from langchain_community.document_loaders.pdf import PyPDFLoader
from langchain_community.document_loaders.markdown import UnstructuredMarkdownLoader

from langchain_core.document_loaders.base import BaseLoader
from langchain_text_splitters.character import RecursiveCharacterTextSplitter
from unstructured.file_utils.filetype import FileType, detect_filetype
from loguru import logger

class MyCustomLoader(BaseLoader):
    """
    文档加载和分割模块
    """
    # 支持加载的文件类型
    file_type = {
        FileType.CSV: (CSVLoader, {'autodetect_encoding': True}),
        FileType.TXT: (TextLoader, {'autodetect_encoding': True}),
        FileType.DOC: (UnstructuredWordDocumentLoader, {}),
        FileType.DOCX: (UnstructuredWordDocumentLoader, {}),
        FileType.PDF: (PyPDFLoader, {}),
        FileType.MD: (UnstructuredMarkdownLoader, {})
    }

    # 初始化方法，设置文档加载器和文本分割器
    def __init__(self, file_path: str):
        loader_class, params = self.file_type[detect_filetype(file_path)]
        logger.info(f"本文档[{file_path}]需使用文档加载器: {loader_class}")
        # params 是一个字典，用于存放初始化 loader_class 时所需的额外参数
        # 例如 CSVLoader 需要 autodetect_encoding=True，这些参数通过 **params 解包传入
        self.loader: BaseLoader = loader_class(file_path, **params)
        self.text_splitter = RecursiveCharacterTextSplitter(
            separators=["\n\n", "\n", " ", ""],
            chunk_size=500,
            chunk_overlap=200,
            length_function=len,
        )

    def lazy_load(self):
        # 文档的切分加载
        docs = self.loader.load()
        split_docs = self.text_splitter.split_documents(docs)
        return split_docs

    def load(self):
        # 加载
        return self.lazy_load()
