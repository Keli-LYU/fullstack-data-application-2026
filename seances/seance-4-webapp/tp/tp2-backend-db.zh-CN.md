# TP 2 — 第 4 次课：将后端连接到 PostgreSQL

## 你将完成什么

完成 [TP 1](tp1-frontend.zh-CN.md) 时，应用已有两个服务：提供 HTML 页面的前端，以及将所有数据保存在内存中的后端。本实验将添加第三个服务 **PostgreSQL**，并将后端重构为分层结构，使其能够读写数据库中的数据。

前端应该几乎不需要改变：它只认识 API。每一次不得不进行的前端修改，都揭示了 API 契约的变化；请记录这些变化。

本实验是**提供指导，而非逐行照抄**：教师会说明要构建什么、按什么顺序构建，以及如何验证。代码由你自己编写，可参考[课程 2](https://github.com/Keli-LYU/fullstack-data-application-2026/blob/main/seances/seance-4-webapp/cours/cours2-backend-db.md)，其中包含所需的全部要素。唯一直接给出的完整命令，是需要在终端中执行的命令。

## 实验目标

完成后，你应能够：

- 将 FastAPI 后端组织为分层结构（routers／services／repositories／models／schemas）；
- 配置 SQLAlchemy，并为每个请求注入一个会话；
- 创建、审阅和修正 Alembic 迁移；
- 将全部配置提取到环境变量中；
- 通过一次 `docker compose up` 编排后端、前端和数据库，并选择迁移的应用方式；
- 从 SQL 日志中识别 N+1 问题并修复；
- 实现包含业务规则的完整纵向功能，并按审查清单进行复核。

这是本模块最长的实验。**这里的成果将成为你项目的基础**：请认真完成，接下来三次课都会继续使用它。

## 前提条件

- 完成第 1、2 次课实验。
- 完成本次课 TP 1：仓库已分为 `backend/` 和 `frontend/`。
- 已启动 Docker Desktop。

---

## 步骤 0 — 目标目录结构

从 TP 1 的仓库继续。`frontend/` 不变；重构 `backend/` 为分层结构。目标如下：

```text
gearshare/
├── backend/
│   ├── alembic/
│   ├── alembic.ini
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   └── exceptions.py
│   │   ├── db/
│   │   │   └── session.py
│   │   ├── api/
│   │   │   └── deps.py
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── repositories/
│   │   ├── services/
│   │   └── routers/
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/          # TP 1 的前端，不变
├── .env.example
├── .env               # ← 放入 .gitignore
├── .gitignore
└── docker-compose.yml
```

创建空目录，然后：

1. **依赖。** 在 `backend/requirements.txt` 中添加后端现在需要的四个库：SQLAlchemy 2.0、PostgreSQL 驱动 `psycopg`（第 3 版，包含 `binary` extra）、Alembic 和 `pydantic-settings`。与 FastAPI 一样，固定主版本。保留第 2 次课添加的 `pytest` 和 `httpx`。
2. **`.gitignore`。** 至少排除 `.env`、Python 和 pytest 缓存，以及虚拟环境。

**现在就完成 `.gitignore`。** 第 4 次课提交进 Git 的 `.env`，会使秘密一直暴露在 Git 历史中，直到最终提交作业。检查：

```bash
echo "TEST=1" > .env
git status          # .env 绝不能出现
```

---

## 步骤 1 — 配置与会话

需要编写三个文件：

- **`app/core/config.py`**：用 `pydantic-settings` 编写配置类，至少读取数据库 URL 和是否显示 SQL 的布尔选项（默认关闭）。在模块级别只实例化一次。
- **`app/db/session.py`**：根据该配置创建 SQLAlchemy engine 和会话工厂。启用失效连接检查（`pool_pre_ping`）。
- **`app/api/deps.py`**：编写依赖 `get_db`，为每个请求打开一个会话；一切正常时提交，发生异常时回滚，并且**无论如何都要关闭**。还要提供别名 `DbSession`，避免到处重复 `Depends(get_db)`。

然后编写并提交 **`.env.example`**：列出全部必要变量及开发用值，包括 `postgres` 镜像要求的三个变量（`POSTGRES_USER`、`POSTGRES_PASSWORD`、`POSTGRES_DB`）、格式为 `postgresql+psycopg://utilisateur:motdepasse@hote:port/base` 的 `DATABASE_URL`，以及 `SQL_ECHO`。复制它：

```bash
cp .env.example .env
```

**检验理解：** `DATABASE_URL` 的主机应写 `db` 还是 `localhost`？为什么？如果不确定，重读第 0 次课的 Docker 网络部分。

**检查点：** 在 `get_db` 中，如果路由在向会话添加一个对象之后抛出异常，会发生什么？该对象会进入数据库吗？写下答案，在步骤 4 验证。

---

## 步骤 2 — 模型

编写 `app/models/base.py`，然后编写 `user.py`、`item.py` 和 `reservation.py`，**严格对应**第 3 次课的 SQL 模式。课程中的 `Item` 模型可作为语法参考；另外两个模型需要完整自行编写。

不能遗漏的要点：

- 所有外键都设置 `index=True`；
- `tarif_jour` 使用 `Numeric(8, 2)`（金额绝不能用 `Float`）；
- `created_at` 使用 `DateTime(timezone=True)`，并设置服务器端默认值；
- `User.email` 唯一；
- 在 `__table_args__` 中添加第 3 次课的 `CHECK` 约束（价格为正、日期关系合理、状态合法），并为约束**命名**；
- 每个关联的两端都定义 `relationship(back_populates=...)`。

最后，确保 `app/models/__init__.py` 导入 `Base` 和三个模型。这个文件不是装饰：重读课程中的 Alembic 部分，理解缺少它会发生什么。

---

## 步骤 3 — Alembic

在 `backend/` 中初始化 Alembic：

```bash
alembic init alembic
```

然后在 `alembic/env.py` 中将它与应用连接起来：

- 连接 URL 必须来自配置，**不能**来自 `alembic.ini`；
- `target_metadata` 必须指向 `Base` 的元数据，并确保模型已导入。

在 `alembic.ini` 中将 `sqlalchemy.url` 留空：此文件会提交进 Git，密码不该出现在这里。

为了在容器中运行 Alembic，暂时向 `docker-compose.yml` 添加 `db` 服务（步骤 6 会进一步完善；课程提供了示例）。只启动数据库，再生成迁移：

```bash
docker compose up -d db
docker compose run --rm backend alembic revision --autogenerate -m "schema initial"
```

> 💡 如果在本机而非容器中执行 Alembic，`DATABASE_URL` 应指向 `localhost` 而非 `db`，并且需要发布数据库端口。最简单的办法是全部在容器内完成。

**打开 `alembic/versions/` 中生成的文件，从头到尾阅读。** 检查：

- [ ] 三张表按正确顺序创建（先 `users`，后 `items`）；
- [ ] 外键存在，且 `ondelete` 正确；
- [ ] `CHECK` 约束存在，并具有名称；
- [ ] 外键索引已创建；
- [ ] `downgrade()` 按相反顺序删除全部内容。

如果有遗漏，不要直接修迁移：应修正**模型**，删除迁移文件后重新生成。

应用迁移、检查，再测试升级与回退：

```bash
docker compose run --rm backend alembic upgrade head
docker compose exec db psql -U gearshare -d gearshare -c "\dt"
docker compose exec db psql -U gearshare -d gearshare -c "\d items"
docker compose run --rm backend alembic downgrade base
docker compose run --rm backend alembic upgrade head
```

整个循环必须无错误完成。如果 `downgrade` 失败，现在就修复迁移：不可逆的迁移会成为贯穿整个项目的问题。

### 3 bis — 重命名的陷阱

这是一个简短但重要的练习。先用 `psql` 向数据库插入两个物品（外键要求先有一个用户）。然后在 `Item` 模型中将列 `tarif_jour` 重命名为 `prix_jour`，生成迁移：

```bash
docker compose run --rm backend alembic revision --autogenerate -m "renommage tarif_jour"
```

阅读生成的迁移。它具体做了什么？如果应用它，两个物品会发生什么？写下预测，然后**手动修正迁移**，使其无损重命名列（课程给出了应使用的 Alembic 操作）。不要忘记 `downgrade()`。

应用后，验证价格仍在：

```bash
docker compose run --rm backend alembic upgrade head
docker compose exec db psql -U gearshare -d gearshare -c "SELECT id, titre, prix_jour FROM items;"
```

随后**恢复原状**（执行 `downgrade -1`，删除迁移文件，将模型改回 `tarif_jour`）：这只是练习，保留原来的名称。

在 `docs/review-migrations.md` 中记录观察结果：生成的迁移、你的预测和修正。此文件属于提交材料。

---

## 步骤 4 — 完整的纵向功能：`items`

逐层实现 `items` 资源，**严格按以下顺序**，每个文件检查完再继续：

1. **`app/core/exceptions.py`**：定义业务异常基类，并按错误类型定义子类——资源不存在、业务冲突、访问被拒绝。它们携带易读消息，但都不应了解 HTTP。
2. **`app/schemas/item.py`**：创建 schema、修改 schema（所有字段可选），以及可从 SQLAlchemy 对象构建的读取 schema。
3. **`app/repositories/item.py`**：定义 `ItemRepository` 类，支持获取单个物品、列表查询（分页、文本搜索、按可用性过滤）、添加和删除。**不能有 `commit()`**：原因见课程。
4. **`app/services/item.py`**：定义使用 repository 的 `ItemService` 类，物品不存在时抛出“未找到”异常。暂时没有其他规则（所有权检查将在第 5 次课引入）。
5. **`app/routers/items.py`**：实现 CRUD 的五条路由，设置 `response_model`，使用第 1 次课的状态码。router 只负责转换：输入 schema、调用 service、输出 schema。

在 `app/main.py` 中注册 router，保留 `/health` 路由，并把业务异常映射成 HTTP 状态码。自行选择每个路由使用 `try`／`except`，还是使用全局异常处理器。在 `docs/review-migrations.md` 中用一句话说明选择理由。

**检查：**

```bash
docker compose up -d --build
curl -X POST http://localhost:8000/items \
  -H "Content-Type: application/json" \
  -d '{"owner_id": 1, "titre": "Vélo de ville", "tarif_jour": 8.5}'

curl http://localhost:8000/items
curl -i http://localhost:8000/items/9999          # 预期：404，响应体为 {"detail": "..."}
docker compose exec db psql -U gearshare -d gearshare -c "SELECT * FROM items;"
```

最后一条命令最关键：**数据真的存入数据库了吗？** 然后重启所有服务，再执行 `GET /items`：数据必须保留。

```bash
docker compose restart
curl http://localhost:8000/items
```

最后回到步骤 1 的检查点：制造一次添加后的错误（例如 POST 时提供不存在的 `owner_id`），检查数据库，确认没有写入任何数据。得到的 HTTP 状态码是什么？是否合适？如果是 `500`，思考应该由哪一层发现这种情况。

---

## 步骤 5 — 找出 N+1 问题

在 `.env` 中设置 `SQL_ECHO=true`，重启后端。

扩展物品的返回表示，加入其所有者（前端列表页可显示）。不添加新路由：只是丰富 `items` 资源，现在 `GET /items` 多返回一个 `owner` 字段。

为此，创建一个简化的所有者读取 schema，只包含 ID 和显示名称，将其作为物品读取 schema 的一个字段。这个 schema **既不能包含 `email`，也不能包含 `password_hash`**：绝不要在另一资源的表示中暴露完整用户。

用一条 SQL 命令插入约二十个物品（提示：`INSERT ... SELECT` 配合 `generate_series`），调用 `GET /items?limit=50`，并**统计日志中的 SQL 查询数量**：

```bash
curl -s "http://localhost:8000/items?limit=50" > /dev/null
docker compose logs --since 30s backend | grep -c "SELECT"
```

只显示一页会执行多少次查询？它们从哪里来？这里的 N+1 隐藏在序列化中：找出哪一行代码触发了它，即便你没有编写循环。在 `ItemRepository` 的列表方法中修复（课程给出了应使用的加载选项），然后重新统计。

在 `docs/review-migrations.md`（或 `docs/notes-perf.md`）中记录修复前后的两个数字。

> 提交前不要忘记恢复 `SQL_ECHO=false`：持续输出 SQL 日志会使日志难以使用，而且在生产环境中可能包含个人数据。

---

## 步骤 6 — 三服务 Compose 与启动时迁移

### 6.1. 三个服务

完善 `docker-compose.yml`：

- `db` 服务通过 `.env` 变量替换接收凭据，将数据保存在命名卷中，并配置 `healthcheck`；
- `backend` 服务使用 `env_file: .env`，不仅要等数据库启动，还要等它**准备就绪**；
- `frontend` 服务保持 TP 1 的配置：**不使用 `env_file`**，只需要 `API_BASE_URL`（原因参见[课程 1](https://github.com/Keli-LYU/fullstack-data-application-2026/blob/main/seances/seance-4-webapp/cours/cours1-frontend.md)）。

### 6.2. 自行选择：如何应用迁移？

此前一直手动运行 `alembic upgrade head`。检查作业时，教师只会执行 `git clone`、`cp .env.example .env`、`docker compose up`，不会再执行其他命令。因此迁移必须**自动应用**，并且在 API 接收第一个请求之前完成。

课程介绍了两种方法。**由小组自行选择并说明理由**：

| | 方案 1：`entrypoint.sh` | 方案 2：`migrate` 服务 |
|---|---|---|
| 命令放在哪里 | 后端镜像中，在 `uvicorn` 之前执行 | 独立 Compose 服务中，基于同一镜像构建 |
| 谁等待谁 | 后端等待数据库 | `migrate` 等待数据库，后端等待 `migrate` 完成 |
| 需要编写什么 | shell 脚本和使用它的 `Dockerfile` | 一个额外服务，以及 `depends_on` 中正确的 `condition` |

决定之前，在 `docs/choix-migrations.md` 中书面回答：

1. **第二次**执行 `docker compose up`，数据库已是最新状态时，会发生什么？
2. 如果迁移失败，`docker compose ps` 和日志中会看到什么？后端还会启动吗？
3. 生产环境中，如果三个后端实例同时启动，连接到尚未迁移的数据库，会发生什么？（无需在本地测试：发布的 `8000` 端口会阻止启动多个实例。）
4. 开发期间后端使用 `--reload`：所选方案仍能正常工作吗？

随后用几行文字写明选择及理由。没有错误的选择，只有缺乏理由的回答。

### 6.3. 从零验证

```bash
docker compose down -v          # ⚠️ 同时删除卷：数据库将从空状态重新开始
docker compose up --build
```

一次 `up` 应完成：启动 Postgres，等待就绪，应用迁移，启动 API，启动前端。观察日志顺序确认，然后执行：

```bash
docker compose ps -a
docker compose exec db psql -U gearshare -d gearshare -c "SELECT * FROM alembic_version;"
```

如果必须按特定顺序运行多条命令才能工作，说明还没有完成。

### 6.4. 前端使用真实数据库

打开 `http://localhost:8080`，重新执行 TP 1 的流程：列表、详情、创建物品。

- **列表**和**详情**应无需修改前端就能运行：读取契约没有变化（或几乎没有：注意变成 `Numeric` 后，`tarif_jour` 如何显示）。
- **创建**会失败，提示“owner_id : Field required”。契约改变了：物品现在必须有所有者。TP 1 的前端会正确显示后端的 `422` 错误，这正是预期行为。

采取**临时**修正：在数据库插入演示用户，再让前端发送 `owner_id`，在创建路由中固定该值。

```bash
docker compose exec db psql -U gearshare -d gearshare \
  -c "INSERT INTO users (email, display_name, password_hash) VALUES ('demo@esiee.fr', 'Démo', 'x');"
```

在这个值旁添加注释 `# TODO séance 5`：第 5 次课中，所有者将是登录用户，由后端从令牌推导，此字段会从表单中消失。

最后重启所有服务（`docker compose restart`），重新加载列表：**物品仍然存在**。这就是与 TP 1 步骤 6 的区别。

在 `docs/review-migrations.md` 中记录对 `frontend/` 的每项必要修改，以及导致修改的契约变化。

---

## 步骤 7 — `reservations` 纵向功能

此前已逐层构建 `items`。现在按同样方式构建 `reservations`，**严格遵循** `items` 的架构：同样的命名约定、分层划分和业务异常。`Reservation` 模型已在步骤 2 创建。

### 7.1. 契约

要求实现的路由：

| 方法与路径 | 作用 | 预期状态码 |
|---|---|---|
| `POST /reservations` | 创建预约 | `201`、`404`、`409`、`422` |
| `GET /reservations` | 列表，可按 `item_id` 过滤，支持分页 | `200` |
| `GET /reservations/{id}` | 详情 | `200`、`404` |
| `PATCH /reservations/{id}` | 取消，请求体 `{"statut": "annulee"}` | `200`、`404`、`409` |

### 7.2. 业务规则

全部业务规则都放在 service 中，不能放在其他地方：

- 物品必须存在，否则“未找到”；
- 物品必须可用，否则“冲突”；
- 此物品不能有任何**有效**预约与请求时间段重叠，否则“冲突”；
- 只能取消状态为 `active` 的预约，否则“冲突”。

重叠检测是一项查询，因此放在 repository 中，由 service 调用。编写之前，先在纸上画出现有时间段与请求时间段的五种关系：**完全在前、完全在后、起始部分重叠、结束部分重叠、完全包围**。然后找出最简单的条件，使它恰好对三种冲突情况返回“真”。提示：只需两次比较，从**不冲突**的情况入手更容易推理。

还要作出决定并记录：两个首尾相接的预约（一个在另一个开始的当天结束）是否冲突？查询必须体现这个决定。

### 7.3. 验证

在 `docs/cas-tests-chevauchement.md` 中写出这五种情况（加上首尾相接的情况），每种都列出现有时间段、请求时间段和预期状态码。然后通过 `http://localhost:8000/docs` 或 `curl` 逐一执行，并记录实际结果。这个文件就是 service 的测试计划：课程 2 演示了如何用 `parametrize` 在测试数据库上自动执行这些测试。

还要检查迁移：如果 `Reservation` 模型相较初始模式发生变化，就生成迁移、审阅它，并测试其 `downgrade()`。

### 7.4. 复核

将 `reservations` 纵向功能交给组内另一对同学审查（或第二天自己重新冷静审阅），填写 `docs/review-couches.md`：

| 检查点 | OK／KO（通过／不通过） | 我所做的修正 |
|---|---|---|
| router 中没有 SQL 或 SQLAlchemy 查询 | | |
| service 中没有 `HTTPException`（只有业务异常） | | |
| repository 中没有 `commit()` | | |
| 4 条路由都配置 `response_model` | | |
| 读取 schema 从 SQLAlchemy 对象构建，不含内部字段 | | |
| 重叠查询涵盖全部五种情况，包括完全包围 | | |
| SQL 查询中没有 f-string | | |
| `GET /reservations` 没有 N+1 问题（如果加载了 `item` 关联） | | |
| 已审阅迁移并测试 `downgrade()` | | |
| 没有无理由添加的依赖 | | |

必须严格审查重叠查询：这是本实验最常见的错误。如果只检查“请求的开始时间是否落在现有时间段内”，就会漏掉新预约**完全包围**现有预约的情况。

### 7.5. 前端

TP 1 编写的物品详情页应仍能预约和取消。但后端现在会在时间段已被占用或物品不可用时返回 `409`，而前端此前只处理 `422`：将 `409` 加入预约表单显示的错误处理（课程 1 展示了方法）。在浏览器中验证：冲突预约应显示清晰提示，而不是错误页。

---

## TP 2 结束时需要提交的内容

在项目 Git 仓库中提交：

1. **干净克隆后 `docker compose up` 即可运行**：`git clone`、`cp .env.example .env`、`docker compose up` → API 在 `:8000`、前端在 `:8080`，数据库自动完成迁移且可访问。
2. **分层后端**：`models/`、`schemas/`、`repositories/`、`services/`、`routers/`，至少完整实现 `items` 和 `reservations` 资源。
3. `alembic/versions/` 中的 **Alembic 迁移**，且 `downgrade()` 已测试。
4. **已提交 `.env.example`，仓库中没有 `.env`。** 教师会检查 Git 历史。
5. **TP 1 的前端已连接真实数据库**：列表、详情、创建物品、预约和取消均可用，且数据在重启后保留。
6. **`docs/choix-migrations.md`**：步骤 6.2 四个问题的回答、所选方案（`entrypoint.sh` 或 `migrate` 服务）及理由。
7. **`docs/review-couches.md`**：`reservations` 纵向功能的审查和已做的修正。
8. **`docs/review-migrations.md`**：列重命名的观察、异常映射方案的选择、N+1（修复前后两个数字），以及契约变化导致的前端修改。
9. **`docs/cas-tests-chevauchement.md`**：重叠情况、预期状态码和实际结果。

## 进一步探索

- **将第 2 次课的测试套件接入测试数据库**：创建 `gearshare_test`，添加课程 2 的 `engine`、`db` 和 `client` fixtures，将原来的内存重置改为事务回滚，并验证第 2 次课的契约测试**无需修改**即可通过。随后将 `docs/cas-tests-chevauchement.md` 自动化为针对 `ReservationService` 的参数化测试。这是第 5 次课的首项任务，可以提前进行。
- 在一个分支中实现步骤 6 未选择的**另一种**迁移方案，比较四个问题下的表现。
- 编写 `seed.py` 脚本填充演示数据，并通过 `docker compose run --rm backend python -m app.seed` 运行。
- 实现记录每个请求耗时的中间件，找出最慢的路由。
