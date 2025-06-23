# 從 llama.cpp 學習 LLM 推理原理》學習路線圖

這是一份為你量身打造的「從 llama.cpp 學習 LLM 推理原理」學習路線圖，重點在於**掌握底層原理、系統化知識與可實驗的環境**。整體分成 5 個階段，每階段都有學習目標、具體項目、建議時間與工具資源。

---

## 🧭 路線圖概覽

| 階段 | 目標                           | 主題焦點                               | 建議時間  |
| ---- | ------------------------------ | -------------------------------------- | --------- |
| 1    | 初探 LLM 推理流程              | 模型載入、tokenizer、推理循環          | 1 週      |
| 2    | 深入 KV cache 與 context 管理  | attention cache, context 長度限制      | 1 週      |
| 3    | 掌握 sampling 與 decoding 策略 | greedy, top-k, top-p, temperature 控制 | 3 天      |
| 4    | 探索量化與效能調校             | Q4/Q5/Q8, mmap, threading, GPU 加速    | 1 週      |
| 5    | 動手做本地 Agent/Chat App 原型 | 推理封裝、簡易 Chat API、上下文記憶等  | 1 ～ 2 週 |

---

## 🧩 詳細分階段內容

---

### ✅ 第一階段：入門與核心流程認識

> **目標**：理解一個 LLM 推理從文字 → token → logits → token 的整個流程

**建議步驟：**

- Clone 並編譯 [llama.cpp](https://github.com/ggerganov/llama.cpp)
- 下載 GGUF 模型（如 `TheBloke/Llama-2-7B-Chat-GGUF`）
- 測試 CLI 推理：`./main -m model.gguf -p "Hello, my name is"`
- 閱讀 `main/main.cpp` → 找出：
  - `llama_model_loader`
  - `llama_tokenize()`
  - `llama_eval() `(現在是 `llama_decode()`) 與 `llama_sample_token()`

**推薦學習點：**

- 模型如何載入到 RAM？
- token 是如何轉換的？（BPE encoding）
- logits → 選出下一個 token 的流程？

---

### ✅ 第二階段：KV Cache 與上下文管理

> **目標**：理解 KV Cache 結構與 context 長度對效能與穩定性的影響

**建議閱讀：**

- `llama_eval()`(現在是 `llama_decode()`) 是如何儲存 `KV Cache` 的？
- 如何做到「只餵新 token」進去而非重跑整個 prompt？

**你會看到：**

```cpp
llama_kv_cache *cache = model->ctx.kv_self;
```

**實驗建議：**

- 用長 prompt（超過 3000 tokens）試試，看 memory usage
- 測試 `-ngl` 和 `--ctx-size` 的效果

**學習點：**

- KV Cache 如何儲存 key/value？
- 當 context 太長時，會怎樣？如何裁剪（sliding window）？

---

### ✅ 第三階段：Sampling 策略精通

> **目標**：理解為何 sampling 策略影響生成風格與合理性

**你將學到：**

- Top-k: 保留 k 個最大概率再隨機挑選
- Top-p: 累計機率達到 p 為止再隨機挑選
- Temperature: 控制 logits 的熵
- Greedy decoding: 每次都選機率最高

**程式路徑：**

- `sampling.cpp` 裡的 `llama_sample_top_k`, `llama_sample_temperature`

**實驗建議：**

- 用不同 sampling 組合生成故事（暴力 or 夢幻）

---

### ✅ 第四階段：模型量化與推理加速

> **目標**：實際測量不同量化設定對模型精度與速度的影響

**你要學會：**

- q4_0, q5_1, q8_0 差在哪？
- 如何使用 `llama_quantize` 重新量化模型？
- mmap、thread 數設定、GPU 開啟方式

**實驗建議：**

- 用 `bench/` 跑 latency benchmark
- 設定 `--n-gpu-layers`, `--threads`

**學習點：**

- 為什麼小模型或量化模型會變笨？
- mmap 如何幫助冷啟動快很多？

---

### ✅ 第五階段：打造自己的本地 Agent 原型

> **目標**：整合前面所有概念，打造一個簡易 API / chatbot 應用

**實作建議：**

- 使用 `examples/server` 模組
- 將推理邏輯包成 Flask 或 FastAPI 服務
- 加入「聊天歷史」做出多輪記憶
- 可額外試：embedding 模組（`llama.cpp` 有支援）

**進階挑戰：**

- 使用 `llama.cpp` 多模型切換（透過 mmap）
- 加入 RAG (Retrieval Augmented Generation) 功能

---

## 🛠️ 工具與資源推薦

| 工具/資源                                                  | 用途                         |
| ---------------------------------------------------------- | ---------------------------- |
| [llama.cpp GitHub](https://github.com/ggerganov/llama.cpp) | 主程式碼庫                   |
| [TheBloke GGUF 模型倉庫](https://huggingface.co/TheBloke)  | 模型下載                     |
| Chatbot UI (前端)                                          | 和本地 llama.cpp API 整合    |
| Netron                                                     | 可視化 GGUF 或 ONNX 模型結構 |

---

### 💬 補充說明

- vLLM 與 llama.cpp 最大的差異在於 **併發與推理策略**，但 **底層 token-level 推理流程是一樣的**。
- 理解 llama.cpp 能幫助你**debug 或優化推理效能**，並打下你未來設計 LLM Runtime 的基礎。

## 回答問題：

## 1. KV Cache 記憶體管理

- 如何初始化、更新、裁剪 `kv_cache`
- 為什麼長上下文會造成 OOM
- 與 `rope` 位置編碼搭配使用

---

## 2. Prompt 與 tokenization

- 模型是怎麼把文字轉成 token 的？
- BOS/EOS token 有什麼影響？
- 為什麼 prompt 編寫對輸出有這麼大影響？

---

## 3. 量化技巧

- q4_0, q4_K, q5_1, q8_0 等代表什麼意思？
- 訓練後量化（Post-Training Quantization, PTQ）怎麼影響效能與精度

---

## 4. 模型輸入與 sampling 策略

- greedy / top-k / nucleus sampling 差異與程式實作
- 如何決定下一個 token？參與運算的 logits 怎麼處理？

---

## 5. 在 CPU/GPU 上部署與效能調優

- 單線程 vs 多線程（`n_threads`）
- GPU 加速是否有效（Metal / CUDA / OpenCL）
- memory mapping（mmap）的角色
