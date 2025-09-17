# MC服务器-dynmap在线地图数据爬虫系统

这是一个用于获取和分析MC服务器-dynmap在线地图数据的爬虫系统，能够自动获取在线玩家信息和地图城市数据，并提供强大的查询和统计功能。
**编写时支持版本信息：coreversion："3.7-SNAPSHOT-985"，dynmapversion："3.7-SNAPSHOT-968"
## 功能特性

### 🎮 数据获取
- **在线玩家数据**: 自动获取当前在线玩家的位置、生命值、护甲等信息
- **城市信息**: 获取地图上所有城市的详细信息，包括区块面积、所有者、玩家列表等
- **国家数据**: 自动解析城市所属的国家信息，包括领土统计
- **非活跃玩家检测**: 自动检测41-42天未在线的玩家，并报告
- **report.py**: 自定义通知模块，用于报告非活跃玩家，可以自由定义不影响原有爬虫系统。

### 📊 数据存储
- 使用SQLite数据库存储所有数据
- 自动维护玩家、城市、国家三张数据表
- 支持数据的增量更新和历史记录

### 🔍 查询功能
- **玩家查询**: 根据账户名查询玩家详细信息，包括所在城市和国家
- **城市查询**: 查询城市的区块面积、玩家列表、所属国家等信息
- **国家查询**: 查询国家的领土统计、下属城市列表等
- **搜索功能**: 支持关键词搜索玩家、城市、国家
- **排行榜**: 城市区块面积排行榜、国家领土面积排行榜

### 📈 统计分析
- 数据库统计摘要
- 最近在线玩家统计
- 非活跃玩家检测（41-42天未在线提醒）
- 数据导出功能

## 项目结构

```
simmc_spider/
├── main.py              # 主程序入口
├── report.py            # 自定义通知模块
├── spider.py            # 爬虫核心类
├── database.py          # 数据库模型类
├── parser.py            # 数据解析器类
├── query_service.py     # 查询服务类
├── requirements.txt     # 依赖包列表
├── config.json          # 配置文件（自动生成）
├── simmc_data.db        # SQLite数据库（自动生成）
└── README.md            # 项目说明
```
**你可以自由编写report.py模块，实现自定义的通知功能，比如发送kook，qq通知等**

## 安装和使用

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 运行方式

#### 交互模式（推荐）
```bash
python main.py
```
或
```bash
python main.py interactive
```

#### 命令行模式
```bash
# 执行一次数据获取
python main.py run

# 持续运行模式（每30分钟获取一次）
python main.py continuous

# 自定义间隔时间（每10分钟获取一次）
python main.py continuous 10

# 查询玩家信息
python main.py player execsuroot

# 查询城市信息
python main.py city "北海的屁股不知道南边的北极熊"

# 查询国家信息
python main.py country "神圣米兰共和国"

# 搜索功能
python main.py search "Love1y_fxs"

# 显示排行榜
python main.py rankings

# 显示统计信息
python main.py stats

# 导出数据
python main.py export all
python main.py export players
python main.py export cities
```

### 3. 交互模式命令

在交互模式下，可以使用以下命令：

- `run` - 执行一次数据获取
- `continuous [间隔分钟]` - 持续运行模式
- `player <账户名>` - 查询玩家信息
- `city <城市名>` - 查询城市信息
- `country <国家名>` - 查询国家信息
- `search <关键词>` - 搜索玩家/城市/国家
- `rankings` - 显示排行榜
- `stats` - 显示统计信息
- `online [小时数]` - 显示最近在线玩家
- `export [类型] [文件名]` - 导出数据
- `help` - 显示帮助
- `quit` - 退出程序

## 配置说明

系统会自动生成 `config.json` 配置文件，包含以下配置项：

```json
{
  "db_path": "simmc_data.db",
  "timeout": 30,
  "retry_count": 3,
  "retry_delay": 5,
  "interval_minutes": 60,
  "player_api_url": "https://map.simmc.cn/standalone/dynmap_world.json",
  "city_api_url": "https://map.simmc.cn/tiles/_markers_/marker_world.json"
}
```
📋 配置参数说明
|参数名称|默认值|说明|
|--|--|--|
|db_path|simmc_data.db|SQLite数据库文件路径|
|timeout|30|HTTP请求超时时间（秒）|
|retry_count|3|请求失败时的重试次数|
|retry_delay|5|重试间隔时间（秒）|
|interval_minutes|60|持续运行模式的数据获取间隔（分钟）|
|player_api_url|https://map.simmc.cn/standalone/dynmap_world.json|获取在线玩家数据的API端点|
|city_api_url|https://map.simmc.cn/tiles/_markers_/marker_world.json|获取城市数据的API端点|
## 数据库结构

### 玩家表 (players)
- account: 玩家账户名
- name: 玩家显示名称
- world: 所在世界
- x, y, z: 坐标位置
- health: 生命值
- armor: 护甲值
- update_time: 更新时间戳

### 城市表 (cities)
- city_name: 城市名称
- city_level: 城市等级
- city_owner: 城市所有者
- city_balance: 城市余额
- city_block: 城市区块数
- city_players: 城市玩家列表（JSON格式）
- city_country: 所属国家
- x, y, z: 城市坐标
- update_time: 更新时间戳

### 国家表 (countries)
- country_name: 国家名称
- country_level: 国家等级
- country_capital: 国家首都
- territories: 领土列表（JSON格式）
- territory_count: 领土数量
- player_count: 玩家数量
- total_blocks: 总区块数
- update_time: 更新时间戳

## 特殊功能

### 非活跃玩家检测
系统会自动检测41-42天未在线的玩家，并在数据更新时打印相关信息，包括：
- 玩家基本信息
- 所在城市信息
- 所属国家信息

### 数据验证
- 自动过滤无效数据
- 跳过名为"出生点"的城市数据
- 验证数据完整性和格式正确性

### 错误处理
- 网络请求重试机制
- 数据库操作异常处理
- 优雅的错误提示和恢复

## 注意事项

1. 首次运行时会自动创建数据库和配置文件
2. 建议在稳定的网络环境下运行
3. 持续运行模式下可以使用 Ctrl+C 安全停止
4. 数据库文件会随着时间增长，可以定期清理旧数据

## 技术栈

- Python 3.7+
- SQLite3 数据库
- requests 网络请求
- BeautifulSoup4 HTML解析
- 模块化设计，功能解耦

## 许可证：Apache-2.0 license

本项目仅供学习和研究使用，请遵守相关服务器的使用条款。