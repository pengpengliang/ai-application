<template>
  <div class="home-container">
    <h1>欢迎使用翻译工具</h1>
    <p>请点击下方链接进入翻译工具页面</p>
    <router-link to="/tools/translateTool" class="btn">
      进入翻译工具
    </router-link>
    <router-link to="/" class="btn">
      进入聊天机器人
    </router-link>
  </div>
</template>

<style scoped>
.home-container {
  max-width: 600px;
  margin: 0 auto;
  padding: 40px 20px;
  text-align: center;
  font-family: Arial, sans-serif;
}

h1 {
  color: #333;
  margin-bottom: 20px;
}

p {
  color: #666;
  margin-bottom: 30px;
  font-size: 16px;
}

.btn {
  display: inline-block;
  padding: 12px 24px;
  background-color: #4CAF50;
  color: white;
  text-decoration: none;
  border-radius: 4px;
  font-size: 16px;
  transition: background-color 0.3s;
}

.btn:hover {
  background-color: #45a049;
}
</style>