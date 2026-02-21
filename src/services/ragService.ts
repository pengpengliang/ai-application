// import { ChatOpenAI } from "@langchain/openai";
// import {
//   MessagesPlaceholder,
//   ChatPromptTemplate,
// } from "@langchain/core/prompts";
// // import { RunnableWithMessageHistory } from "@langchain/core/runnables";
// import { HTMLWebBaseLoader } from "@langchain/community/document_loaders/web/html";
// import { RecursiveCharacterTextSplitter } from "@langchain/textsplitters";
// import { AlibabaTongyiEmbeddings } from "@langchain/community/embeddings/alibaba_tongyi";
// import { Chroma } from "@langchain/community/vectorstores/chroma";
// import {CloseVectorNode} from "@langchain/community/vectorstores/closevector/node";
// import {HNSWLib} from "@langchain/community/vectorstores/hnswlib";
// import type { ChatServiceConfig } from "@/types/chat";
// import type { Document } from '@langchain/core/documents';
// /**
//    * 1.获得文档内容 - langchain各种loader
//    * 2.文档切片 - langchain文本切分器 切分之后是Document
//    * 3.转化成向量 - langchain嵌入模型
//    * 4.存到向量数据库 - langchain向量数据库 langchain检索器
//    * 5.根据用户输入的问题，从向量数据库中提取相关文档（根据问题的向量表示，从数据库中提取与问题最相关的文档）- langchain链
//    * 6.将提取到的文档内容作为上下文，与用户问题一起输入到模型中，生成回答 - langchain链
//    */
// export class RagService {
//   private model: ChatOpenAI;
//   private embeddings: AlibabaTongyiEmbeddings;
//   private vectorStore: HNSWLib;
//   private retriever: any;
//   private prompt = ChatPromptTemplate.fromMessages([
//     ["system", "您是问答任务的助理。使用以下的上下文来回答问题，上下文：{context}，如果上下文没有相关信息，请回答“我不确定”"],
//     ["human", "{input}"],
//   ]);
//   constructor(config?: Partial<ChatServiceConfig>) {
//     const apiKey = config?.apiKey || process.env.VITE_API_KEY;
//     if (!apiKey) {
//       throw new Error("API key is required");
//     }

//     this.model = new ChatOpenAI({
//       model: config?.model || "qwen-flash",
//       temperature: config?.temperature || 0.7,
//       configuration: {
//         baseURL:
//           config?.baseURL ||
//           "https://dashscope.aliyuncs.com/compatible-mode/v1",
//       },
//       apiKey,
//     });

//     this.embeddings = new AlibabaTongyiEmbeddings({
//       modelName: "text-embedding-v3",
//       apiKey
//     });

//     this.vectorStore = new HNSWLib(this.embeddings, {
//       space: "l2"
//     });

//     // this.vectorStore = new Chroma(this.embeddings, {
//     //   collectionName: "my_collection",
//     //   // 使用内存模式，不需要外部Chroma服务器
//     //   collectionMetadata: {
//     //     "hnsw:space": "cosine",
//     //   },
//     // });

//     // this.retriever = this.vectorStore.asRetriever({
//     //   searchType: "similarity",
//     //   k: 1,
//     // });
//   }

//   // 获得文档内容
//   async getDocContent(url: string) {
//     const loader = new HTMLWebBaseLoader(url);
//     const docs = await loader.load();
//     // console.log(docs, "docs");
//     return docs;
//   }

//   // 文档切片
//   async splitDoc(docs: Document[]) {
//     const splitter = new RecursiveCharacterTextSplitter({
//       chunkSize: 1000,
//       chunkOverlap: 100,
//     });
//     const splitDocs = await splitter.splitDocuments(docs);
//     // console.log(splitDocs, "splitDocs");
//     return splitDocs;
//   }

//   // 添加到向量数据库
//   async embedDocs(docs: Document[]) {
//     await this.vectorStore.addDocuments(docs);
//     // console.log(this.vectorStore, "vectorStore");
//   }

//   // 从向量数据库中提取相关文档
//   async getRetrieverDocs(query: string) {
//     const docs = await this.retriever.invoke(query);
//     console.log(docs, "docs");
//     return docs;
//   }

//   // 调用链
//   async invokeChain(query: string, docs: any) {
//     const chain = this.prompt.pipe(this.model);
//     const response = await chain.invoke({
//       context: docs,
//       input: query,
//     });
//     console.log(response, "response");
//     return response;
//   }

//   // 用了检索器，所以不需要再调用addDocsToVectorStore方法
//   async addDocsToVectorStore(docs: any) {
//     await this.vectorStore.addDocuments(docs);
//   }
// }

// // export const ragService = new RagService();
