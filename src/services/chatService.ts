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

  async *parseStream(body: ReadableStream<Uint8Array>): AsyncGenerator<{ content: string }> {
    const reader = body.getReader();
    const decoder = new TextDecoder('utf-8');
    let buffer = '';

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) {
          break;
        }

        buffer += decoder.decode(value);
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              if (data.content) {
                yield { content: data.content };
              }
            } catch (e) {
              console.error('解析JSON失败:', e);
            }
          }
        }
      }
    } finally {
      reader.releaseLock();
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