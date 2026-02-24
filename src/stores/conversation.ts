import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { ConversationItem } from 'vue-element-plus-x/types/Conversations';
import { chatService } from '@/services/chatService';

interface ConversationState {
  conversationList: ConversationItem<{ id: string; label: string }>[];
  currentSessionId: string;
  isNewSession: boolean;
}

// 获取当前日期，格式为 yyyy-mm-dd
function getCurrentDate() {
  const today = new Date();
  const year = today.getFullYear();
  const month = String(today.getMonth() + 1).padStart(2, '0');
  const day = String(today.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

export const useConversationStore = defineStore('conversation', () => {
  const state = ref<ConversationState>({
    conversationList: [],
    currentSessionId: '',
    isNewSession: false
  });

  //请求一个接口，获取一个新的sessionId
  // async function createSessionId() {
  //   const response = await fetch('/python-server/chat_session/create', {
  //     method: 'POST',
  //     headers: {
  //       'Content-Type': 'application/json',
  //     }
  //   });
  //   const data = await response.json();
  //   console.log('创建会话响应:', data);
  //   state.value.currentSessionId = data.sessionId;
  // }

  const currentConversation = computed(() => {
    return state.value.conversationList.find(
      item => item.id === state.value.currentSessionId
    );
  });

  function changeIsNewSession(value: boolean) {
    state.value.isNewSession = value;
  }

  function createSessionId() {
    state.value.currentSessionId = `${new Date().getTime()}`;
  }

  function changeSessionId(sessionId: string) {
    state.value.currentSessionId = sessionId;
  }

  function addConversation(content: string) {
    state.value.conversationList.push({
      id: state.value.currentSessionId,
      label: content,
      group: getCurrentDate(),
    });
  }

  function switchConversation(sessionId: string) {
    changeIsNewSession(false);
    state.value.currentSessionId = sessionId;
  }

  function deleteConversation(sessionId: string) {
    const index = state.value.conversationList.findIndex(item => item.id === sessionId);
    if (index !== -1) {
      state.value.conversationList.splice(index, 1);
      chatService.deleteSession(sessionId);

      if (state.value.currentSessionId === sessionId) {
        state.value.currentSessionId = state.value.conversationList.length > 0
          ? state.value.conversationList[0].id
          : '';
      }
    }
  }

  function renameConversation(sessionId: string, newLabel: string) {
    const conversation = state.value.conversationList.find(item => item.id === sessionId);
    if (conversation) {
      conversation.label = newLabel;
    }
  }

  return {
    conversationList: computed(() => state.value.conversationList),
    currentSessionId: computed(() => state.value.currentSessionId),
    isNewSession: computed(() => state.value.isNewSession),
    currentConversation,
    changeIsNewSession,
    createSessionId,
    changeSessionId,
    addConversation,
    switchConversation,
    deleteConversation,
    renameConversation
  };
});
