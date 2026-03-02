<script setup lang="ts">
import {ref, type Ref, watch, shallowRef } from 'vue';
import { Sender, BubbleList,Attachments } from 'vue-element-plus-x';
import { ElButton,ElIcon,ElMessage, UploadProps } from 'element-plus';
import { CloseBold, Link } from '@element-plus/icons-vue';
import type {
  BubbleListItemProps,
  BubbleListProps
} from 'vue-element-plus-x/types/BubbleList';
import { useConversationStore } from '@/stores/conversation';
import { chatService } from '@/services/chatService';
import { FilesCardProps } from 'vue-element-plus-x/types/FilesCard';

type listType = BubbleListItemProps & {
  key: number;
  role: 'user' | 'ai';
};
type SelfFilesCardProps = FilesCardProps & {
  id?: number;
};
const conversationStore = useConversationStore();

const chatList: Ref<BubbleListProps<listType>['list']> = ref([]);
const senderLoading = ref(false);
const USER_AVATAR = 'https://avatars.githubusercontent.com/u/76239030?v=4';
const AI_AVATAR = 'https://cube.elemecdn.com/0/88/03b0d39583f48206768a7534e55bcpng.png';
const files = ref<SelfFilesCardProps[]>([]);
const senderValue = ref('');
const senderRef = ref();
const showHeaderFlog = ref(false);
function handleOpenHeader() {
  if (!showHeaderFlog.value) {
    senderRef.value.openHeader();
  }
  else {
    senderRef.value.closeHeader();
  }
  showHeaderFlog.value = !showHeaderFlog.value;
}

function closeHeader() {
  showHeaderFlog.value = false;
  senderRef.value.closeHeader();
}

function handlePasteFile(firstFile: File, fileList: FileList) {
  showHeaderFlog.value = true;
  senderRef.value.openHeader();
  const fileArray = Array.from(fileList);

  fileArray.forEach((file, index) => {
    files.value.push({
      id: index,
      uid: index + '_' + file.name + '_' + file.size,
      name: file.name,
      fileSize: file.size,
      imgFile: file,
      showDelIcon: true,
      imgVariant: 'square'
    });
  });
}

async function handleHttpRequest(options: any) {
  try {
    ElMessage.info('上传中...');
    const formData = new FormData();
    formData.append('file', options.file);
    formData.append('process_method', 'summary');
    if (!conversationStore.currentSessionId) {
      await conversationStore.createSessionId();
    }
    // todo: 前端UI框架暂不支持改动上传中这三个文字，如果框架支持，则可以把后台接口拆分成上传和解析两个接口
    const fileLength = files.value.length;
    const res = {
      fileName: options.file.name,
      uid: options.file.uid,
      fileSize: options.file.size,
      imgFile: options.file
    };
    files.value.push({
      id: files.value.length,
      uid: res.uid,
      name: res.fileName,
      fileSize: res.fileSize,
      imgFile: res.imgFile,
      showDelIcon: true,
      imgVariant: 'square',
      status: 'uploading',
      percent: 0
    })
    // percent每10s增加10
    const percentInterval = setInterval(() => {
      if (files.value[fileLength].percent >= 99) {
        files.value[fileLength].percent = 99;
        return;
      }
      files.value[fileLength].percent += 9;
    }, 1500);
    formData.append('session_id', conversationStore.currentSessionId);
    fetch('/python-server/upload/', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data =>{
        files.value[fileLength].percent = 100;
        files.value[fileLength].status = 'done';
        clearInterval(percentInterval);
        ElMessage.success('上传成功');
    });
  } catch (error) {
    ElMessage.error('上传失败');
  }
}

function handleDeleteCard(item: SelfFilesCardProps) {
  files.value = files.value.filter((items: any) => items.id !== item.id);
  ElMessage.success('删除成功');
}

function clearFileList() {
  files.value = [];
}


function createMessage(
  role: 'user' | 'ai',
  content: string,
  loading = false,
  typing = false
): listType {
  const isUser = role === 'user';
  return {
    key: Date.now() + Math.random(),
    role,
    placement: isUser ? 'end' : 'start',
    content,
    loading,
    shape: 'corner',
    variant: isUser ? 'outlined' : 'filled',
    isMarkdown: true,
    typing,
    isFog: false,
    avatar: isUser ? USER_AVATAR : AI_AVATAR,
    avatarSize: '24px',
    avatarGap: '12px'
  };
}

