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
      throw new Error('Message cannot be empty');
    }
    // const response = await fetch('/api/parseDoc', {
    //   method: 'POST',
    //   headers: {
    //     'Content-Type': 'application/json',
    //   },
    //   body: JSON.stringify({
    //     input: message
    //   })
    // });
    // return await response.json();
    const config = { configurable: { sessionId } };
    const response = await this.withMessageHistory.stream({ input: message }, config);
    return response;
    // const formData = new FormData();
    // formData.append('question', message);
    // const response = await fetch('/python-server/summary-doc/', {
    //   method: 'POST',
    //   body: formData
    // });
    // return await response.json();
  }

  async getMessageHistory(sessionId: string) {
    if (!sessionId) {
      throw new Error('Session ID is required');
    }

    const history = await this.withMessageHistory.getMessageHistory(sessionId);
    return history;
  }

  hasSession(sessionId: string) {
    return this.store.has(sessionId);
  }

  deleteSession(sessionId: string) {
    this.store.delete(sessionId);
  }
}

export const chatService = new ChatService();