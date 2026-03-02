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
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

export default router;