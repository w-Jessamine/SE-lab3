# 🔗 Git 远程仓库托管指南

本项目已在本地初始化 Git 仓库，以下是托管到远程仓库的步骤。

## 方式一：托管到 GitHub

### 1. 创建 GitHub 仓库

访问 https://github.com/new 创建新仓库：
- 仓库名：`order-system` 或其他名称
- 可见性：Public（公开） 或 Private（私有）
- **不要**勾选 "Initialize this repository with a README"（已有本地仓库）

### 2. 关联远程仓库

```bash
# 添加远程仓库（替换为你的 GitHub 用户名和仓库名）
git remote add origin https://github.com/YOUR_USERNAME/order-system.git

# 或使用 SSH（推荐）
git remote add origin git@github.com:YOUR_USERNAME/order-system.git

# 验证远程仓库
git remote -v
```

### 3. 推送到远程

```bash
# 推送主分支到远程（首次推送）
git push -u origin main

# 或如果远程分支名是 master
git branch -M main
git push -u origin main
```

### 4. 后续推送

```bash
# 修改代码后
git add .
git commit -m "feat: 添加新功能"
git push
```

---

## 方式二：托管到 Gitee（码云）

### 1. 创建 Gitee 仓库

访问 https://gitee.com/projects/new 创建新仓库：
- 仓库名称：`order-system`
- 是否开源：选择公开或私有
- **不要**勾选 "使用 Readme 文件初始化这个仓库"

### 2. 关联远程仓库

```bash
# 添加远程仓库（替换为你的 Gitee 用户名和仓库名）
git remote add origin https://gitee.com/YOUR_USERNAME/order-system.git

# 或使用 SSH
git remote add origin git@gitee.com:YOUR_USERNAME/order-system.git
```

### 3. 推送到远程

```bash
git push -u origin main
```

---

## 方式三：托管到 GitLab

### 1. 创建 GitLab 项目

访问 https://gitlab.com/projects/new 创建新项目：
- 项目名：`order-system`
- 可见性：Private/Internal/Public

### 2. 关联远程仓库

```bash
git remote add origin https://gitlab.com/YOUR_USERNAME/order-system.git

# 或使用 SSH
git remote add origin git@gitlab.com:YOUR_USERNAME/order-system.git
```

### 3. 推送到远程

```bash
git push -u origin main
```

---

## 🔐 SSH 密钥配置（推荐）

使用 SSH 可以免密推送，更安全方便。

### 1. 生成 SSH 密钥

```bash
# 生成新密钥（替换为你的邮箱）
ssh-keygen -t ed25519 -C "your_email@example.com"

# 或使用 RSA（兼容性更好）
ssh-keygen -t rsa -b 4096 -C "your_email@example.com"

# 按提示操作，默认保存在 ~/.ssh/id_ed25519（或 id_rsa）
```

### 2. 添加到 ssh-agent

```bash
# 启动 ssh-agent
eval "$(ssh-agent -s)"

# 添加私钥
ssh-add ~/.ssh/id_ed25519  # 或 ~/.ssh/id_rsa
```

### 3. 复制公钥

```bash
# macOS
pbcopy < ~/.ssh/id_ed25519.pub

# Linux
cat ~/.ssh/id_ed25519.pub
# 手动复制输出内容

# Windows (Git Bash)
clip < ~/.ssh/id_ed25519.pub
```

### 4. 添加到远程平台

- **GitHub**: Settings → SSH and GPG keys → New SSH key
- **Gitee**: 设置 → SSH 公钥 → 添加公钥
- **GitLab**: User Settings → SSH Keys → Add new key

### 5. 测试连接

```bash
# GitHub
ssh -T git@github.com

# Gitee
ssh -T git@gitee.com

# GitLab
ssh -T git@gitlab.com
```

---

## 📋 常用 Git 命令

```bash
# 查看状态
git status

# 查看提交历史
git log --oneline

# 查看远程仓库
git remote -v

# 拉取远程更新
git pull

# 推送到远程
git push

# 创建新分支
git checkout -b feature/new-feature

# 切换分支
git checkout main

# 合并分支
git merge feature/new-feature

# 标签（版本）
git tag v1.0.0
git push origin v1.0.0
```

---

## 🚀 推荐的 .gitignore 补充

项目已包含 `.gitignore`，如需补充可添加：

```gitignore
# 数据库文件
*.db
*.sqlite
*.sqlite3

# 环境变量
.env
.env.local

# IDE
.vscode/
.idea/
*.swp

# Python
__pycache__/
*.pyc
venv/
.pytest_cache/

# macOS
.DS_Store
```

---

## ✅ 验证推送成功

推送后访问远程仓库网页，应该能看到：
- ✅ 完整的项目文件结构
- ✅ README.md 显示在首页
- ✅ UML 图片可预览
- ✅ 提交历史记录

---

## 🆘 常见问题

### 问题1：push 被拒绝（non-fast-forward）

```bash
# 先拉取远程更新
git pull --rebase origin main

# 再推送
git push
```

### 问题2：远程仓库已有 README

```bash
# 拉取远程内容并合并
git pull origin main --allow-unrelated-histories

# 推送
git push -u origin main
```

### 问题3：修改远程仓库地址

```bash
# 查看当前远程地址
git remote -v

# 修改为新地址
git remote set-url origin NEW_URL
```

### 问题4：取消关联远程仓库

```bash
git remote remove origin
```

---

## 📚 推荐阅读

- [GitHub 官方文档](https://docs.github.com/)
- [Gitee 帮助中心](https://gitee.com/help)
- [Git 教程 - 廖雪峰](https://www.liaoxuefeng.com/wiki/896043488029600)
- [Pro Git 中文版](https://git-scm.com/book/zh/v2)

