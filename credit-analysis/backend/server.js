const express = require('express');
const cors = require('cors');
const multer = require('multer');
const path = require('path');
const fs = require('fs');
const { createWorker } = require('tesseract.js');

const app = express();
const PORT = 3001;

app.use(cors());
app.use(express.json());

// ── 加载贷款规则 ──
const rulesPath = path.join(__dirname, 'rules.json');
function loadRules() {
  const raw = fs.readFileSync(rulesPath, 'utf-8');
  return JSON.parse(raw).rules;
}

// ── multer 配置 ──
const storage = multer.diskStorage({
  destination: path.join(__dirname, 'uploads'),
  filename(req, file, cb) {
    const ext = path.extname(file.originalname);
    cb(null, Date.now() + ext);
  }
});

const upload = multer({
  storage,
  limits: { fileSize: 10 * 1024 * 1024 },
  fileFilter(req, file, cb) {
    const allowed = ['.pdf', '.png', '.jpg', '.jpeg', '.bmp', '.tiff'];
    const ext = path.extname(file.originalname).toLowerCase();
    if (allowed.includes(ext)) {
      cb(null, true);
    } else {
      cb(new Error('不支持的文件格式，请上传 PDF 或图片文件（png/jpg/bmp/tiff）'));
    }
  }
});

// ── 从文本中提取征信分数 ──
function extractScore(text) {
  if (!text) return null;

  // 优先匹配带关键词的分数（关键词后允许任意分隔符）
  const keywordPatterns = [
    /征信.*?(\d{2,3})\s*分/,
    /信用.*?(\d{2,3})\s*分/,
    /评分.*?(\d{2,3})\s*分?/,
    /分数.*?(\d{2,3})\s*分?/,
    /score\D*(\d{2,3})\b/i,
    /credit\D*(\d{2,3})\b/i,
  ];

  for (const re of keywordPatterns) {
    const match = text.match(re);
    if (match) {
      const score = parseInt(match[1], 10);
      if (score >= 200 && score <= 999) return score;
    }
  }

  // 如果没有关键词上下文，从文本中找 300-999 的数字，取最可能是分数的那一个
  const numbers = [...text.matchAll(/(?<!\d)([3-9]\d{2})(?!\d)/g)];
  if (numbers.length === 0) return null;

  // 偏好：离"分"字最近的数字
  const fenIdx = text.indexOf('分');
  if (fenIdx >= 0) {
    let best = null, bestDist = Infinity;
    for (const m of numbers) {
      const dist = Math.abs(m.index - fenIdx);
      if (dist < bestDist) { bestDist = dist; best = parseInt(m[1]); }
    }
    if (best && bestDist < 30) return best;
  }

  // 取最后一个（通常最靠近正文末尾，而非元数据）
  return parseInt(numbers[numbers.length - 1][1]);
}

// ── 用 pdfjs-dist 解析 PDF（动态 import ESM 模块） ──
let _pdfjsDoc = null;
async function getPdfjs() {
  if (_pdfjsDoc) return _pdfjsDoc;
  _pdfjsDoc = await import('pdfjs-dist/legacy/build/pdf.mjs');
  return _pdfjsDoc;
}

async function parsePdfWithPdfjs(filePath) {
  try {
    const { getDocument } = await getPdfjs();
    const data = new Uint8Array(fs.readFileSync(filePath));
    const doc = await getDocument({ data, useWorkerFetch: false, isEvalSupported: false }).promise;
    let text = '';
    for (let i = 1; i <= doc.numPages; i++) {
      const page = await doc.getPage(i);
      const content = await page.getTextContent();
      text += content.items.map(it => it.str).join(' ') + '\n';
    }
    return text.trim();
  } catch { return null; }
}

// ── 用 Tesseract.js 做图片 OCR ──
let _ocrWorker = null;
async function getOcrWorker() {
  if (_ocrWorker) return _ocrWorker;
  _ocrWorker = await createWorker('chi_sim+eng');
  return _ocrWorker;
}

async function ocrImage(filePath) {
  try {
    const worker = await getOcrWorker();
    // 读取文件为 Buffer 再传给 tesseract，避免路径问题
    const imageBuf = require('fs').readFileSync(filePath);
    const { data } = await worker.recognize(imageBuf);
    return (data.text || '').trim();
  } catch (err) {
    console.error('OCR failed:', err.message);
    return null;
  }
}

// ── 从二进制中捞可读文本 ──
function extractTextFromBinary(filePath) {
  try {
    const buf = fs.readFileSync(filePath);
    const str = buf.toString('utf-8');
    // 去掉不可打印字符
    const cleaned = str.replace(/[^\x20-\x7E一-鿿㐀-䶿]/g, '');
    return cleaned.length > 20 ? cleaned : null;
  } catch { return null; }
}

// ── POST /api/upload ──
app.post('/api/upload', upload.single('file'), async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({ error: '请选择要上传的文件' });
    }

    const ext = path.extname(req.file.originalname).toLowerCase();
    let text = '';

    if (ext === '.pdf') {
      text = await parsePdfWithPdfjs(req.file.path);
      if (!text) text = extractTextFromBinary(req.file.path);
    } else {
      text = await ocrImage(req.file.path);
      if (!text) text = extractTextFromBinary(req.file.path);
    }

    // 优先从文本内容提取，其次从文件名
    const contentScore = extractScore(text || '');
    const fileNameScore = extractScore(req.file.originalname);
    const score = contentScore || fileNameScore;

    if (!score) {
      const hint = ext === '.pdf'
        ? '无法从 PDF 中提取征信分数。请确认文件包含可选中的文字（非扫描图片），且内容含 "征信分数：XXX" 等关键词。'
        : '无法从图片中识别出征信分数。请确保图片清晰、文字可辨，且包含 "征信分数：XXX" 等关键词。';
      return res.status(400).json({ error: hint });
    }

    const rules = loadRules();
    const matched = rules.find(r => score >= r.minScore && score <= r.maxScore);

    if (!matched || matched.banks.length === 0) {
      return res.json({
        score,
        banks: [],
        message: `您的征信分数为 ${score} 分，暂无可匹配的银行贷款方案。建议继续保持良好信用记录。`
      });
    }

    res.json({
      score,
      scoreRange: `${matched.minScore}-${matched.maxScore}分档`,
      banks: matched.banks,
      total: matched.banks.length,
      analyzedAt: new Date().toISOString()
    });
  } catch (err) {
    console.error('分析失败:', err);
    res.status(500).json({ error: '服务器内部错误，请稍后重试' });
  }
});

// ── GET /api/rules ──
app.get('/api/rules', (_req, res) => {
  res.json({ rules: loadRules() });
});

// ── 定时清理上传文件（30分钟） ──
setInterval(() => {
  const dir = path.join(__dirname, 'uploads');
  fs.readdir(dir, (err, files) => {
    if (err) return;
    const now = Date.now();
    files.forEach(f => {
      const fp = path.join(dir, f);
      fs.stat(fp, (_, s) => {
        if (s && now - s.mtimeMs > 30 * 60 * 1000) fs.unlink(fp, () => {});
      });
    });
  });
}, 10 * 60 * 1000);

app.listen(PORT, async () => {
  console.log(`征信分析后端已启动 → http://localhost:${PORT}`);

  // 预热 OCR 模型（后台下载语言包）
  getOcrWorker().then(() => {
    console.log('OCR 引擎就绪 (chi_sim+eng)');
  }).catch(e => {
    console.error('OCR 模型加载失败:', e.message);
  });
});
