import express from 'express';
import cors from 'cors';
import axios from 'axios';
import dotenv from 'dotenv';
import { RagService } from './src/services/ragService';

// 加载环境变量
dotenv.config();
const app = express();
const PORT = process.env.PORT || 3001;

// 中间件
app.use(cors());
app.use(express.json());

// app.post('/api/proxy', async (req, res) => {
//   try {
//     const { url, method = 'GET', data = {}, headers = {} } = req.body;

//     if (!url) {
//       return res.status(400).json({ error: 'URL is required' });
//     }

//     const response = await axios({
//       url,
//       method,
//       data,
//       headers
//     });

//     res.json(response.data);
//   } catch (error: any) {
//     console.error('Proxy error:', error);
//     res.status(error.response?.status || 500).json({
//       error: error.message,
//       details: error.response?.data
//     });
//   }
// });

// 自定义接口示例
app.get('/api/hello', async (req, res) => {
  res.json({ message: 'Hello from Express middle layer!' });
});

// RAG 服务接口
// app.get('/api/rag/get-doc', async (req, res) => {
//   try {
//     const ragService = new RagService();

//     const htmlContent = await ragService.getDocContent('https://www.news.cn/api/fortune/20250212/895ac6738b7b477db8d7f36c315aae22/c.html');
//     const splitDoc = await ragService.splitDoc(htmlContent);
//     // console.log(splitDoc, "splitDoc");
//     await ragService.embedDocs(splitDoc);
//     // console.log(ragService, "ragService");
//     res.json({
//       message: 'RAG service operation completed',
//       docsCount: splitDoc.length
//     });
//   } catch (error) {
//     console.error('RAG service error:', error);
//     res.status(500).json({ error: 'Internal server error' });
//   }
// });

app.listen(PORT, async () => {
  console.log(`Express server running on http://localhost:${PORT}`)
});