# Steam遊戲數據分析系統# Steam 数据分析系统



## 🎯 項目簡介课程设计项目 - 自动化的Steam游戏数据抓取与评论威胁分析



本項目是一個基於Python的Steam遊戲數據分析系統，專為課程設計開發。系統能夠自動收集Steam熱銷遊戲數據，進行評論威脅分析，並提供多維度的統計分析和可視化展示。## 快速开始



### 主要功能### 1. 安装依赖

- 🎮 **遊戲數據爬取**：自動獲取Steam熱銷榜遊戲信息

- 🧹 **數據清洗**：智能處理和標準化原始數據```bash

- 💬 **評論分析**：檢測評論中的潛在威脅和異常行為pip install requests beautifulsoup4 pandas matplotlib numpy

- 📊 **統計分析**：多維度數據分析（價格心理學、折扣規律等）```

- 📈 **可視化展示**：生成分析圖表和詳細報告

### 2. 运行完整流水线（推荐）

## 🚀 快速開始

```bash

### 運行環境# Windows PowerShell

- Python 3.8+cd "d:\app\app\bilibili bullet comment sentiment analysis system\b-crawler"

- 依賴包：pandas, matplotlib, requests, beautifulsoup4, scipypython src\main_pipeline.py



### 一鍵運行# 或指定参数

```bashpython src\main_pipeline.py --pages 1 --games 5 --reviews 20

# 運行完整增強分析（推薦）```

run_enhanced_analysis.bat

### 3. 运行单个模块

# 快速查看數據統計

quick_stats.bat```bash

```# 只运行某一步

python src\main_pipeline.py --step 1  # 数据抓取

### 分步驟運行python src\main_pipeline.py --step 2  # 数据清洗

```bashpython src\main_pipeline.py --step 3  # 评论分析

# 1. 收集數據（2頁約50款遊戲）python src\main_pipeline.py --step 4  # 可视化

python src/main_pipeline.py --pages 2 --step 1

# 不显示图表（批处理模式）

# 2. 清洗數據python src\main_pipeline.py --no-plots

python src/main_pipeline.py --step 2```



# 3. 分析評論## 命令行参数

python src/main_pipeline.py --games 8 --reviews 25 --step 3

| 参数 | 说明 | 默认值 |

# 4. 生成分析圖表|------|------|--------|

python src/main_pipeline.py --step 4| `--pages` | 抓取Steam畅销榜页数 | 1 |

```| `--games` | 分析评论的游戏数量 | 5 |

| `--reviews` | 每款游戏抓取评论数 | 20 |

## 📁 項目結構| `--no-plots` | 不显示可视化图表 | False |

| `--step` | 只执行特定步骤 (1/2/3/4/all) | all |

```

b-crawler/## 示例

├── src/                              # 源代碼目錄

│   ├── main_pipeline.py              # 主流程控制器```bash

│   ├── steam_data_extractor.py       # Steam數據爬蟲# 快速测试（抓1页，分析3款游戏，每款15条评论）

│   ├── show_stats.py                 # 數據統計工具python src\main_pipeline.py --pages 1 --games 3 --reviews 15

│   ├── analysis part/               # 分析模塊

│   │   ├── data_analysis.py          # 核心統計分析# 大规模分析（抓3页，分析10款游戏）

│   │   └── enhanced_analysis_summary.py  # 分析報告生成python src\main_pipeline.py --pages 3 --games 10 --reviews 30

│   ├── clean/                       # 數據清洗模塊

│   │   └── data_cleaner.py           # 數據清洗器# 只清洗已有数据

│   └── comments/                    # 評論分析模塊python src\main_pipeline.py --step 2

│       └── simple_steam_crawler_easy.py  # 評論威脅檢測

├── data/                            # 數據文件存儲# 批处理模式（不弹窗）

├── analysis_results/                # 分析結果輸出python src\main_pipeline.py --no-plots

├── docs/                           # 詳細文檔```

├── examples/                       # 使用範例

├── run_enhanced_analysis.bat       # 一鍵增強分析## 项目结构

├── quick_stats.bat                 # 快速統計查看

└── README.md                       # 本文檔```

