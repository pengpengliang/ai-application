<script setup lang="ts">
import type { ConversationItem,ConversationMenuCommand } from 'vue-element-plus-x/types/Conversations';
import { markRaw, ref, shallowRef } from 'vue';
import { Conversations } from 'vue-element-plus-x';
import { ElMessage, ElButton } from 'element-plus';
import { Plus } from '@element-plus/icons-vue';
import { useConversationStore } from '@/stores/conversation';

const conversationStore = useConversationStore();

const emits = defineEmits(['clearList']);

function handleMenuCommand(
  command: ConversationMenuCommand,
  item: ConversationItem
) {
  if (command === 'delete') {
    fetch(`/python-server/clear-history/${item.id}`,{
      method: 'POST'
    }).then(res => res.json()).then(data => {
      if (data.message === '聊天记录已清除') {
        conversationStore.deleteConversation(item.id as string);
        ElMessage.success('删除成功');
      }
    }).catch(err => {
      ElMessage.error('删除失败');
    })
  }
  if (command === 'rename') {
    const newLabel = prompt('请输入新的会话名称:', item.label);
    if (newLabel) {
      conversationStore.renameConversation(item.id as string, newLabel);
      ElMessage.success('重命名成功');
    }
  }
}

function handleSessionSelect(item: ConversationItem<{ id: string; label: string }>) {
  if (conversationStore.currentSessionId) {
    conversationStore.switchConversation(item.id as string);
  }
}
</script>

<template>
  <div style="height: 100%;">
    <div style="height: 32px; display: flex; align-items: center; justify-content: center;">
      <el-button type="primary" :icon="Plus" @click="emits('clearList'); conversationStore.changeIsNewSession(true)">添加新会话</el-button>
    </div>
    <div style="display: flex; flex-direction: column; gap: 12px; height: calc(100% - 32px);">
      <Conversations
        :active="conversationStore.currentSessionId"
        :items="conversationStore.conversationList"
        groupable
        :label-max-width="200"
        :show-tooltip="false"
        row-key="id"
        show-to-top-btn
        show-built-in-menu
        @menu-command="handleMenuCommand"
        @change="handleSessionSelect"
      />
    </div>
  </div>

</template>

<style scoped lang="less"></style>