function handleHistoryMessageToList(historyMsg: { messages: any[]; }) {
  return historyMsg.messages.map((item) => {
    return createMessage(item.type === 'human' ? 'user' : 'ai', item.content, false, false);
  });
}

watch(() => conversationStore.currentSessionId, async (newSessionId: string) => {
  if (newSessionId && !conversationStore.isNewSession) {
    const historyMsg = await chatService.getMessageHistory(newSessionId);
    chatList.value = handleHistoryMessageToList(historyMsg);
  } else {
    chatList.value = [];
  }
}, { immediate: true });

async function handleSubmit(value: string) {
  if (!value.trim()) return;
  senderLoading.value = true;
  try {

    senderValue.value = '';

    if (!conversationStore.currentSessionId || conversationStore.isNewSession) {
      conversationStore.changeIsNewSession(true);
      await conversationStore.createSessionId();
      // const response = await fetch('/python-server/chat_session/create', {
      //   method: 'POST',
      //   headers: {
      //     'Content-Type': 'application/json',
      //   }
      // });
      // const data = await response.json();
      // conversationStore.changeSessionId(data.session_id)
    } else {
      conversationStore.changeIsNewSession(false);
    }

    const response = await chatService.chat(conversationStore.currentSessionId, value);
    console.log('模型响应:', response);
    chatList.value.push(createMessage('user', value));

    // 创建AI消息占位符
    const aiMessageIndex = chatList.value.length;
    chatList.value.push(createMessage('ai', '', false, true));

    // 流式接收响应
    let reasoningChunk = ''
    for await (const chunk of response) {
      console.log('收到的chunk:', chunk);
      reasoningChunk += chunk.content as string;
      // 更新AI消息内容
      chatList.value[aiMessageIndex].content = reasoningChunk;
    }
    // chatList.value.push(createMessage('ai', response.content as string, false, true));

    if (conversationStore.isNewSession) {
      conversationStore.addConversation(value);
      conversationStore.changeIsNewSession(false)
    }
  } catch (error) {
    console.error('模型调用失败:', error);
    chatList.value.push(createMessage('ai', '抱歉，服务暂时不可用，请稍后再试。'));
  } finally {
    senderLoading.value = false;
  }
}

function clearList() {
  chatList.value = [];
  clearFileList()
}

defineExpose({
  clearList
})
</script>

<template>
    <div style="height: calc(100% - 230px); overflow: auto;">
        <BubbleList
        :list="chatList"
        always-show-scrollbar
        btn-loading
        />
    </div>
    <div style="padding: 0 24px; display: flex;
      flex-direction: column;
      gap: 12px;
      height: 230px;
      justify-content: flex-end;" class="sender-container">
        <Sender ref="senderRef" v-model="senderValue" :loading="senderLoading" variant="updown" clearable @submit="handleSubmit"  @paste-file="handlePasteFile" allow-speech>
          <template #header>
            <div class="header-self-wrap">
              <div class="header-self-title">
                <div class="header-left">
                  附件
                </div>
                <div class="header-right">
                  <el-button @click.stop="closeHeader">
                    <el-icon><CloseBold /></el-icon>
                  </el-button>
                </div>
              </div>
              <Attachments
                :items="files"
                :http-request="handleHttpRequest"
                @delete-card="handleDeleteCard"
                :limit="1"
                accept="'.txt', '.docx', '.doc'"
              />
            </div>
          </template>

          <!-- 自定义前缀 -->
          <template #prefix>
            <div class="prefix-self-wrap">
              <el-button @click="handleOpenHeader">
                <el-icon><Link /></el-icon>
              </el-button>
            </div>
          </template>
        </Sender>
    </div>

</template>



<style scoped lang="less">
.header-self-wrap {
  display: flex;
  flex-direction: column;
  padding: 16px;
  height: 200px;
  .header-self-title {
    width: 100%;
    display: flex;
    height: 30px;
    align-items: center;
    justify-content: space-between;
    padding-bottom: 8px;
  }
  .header-self-content {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 20px;
    color: #626aef;
    font-weight: 600;
  }
}

.prefix-self-wrap {
  display: flex;
}

.sender-container {
  .header-self-wrap {
    height: 100px;
  }
}
</style>