```b-crawler/

├── src/

## 📊 分析功能特色│   ├── main_pipeline.py           # 主控制器（入口）

│   ├── steam_data_extractor.py    # 数据抓取

### 1. 多維度價格分析│   ├── clean/

- **價格尾數心理學**：分析.99定價對折扣的影響│   │   └── data_cleaner.py        # 数据清洗

- **折扣vs發售時長**：探討遊戲年齡與折扣力度關係│   ├── comments/

- **首發溢價分析**：研究新遊戲定價策略│   │   └── simple_steam_crawler_easy.py  # 评论分析

│   └── analysis part/

### 2. 評論安全分析  │       └── data_analysis.py       # 数据分析与可视化

- **威脅檢測**：識別外部鏈接、可疑關鍵詞、聯繫方式├── data/                          # 输出目录

- **語言分布**：統計中英文評論比例│   ├── steam_topsellers_simple.csv

- **異常行為**：檢測刷評、廣告等不當行為│   ├── steam_topsellers_simple_cleaned.csv

│   └── comment_analysis_results.csv

### 3. 高級統計分析├── docs/                          # 文档

- **ANOVA分析**：價格分組的顯著性檢驗└── examples/                      # 示例脚本

- **Mann-Whitney U檢驗**：非參數統計比較```

- **Cliff's Delta**：效應量計算

## 输出文件

## 📈 輸出文件說明

| 文件 | 内容 |

### 數據文件|------|------|

- `steam_topsellers_simple.csv` - 原始爬取數據| `data/steam_topsellers_simple.csv` | 原始游戏数据 |

- `steam_topsellers_simple_cleaned.csv` - 清洗後數據  | `data/steam_topsellers_simple_cleaned.csv` | 清洗后游戏数据 |

- `comment_analysis_results.csv` - 評論分析結果| `data/comment_analysis_results.csv` | 评论威胁分析结果 |



### 分析結果## 技术栈

- `analysis_results/analysis_report.md` - 詳細分析報告

- 可視化圖表（6個分析維度）- **Python 3.10+**

- 控制台統計輸出- **requests**: HTTP请求

- **BeautifulSoup4**: HTML解析

## ⚙️ 配置參數- **pandas**: 数据处理

- **matplotlib**: 数据可视化

### 爬蟲配置- **numpy**: 数值计算

- 頁面數：默認2頁（約50款遊戲）

- 延遲設置：0.7-0.8秒（平衡效率和禮貌）## 答辩演示

- 重試機制：4次重試，指數退避

```bash

### 分析配置  # 推荐配置（3-5分钟完成）

- 評論分析遊戲數：默認8款python src\main_pipeline.py --pages 1 --games 3 --reviews 15

- 每款遊戲評論數：默認25條```

- 統計顯著性水平：α=0.05

演示要点：

## 🛠️ 技術特點1. 展示命令行输出的实时进度

2. 打开生成的CSV文件展示数据

### 1. 課設友好設計3. 查看弹出的可视化图表

- **簡單易懂**：避免過於複雜的算法實現4. 讲解威胁检测结果

- **模塊化**：清晰的代碼結構便於理解和修改

- **詳細註釋**：每個函數都有清楚的說明## License



### 2. 數據分析深度MIT License - 仅用于课程学习

- **統計嚴謹性**：使用適當的統計檢驗方法
- **創新分析角度**：價格心理學、安全檢測等
- **可視化豐富**：多種圖表類型展示結果

### 3. 錯誤處理完善
- **網絡異常**：智能重試和超時處理
- **數據異常**：缺失值和格式錯誤處理
- **用戶友好**：清晰的錯誤信息和進度提示

## 📚 技術文檔

詳細的代碼說明和技術文檔請查看 `docs/` 目錄：
- 各模塊詳細說明
- 函數接口文檔
- 數據格式規範
- 故障排除指南

## ⚠️ 注意事項

1. **網絡要求**：需要穩定的網絡連接訪問Steam
2. **運行時間**：完整分析約需10-15分鐘
3. **數據更新**：Steam數據實時變化，結果會有差異
4. **道德使用**：請遵守Steam服務條款，合理使用爬蟲

---

**開發時間**: 2024年11月  
**適用課程**: 網絡程序設計實踐  
**技術棧**: Python + pandas + matplotlib + requests