# 🚀 Alpha-Arena-Plus 配置指南

## 📋 环境配置步骤

### 1️⃣ 安装依赖

```bash
pip install -r requirements.txt
```

### 2️⃣ 配置 OpenAI API Key

#### 创建 `.env` 文件

在项目根目录创建 `.env` 文件：

```bash
# 在 PowerShell 中执行
New-Item .env -ItemType File
```

然后编辑 `.env` 文件，添加：

```
OPENAI_API_KEY=sk-your-api-key-here
```

> 💡 **提示**：参考 `env_template.txt` 文件查看完整配置模板

### 3️⃣ 获取 OpenAI API Key

1. 访问：https://platform.openai.com/api-keys
2. 登录你的 OpenAI 账号
3. 点击 "Create new secret key"
4. 复制生成的 key（格式：`sk-...`）

## ⚠️ 注意事项

1. **不要提交 `.env` 文件到 Git**（已在 `.gitignore` 中配置）
2. **保护好你的 API Key**，不要在代码中硬编码
3. **OpenAI API 会产生费用**，建议设置使用限额
4. **运行前确保有足够的 API 余额**