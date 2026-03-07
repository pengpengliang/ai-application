import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router';

const routes: Array<RouteRecordRaw> = [
  {
    path: '/',
    name: 'ChatRobot',
    component: () => import('../views/tools/ChatRobot.vue')
  },
  {
    path: '/home',
    name: 'Home',
    component: () => import('../views/Home.vue')
  },
  {
    path: '/tools/translateTool',
    name: 'TranslateTool',
    component: () => import('../views/tools/TranslateTool.vue')
  },
  {
    path: '/knowledge-base',
    name: 'KnowledgeBase',
    component: () => import('../views/KnowledgeBase.vue')
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

export default router;