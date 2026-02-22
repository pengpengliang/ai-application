import express from 'express';
import cors from 'cors';
import axios from 'axios';
import dotenv from 'dotenv';
import { RagService } from './src/services/ragService';
import qs from 'qs';

// 加载环境变量
dotenv.config();
const app = express();
const PORT = process.env.PORT || 3001;

// 中间件
app.use(cors());
app.use(express.json());

// app.post('/api/proxy', async (req, res) => {
//   try {
//     const { url, method = 'POST', data = {}, headers = {} } = req.body;

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
app.post('/api/parseDoc', async (req, res) => {
  try {
    const { input } = req.body;
    const response = await axios.post('http://localhost:8000/docServe/invoke', {
      input: {
        input
      }
    });
    res.json(response.data);
  } catch (error: any) {
    console.error('Request error:', error);
    res.status(error.response?.status || 500).json({
      error: error.message,
      details: error.response?.data
    });
  }
});

// RAG 服务接口
// app.get('/api/rag/get-doc', async (req, res) => {
//   try {
//     const ragService = new RagService();

//     const htmlContent = await ragService.getDocContent('https://www.news.cn/api/fortune/20250212/895ac6738b7b477db8d7f36c315aae22/c.html');
//     const splitDoc = await ragService.splitDoc(htmlContent);
//     // console.log(splitDoc[0].pageContent, "splitDoc");
//     // console.log(splitDoc[0].metadata, "metadata");
//     // console.log(splitDoc[1] ,"splitDoc2");

//     // console.log(typeof splitDoc[0]);
//     // await ragService.embedDocs(splitDoc);
//     // console.log(ragService, "ragService");
//     // res.json({
//     //   message: 'RAG service operation completed',
//     //   docsCount: splitDoc.length
//     // });
//     const response = await fetch('http://localhost:8000/initialize-batch', {
//       method: 'POST',
//       headers: {
//         'Content-Type': 'application/json',
//       },
//       body: qs.stringify(splitDoc[0])
//     });

//     const result = await response.json();
//     console.log(result,'initialize');
//   } catch (error) {
//     console.error('RAG service error:', error);
//     res.status(500).json({ error: 'Internal server error' });
//   }
// });

app.listen(PORT, async () => {
  console.log(`Express server running on http://localhost:${PORT}`)
});