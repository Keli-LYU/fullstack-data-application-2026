# TP 1 — 第 4 次课：将前端连接到第 1 次课的 API（1 小时 30 分钟）

## 你将完成什么

第 1、2 次课的 API 已经可以运行，但只有开发者能通过 `/docs` 或 `curl` 使用它。本实验将为它添加一个**前端**：第二个 FastAPI 应用，用于提供 HTML 页面，并且**只通过 REST API** 与后端通信。

暂时不处理数据库：后端继续使用内存存储。这是有意安排的。先建立前端与后端之间的边界，然后在 [TP 2](tp2-backend-db.zh-CN.md) 中更换 API 背后的全部实现，而前端无需察觉。

参考课程为[课程 1 的第 2 节](https://github.com/Keli-LYU/fullstack-data-application-2026/blob/main/seances/seance-4-webapp/cours/cours1-frontend.md#2-le-frontend--une-application-fastapi-qui-sert-du-html)。请保持该课程页面打开：这里不会重复其中的全部解释。

## 实验目标

完成后，你应能够：

- 将仓库组织成 `backend/` 和 `frontend/` 两个独立应用，通过一次 `docker compose up` 启动；
- 通过环境变量为前端配置后端地址；
- 将所有后端调用集中封装在唯一的客户端类 `ApiClient` 中；
- 使用 Jinja2 模板和共用基础模板编写 HTML 页面；
- 使用 Post/Redirect/Get（提交／重定向／获取）模式处理表单；
- 将 API 错误转换为易读的提示。

## 前提条件

- 完成第 1 次课实验：内存存储的 `items` CRUD 和 `reservations` 资源。
- 完成第 2 次课实验：API 测试套件全部通过。
- 已启动 Docker Desktop。

---

## 步骤 0 — 重新组织仓库

此前仓库只有一个应用，现在将有两个。把 API 相关内容移到 `backend/`：

```text
votre-depot/
├── backend/
│   ├── app/              # main.py、routers/、schemas/（不变）
│   ├── tests/            # 第 2 次课的测试（不变）
│   ├── pytest.ini
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/             # 暂时为空
├── .gitignore
└── docker-compose.yml    # 留在根目录
```

使用 `git mv`，不要只是直接移动文件：这样 Git 会保留各文件的历史。

```bash
mkdir backend frontend
git mv app tests pytest.ini requirements.txt Dockerfile backend/
```

然后调整 `docker-compose.yml`：

- 将服务 `api` 重命名为 `backend`；
- 构建上下文（`build`）改为 `backend/` 目录；
- 卷挂载改为将 `backend/app` 和 `backend/tests` 挂载进容器。

**检查：**

```bash
docker compose up --build -d
curl http://localhost:8000/health
docker compose exec backend pytest
```

API 应正常响应，而且**第 2 次课的全部测试无需修改即可通过**。若有测试失败，说明移动过程改变了某些内容：先修复再继续。提交一次 Git commit。

---

## 步骤 1 — 前端骨架

创建前端目录结构（[课程 1 第 2.2 节](https://github.com/Keli-LYU/fullstack-data-application-2026/blob/main/seances/seance-4-webapp/cours/cours1-frontend.md#22-la-structure-du-projet-frontend)对此有解释）：

```text
frontend/
├── Dockerfile
├── requirements.txt
└── app/
    ├── __init__.py
    ├── main.py
    ├── api_client.py
    ├── templating.py
    ├── routers/
    │   ├── __init__.py
    │   └── items.py
    ├── templates/
    │   ├── base.html
    │   ├── erreur.html
    │   └── items/
    └── static/
        └── style.css
```

编写 `frontend/requirements.txt`。前端需要五个依赖：`fastapi`、`uvicorn`、`jinja2`、`httpx` 和 `python-multipart`（各自作用参见课程 1 第 2.2 节）。与后端一样，固定它们的版本。

不需要 SQLAlchemy，也不需要 PostgreSQL 驱动：前端**永远**不需要它们。

`frontend/Dockerfile`：复用后端的文件，只修改端口为 `8080`。

在 `docker-compose.yml` 中添加 `frontend` 服务，要求：

- 从 `frontend/` 目录构建；
- 接收环境变量 `API_BASE_URL`，值为 `http://backend:8000`；
- 在后端之后启动；
- 发布端口 `8080`；
- 将 `frontend/app` 挂载进容器，像后端一样使用 `--reload` 启动 `uvicorn`，以便修改生效时无需重建镜像。

目前前端只需要一个变量 `API_BASE_URL`，而且它不是秘密：直接放进 `environment:` 即可（参见[课程 1 第 1.2 节](https://github.com/Keli-LYU/fullstack-data-application-2026/blob/main/seances/seance-4-webapp/cours/cours1-frontend.md#12-configurer-chaque-service--les-variables-denvironnement)的环境变量部分）。

根据课程 1 的[第 2.6 节](https://github.com/Keli-LYU/fullstack-data-application-2026/blob/main/seances/seance-4-webapp/cours/cours1-frontend.md#26-les-routes-de-pages)和[第 2.4 节](https://github.com/Keli-LYU/fullstack-data-application-2026/blob/main/seances/seance-4-webapp/cours/cours1-frontend.md#24-les-templates-jinja2)，编写 `app/templating.py`、`app/main.py` 和 `templates/base.html`。在 `main.py` 添加首页路由 `GET /`，将其重定向到物品列表 `/items`。

还要编写 `templates/erreur.html`：继承 `base.html`，在一个段落内显示 `{{ message }}`，并提供返回 `/items` 的链接。

最后，将[第 2.8 节](https://github.com/Keli-LYU/fullstack-data-application-2026/blob/main/seances/seance-4-webapp/cours/cours1-frontend.md#28-un-peu-de-css)中的样式表复制到 `static/style.css`。

**检查：**

```bash
docker compose up --build -d
docker compose ps
```

两个服务都应处于 `running` 状态。访问 `http://localhost:8080/static/style.css` 应显示样式表。首页仍会报错：因为 `/items` 路由尚未存在，这是下一步的内容。

---

## 步骤 2 — API 客户端

参考[课程 1 第 2.5 节](https://github.com/Keli-LYU/fullstack-data-application-2026/blob/main/seances/seance-4-webapp/cours/cours1-frontend.md#25-le-client-dapi)编写 `app/api_client.py`：包括 `ApiClient` 类、前三个方法（`list_items`、`get_item`、`create_item`），以及在模块末尾创建的唯一实例 `api_client`。

为 `ApiError` 添加 `messages()` 方法，将错误中的 `detail` 转换为可显示的消息列表。注意：FastAPI 拒绝请求（`422`）时，`detail` 不是字符串，而是一个**错误列表**，每个无效字段对应一个错误。其中包括 `loc`（字段位置，最后一个元素是字段名）和 `msg`（消息）。该方法必须兼容两种情况：普通字符串或列表。在 `/docs` 中调用一个会出错的路由，观察具体格式。

**在编写任何页面之前，先从前端容器内验证。** 先通过 `http://localhost:8000/docs` 创建两三个物品，然后执行：

```bash
docker compose exec frontend python -c "from app.api_client import api_client; print(api_client.list_items())"
```

应看到这些物品。接着做个实验：在 `docker-compose.yml` 中暂时将 `http://backend:8000` 改成 `http://localhost:8000`，重新启动（`docker compose up -d`）并再次执行上述命令。你会得到 `503` 的 `ApiError`，因为前端容器内的 `localhost` 指向前端容器自己。然后改回 `backend`。

---

## 步骤 3 — “物品列表”页面

在 `app/routers/items.py` 中编写 `GET /items` 路由，并编写模板 `templates/items/list.html`。课程的[第 2.6 节](https://github.com/Keli-LYU/fullstack-data-application-2026/blob/main/seances/seance-4-webapp/cours/cours1-frontend.md#26-les-routes-de-pages)和[第 2.4 节](https://github.com/Keli-LYU/fullstack-data-application-2026/blob/main/seances/seance-4-webapp/cours/cours1-frontend.md#24-les-templates-jinja2)包含这两部分内容。在表格上方添加“发布物品”链接，指向创建表单页面 `/items/new`。

然后编写 `GET /items/{item_id}` 路由及模板 `templates/items/detail.html`：显示标题、描述、日租价格、状态，以及返回列表的链接。

**检查：**

1. `http://localhost:8080` 重定向到列表并显示物品；
2. 点击某个物品可打开详情页；
3. `http://localhost:8080/items/9999` 显示“未找到”错误页，状态码为 `404`（在浏览器开发者工具的“网络”选项卡检查）；
4. 通过 `/docs` 创建标题为 `<b>Test XSS</b>` 的物品：列表应将标签原样作为文本显示，而不是显示加粗标题。若标题加粗，说明某处关闭了自动转义：找到它。

---

## 步骤 4 — 创建物品的表单

需要两条路由：

- `GET /items/new` 显示表单（模板 `templates/items/form.html`）；
- `POST /items` 接收表单（`<form method="post" action="/items">`），调用 `api_client.create_item`，然后重定向。

与 API 一样，创建物品时向集合 `/items` 发送 POST。只有显示表单的页面需要独立 URL `/items/new`：它是页面，而不是资源。

表单包含四个字段，对应后端的 `ItemCreate`：`titre`（文本，`required minlength="3"`）、`description`（`<textarea>`）、`tarif_jour`（数字，`required min="0.01" step="0.01"`）、`disponible`（复选框）。

`POST` 路由用 `Form()` 读取这四个字段，构造要发送给 API 的数据，然后：

- 成功时，以 `303` 重定向到新物品的详情页；
- 后端返回 `422` 时，重新显示表单，保留已输入值并展示错误消息列表，响应状态码为 `422`；
- 其他错误让 `ApiError` 继续向上传播，由全局处理器处理。

课程 1 第 2.7 节以预约为例展示此模式：将其应用于创建物品。

需要理解三个要点：

- **复选框。** 勾选时发送 `disponible=on`；**不勾选时什么也不发送**。因此对应参数必须有默认值 `False`。否则 FastAPI 会要求该字段，取消勾选将产生 `422`。
- **路由顺序。** 必须在 `/items/{item_id}` **之前**声明 `/items/new`。反过来，FastAPI 会尝试将 `new` 解析为整数 `item_id`，返回 `422`。这与第 1 次课实验的陷阱相同。
- **`303` 重定向。** 创建成功后刷新页面，不应出现重复物品（若不明白原因，重读课程 1 第 2.7 节）。

在模板中，把错误提示放在表单上方，并用此前输入的内容预填各字段，避免用户丢失输入。还要考虑空描述：空表单字段会以空字符串到达前端，应将其作为“无描述”传给后端。

**检查：**

1. 有效创建操作重定向到新物品详情页；
2. 刷新此页面：只创建了一个物品；
3. 暂时删除 HTML 中 `tarif_jour` 字段的 `min` 属性，输入 `0`：`422` 错误来自**后端**，前端应正确显示它，并保留其他字段内容；
4. 用只有两个字符的标题重复同样检查。

第 3 点演示了课程 1 第 1.1 节的观点：浏览器校验是为了方便用户。即便移除它，后端仍应保护数据。

---

## 步骤 5 — 从详情页预约与取消

完善物品详情页，使其能够管理预约。

**API 客户端。** 为 `ApiClient` 添加三个方法：

- 列出某物品的预约（`GET /reservations`，携带参数 `item_id`）；
- 创建预约（`POST /reservations`）；
- 取消预约（`PATCH /reservations/{id}`，请求体为 `{"statut": "annulee"}`）。

**详情页。** 在物品信息下方显示：

- 该物品的预约列表，包括日期和状态；
- 每条有效预约旁的“取消”按钮：使用 `POST` 表单（不能是链接），提交至 `/reservations/{reservation_id}`，包含两个隐藏字段：`statut`（值为 `annulee`）和物品 ID，以便确定重定向位置；
- 一个“预约”表单，包含两个必填的 `date` 类型字段。

**前端路由。**

- `POST /items/{item_id}/reservations` 创建预约。成功时以 `303` 重定向到物品页面，并显示确认信息。出现 `422` 时重新显示详情页，展示错误消息并保留日期输入。
- `POST /reservations/{reservation_id}` 将状态变更传给后端（HTML 表单无法发送 `PATCH`：前端接收 `POST`，再调用 API 的 `PATCH`），然后以 `303` 重定向到物品页面。如果后端返回 `409`（预约已取消），在物品页显示“此预约已取消。”，而不是错误页。

把这些路由放入新的 router：`app/routers/reservations.py`。

教师会检查以下**约束**：

- `api_client.py` 之外不能调用 `httpx`；
- 前端不能包含业务规则：不要用 Python 检查日期，这是后端的工作；
- 不使用 JavaScript；
- 模板中不能使用 `|safe`；
- 不得硬编码后端地址。

**检查：** 预约一个物品，刷新页面（只能有一条预约）；尝试让结束日期早于开始日期（应显示易读错误）；取消预约，再通过重新提交表单（浏览器“后退”按钮）尝试取消同一预约第二次：应显示“已取消”提示，而不是错误页。

---

## 步骤 6 — 观察局限

通过两个实验为后续内容做准备：

1. **停止后端**：执行 `docker compose stop backend`，然后在浏览器刷新列表。应显示“服务不可用”页面，状态码 `503`，而不是堆栈跟踪。重新启动：`docker compose start backend`。
2. **返回列表。** 物品消失了：后端使用内存存储，重启时内存被清空。前端没有丢失任何内容，因为它本来就不存储数据。

TP 2 正是要解决这个问题：将后端接入 PostgreSQL，并验证只要 API 契约保持一致，**前端就能无需修改继续运行**。

---

## TP 1 结束时需要提交的内容

在小组 Git 仓库中提交：

1. **重新组织后的仓库**：`backend/`、`frontend/`，以及包含两个服务的 `docker-compose.yml`；只需 `docker compose up --build` 即可全部启动。
2. `backend/` 中**第 2 次课的测试无需修改全部通过**。
3. **前端**：列表、详情、创建物品，以及从详情页预约和取消；遵守步骤 5 的约束。

## 进一步探索

- **在没有后端的情况下测试前端。** 使用 FastAPI 的 `TestClient` 和 `monkeypatch`，将 `api_client` 实例的方法替换为返回固定数据或抛出 `ApiError` 的假方法。验证后端 `404` 会生成前端 `404` 页面，创建成功时响应 `303`。
- 为物品列表添加过滤功能（按标题搜索、“仅显示可用物品”）：使用 `GET` 表单，将字段转换成 API 的查询参数 `q` 和 `disponible`。
- 添加物品修改功能（API 侧使用 `PATCH`）：注意 HTML 表单仍使用 `POST`，由 API 客户端调用 `PATCH`。
