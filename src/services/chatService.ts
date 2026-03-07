import { ChatOpenAI } from "@langchain/openai";
import { MessagesPlaceholder, ChatPromptTemplate } from "@langchain/core/prompts";
import { RunnableWithMessageHistory } from "@langchain/core/runnables";
import { InMemoryChatMessageHistory } from "@langchain/core/chat_history";
import type { ChatServiceConfig } from '@/types/chat';

class ChatService {
  private model: ChatOpenAI;
  private withMessageHistory: RunnableWithMessageHistory<Record<string, any>, string>;
  private store = new Map<string, InMemoryChatMessageHistory>();

  constructor(config?: Partial<ChatServiceConfig>) {
    const apiKey = config?.apiKey || import.meta.env.VITE_API_KEY;
    if (!apiKey) {
      throw new Error('API key is required');
    }

    this.model = new ChatOpenAI({
      model: config?.model || "qwen-flash",
      temperature: config?.temperature || 0.7,
      configuration: {
        baseURL: config?.baseURL || "https://dashscope.aliyuncs.com/compatible-mode/v1",
      },
      apiKey,
    });

    const prompt = ChatPromptTemplate.fromMessages([
      new MessagesPlaceholder("history"),
      ["human", "{input}"],
    ]);

    const chain = prompt.pipe(this.model);

    this.withMessageHistory = new RunnableWithMessageHistory({
      runnable: chain,
      getMessageHistory: async (sessionId: string) => {
        if (this.store.has(sessionId)) {
          return this.store.get(sessionId)!;
        }
        const newHistory = new InMemoryChatMessageHistory();
        this.store.set(sessionId, newHistory);
        return newHistory;
      },
      inputMessagesKey: "input",
      historyMessagesKey: "history",
    });
  }

  async chat(sessionId: string, message: string) {
    if (!message.trim()) {
      throw new Error('消息不能为空');
      return
    }

    const formData = new FormData();
    formData.append('session_id', sessionId);
    formData.append('input_text', message);

    const response = await fetch('/python-server/chat/stream', {
      method: 'POST',
      body: formData
    });
    console.log('聊天响应:', response);
    if (!response.body) {
      throw new Error('响应体为空');
      return
    }

    return this.parseStream(response.body);
  }

  /**
   * 解析服务器返回的 SSE（Server-Sent Events）流数据
   * 逐行读取并以 JSON 格式提取 content 字段，用于前端实时展示
   * @param body - 可读流，包含服务器推送的文本数据
   * @yields 每次返回一个包含 content 字段的对象
   */
  async *parseStream(body: ReadableStream<Uint8Array>): AsyncGenerator<{ content: string }> {
    const reader = body.getReader(); // 获取流的读取器
    const decoder = new TextDecoder('utf-8'); // 用于将 Uint8Array 解码为字符串
    let buffer = ''; // 缓存未处理完的半行数据

    try {
      while (true) {
        const { done, value } = await reader.read(); // 读取下一段数据
        console.log('读取到的数据:', value);
        console.log('流是否结束:', done);
        if (done) {
          break; // 流已结束
        }
        console.log('解码后的数据:', decoder.decode(value, { stream: true }));
        // stream: true 表示本次解码的数据可能不完整（例如 UTF-8 字符被截断），
        // 需要保留未处理完的字符在内部状态中，等待后续数据继续拼接，防止乱码。
        buffer += decoder.decode(value, { stream: true });
        console.log('当前缓存:', buffer);
        const lines = buffer.split('\n'); // 按行分割
        console.log('按行分割后:', lines);
        buffer = lines.pop() || ''; // 最后一行可能不完整，留待下次处理
        console.log('处理后的缓存:', buffer);
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              console.log('原始数据:', line);
              const data = JSON.parse(line.slice(6)); // 去掉前缀后解析 JSON
              console.log('解析后的JSON:', data);
              if (data.content) {
                yield { content: data.content }; // 向外部产出有效内容
              }
            } catch (e) {
              console.error('解析JSON失败:', e); // 打印解析异常，继续后续行
            }
          }
        }
      }
    } finally {
      reader.releaseLock(); // 释放读取器锁，防止内存泄漏
    }
  }

  async getMessageHistory(sessionId: string) {
    if (!sessionId) {
      throw new Error('会话ID不能为空');
    }
    const response = await fetch(`/python-server/chat-history/${sessionId}`, {
      method: 'GET'
    });
    const data = await response.json();
    return data;
  }

  hasSession(sessionId: string) {
    return this.store.has(sessionId);
  }

  deleteSession(sessionId: string) {
    this.store.delete(sessionId);
  }
}

export const chatService = new ChatService();