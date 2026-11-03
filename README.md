# Docker: СРО 1 и СРО 2

Четыре своих Docker-образа, опубликованных на Docker Hub:

| СРО | Что | Образ | Технологии |
|-----|-----|-------|------------|
| 1 | Сайт №1 — **локальный** (гид «Сапар») | [`abdigani/sapar-local-site`](https://hub.docker.com/r/abdigani/sapar-local-site) | nginx, свой конфиг |
| 1 | Сайт №2 — **глобальный** на AWS («Облачная доска») | [`abdigani/cloud-board`](https://hub.docker.com/r/abdigani/cloud-board) | Python, AWS EC2 |
| 2 | Приложение №1 — **PassKit**, утилита для паролей | [`abdigani/passkit`](https://hub.docker.com/r/abdigani/passkit) | Python, CLI |
| 2 | Приложение №2 — **Docker Quiz**, викторина | [`abdigani/docker-quiz`](https://hub.docker.com/r/abdigani/docker-quiz) | Go, multi-stage, `FROM scratch` |

Все образы собраны под **linux/amd64 и linux/arm64**: запускаются на Windows/Linux-ПК,
на Mac с Apple Silicon и на сервере AWS.

---

## Быстрая проверка

Нужен только установленный Docker. Клонировать репозиторий не обязательно — образы скачаются с Docker Hub.
Исходники: `git clone https://github.com/gon4idon4i/docker-sro.git`

```bash
# СРО 2 — приложение 1: меню утилиты для паролей
docker run --rm -it abdigani/passkit:1.0

# СРО 2 — приложение 2: викторина
docker run --rm -it abdigani/docker-quiz:1.0

# СРО 1 — сайт 1, потом открыть http://localhost:8081
docker run -d --name sapar -p 8081:80 abdigani/sapar-local-site:1.0

# СРО 1 — сайт 2, потом открыть http://localhost:8082
docker run -d --name board -p 8082:8080 abdigani/cloud-board:1.0
```

Глобальная версия сайта 2 на AWS: **http://__AWS_IP__** (адрес появится после деплоя)

---

## СРО 1. Два сайта: локальный и глобальный

### Сайт №1 — локальный, через Docker

`sro1-websites/local-site/` — одностраничный гид «Сапар» по пяти местам Казахстана.
Отдаётся nginx'ом из контейнера, работает только на своём компьютере (`localhost`).

Что сделано в образе, кроме копирования HTML:

- стандартный `default.conf` удалён и заменён своим [`nginx.conf`](sro1-websites/local-site/nginx.conf);
- gzip-сжатие и кэширование статики на 7 дней;
- своя страница `404.html`;
- служебный адрес `/health` и `HEALTHCHECK` в Dockerfile — в `docker ps` видно `(healthy)`;
- `server_tokens off` — nginx не показывает свою версию в заголовках.

```bash
cd sro1-websites/local-site
docker compose up -d --build      # сборка и запуск
docker ps                         # STATUS: Up ... (healthy)
curl localhost:8081/health        # ok
docker compose down               # остановка
```

### Сайт №2 — глобальный, через AWS

`sro1-websites/global-site/` — «Облачная доска»: веб-сервер на Python без внешних
библиотек. На странице:

- **«Где я запущен»** — имя контейнера, ОС, аптайм, счётчик визитов. Если сервер
  работает на AWS EC2, через сервис метаданных (IMDSv2) подтягиваются `instance-id`,
  тип инстанса и зона доступности — так видно, что сайт действительно в облаке;
- **гостевая книга** — сообщения сохраняются в том `/data` и переживают перезапуск контейнера.

API: `GET /api/info`, `GET|POST /api/notes`, `GET /health`. Сервер работает не от root.

Локальная проверка перед деплоем:

```bash
cd sro1-websites/global-site
docker compose up -d --build      # http://localhost:8082
```

#### Деплой на AWS EC2

1. AWS Console → **EC2** → **Launch instance**.
2. Name: `cloud-board`, AMI: **Amazon Linux 2023**, тип: **t3.micro** (Free Tier).
3. Key pair — создать или выбрать (нужен только для SSH).
4. Network settings → **Allow HTTP traffic from the internet** (порт 80).
5. Advanced details → **User data** — вставить содержимое
   [`aws/user-data.sh`](sro1-websites/global-site/aws/user-data.sh).
   Скрипт сам ставит Docker и запускает образ с Docker Hub на 80 порту.
6. **Launch instance**, подождать 1–2 минуты, открыть `http://<Public IPv4 address>`.

Плашка «AWS EC2» на странице и `instance-id` подтверждают, что сайт работает на сервере Amazon.

Проверка по SSH (необязательно):

```bash
ssh -i key.pem ec2-user@<IP>
docker ps
docker logs cloud-board
```

> После сдачи инстанс лучше остановить (**Instance state → Stop**), чтобы не тратить Free Tier.

---

## СРО 2. Два приложения в Docker (не сайты)

### Приложение №1 — PassKit

`sro2-apps/passkit/` — консольная утилита для работы с паролями. Работает в двух режимах.

**Интерактивное меню** (нужны флаги `-it`):

```bash
docker run --rm -it abdigani/passkit:1.0
```

```
  ╔═══════════════════════════════╗
  ║   PassKit · пароли в Docker   ║
  ╚═══════════════════════════════╝

  1 сгенерировать пароль   2 парольная фраза
  3 проверить пароль       4 хэш строки
  0 выход
```

**Команды** — аргументы после имени образа передаются в программу (`ENTRYPOINT`):

```bash
docker run --rm abdigani/passkit:1.0 gen -l 20 -n 3      # 3 пароля по 20 символов
docker run --rm abdigani/passkit:1.0 phrase -w 5         # tau-kar-shubat-shana-kobyz-75
docker run --rm abdigani/passkit:1.0 check qwerty123     # оценка стойкости
docker run --rm abdigani/passkit:1.0 hash hello -a md5   # 5d41402abc4b2a76b9719d911017c592
docker run --rm abdigani/passkit:1.0 --help
```

Пример проверки пароля:

```
  Длина:     9
  Энтропия:  0.0 бит
  Перебор:   ~меньше минуты
  Оценка:    СЛАБЫЙ
   - пароль есть в списке самых популярных
   - сделайте длину от 12 символов
```

Пароли генерируются модулем `secrets` (криптостойкий генератор), парольные фразы
собираются из казахских слов латиницей. Оценка стойкости — по энтропии и времени перебора
при 10 млрд попыток в секунду. Контейнер работает от пользователя `kit`, не от root.

### Приложение №2 — Docker Quiz

`sro2-apps/docker-quiz/` — викторина из 15 вопросов по Docker и Linux на Go.
Каждый раз задаёт вопросы в случайном порядке и объясняет правильный ответ.

```bash
docker run --rm -it abdigani/docker-quiz:1.0          # 10 вопросов
docker run --rm -it abdigani/docker-quiz:1.0 -n 5     # 5 вопросов
docker run --rm abdigani/docker-quiz:1.0 -list        # все вопросы с ответами
```

Образ собран в два этапа ([Dockerfile](sro2-apps/docker-quiz/Dockerfile)):

1. `golang:1.23-alpine` компилирует статический бинарник, вопросы вшиваются в него через `go:embed`;
2. финальный образ `FROM scratch` — пустой, в нём только этот бинарник.

В итоге образ весит **~2.8 МБ** против ~79 МБ у образа на Python.

---

## Размеры образов

| Образ | Базовый | Размер |
|-------|---------|--------|
| sapar-local-site | nginx:1.27-alpine | 76 МБ |
| cloud-board | python:3.12-alpine | 79 МБ |
| passkit | python:3.12-alpine | 79 МБ |
| docker-quiz | scratch | 2.8 МБ |

---

## Сборка и публикация на Docker Hub

Один скрипт собирает все образы под две архитектуры и отправляет их на Docker Hub:

```bash
docker login
DOCKER_USER=abdigani ./scripts/publish.sh
```

Внутри для каждого образа выполняется:

```bash
docker buildx build --platform linux/amd64,linux/arm64 \
  -t abdigani/<образ>:1.0 -t abdigani/<образ>:latest --push <папка>
```

| Часть | Зачем |
|-------|-------|
| `buildx build` | сборщик с поддержкой нескольких платформ |
| `--platform linux/amd64,linux/arm64` | образ под Intel/AMD и под ARM (Apple Silicon, AWS Graviton) |
| `-t логин/образ:1.0` | имя на Docker Hub и версия |
| `--push` | сразу отправить в репозиторий |

---

## Структура репозитория

```
docker-sro/
├── sro1-websites/
│   ├── local-site/          # сайт 1: nginx + свой конфиг
│   │   ├── html/            #   index.html, 404.html, style.css
│   │   ├── nginx.conf
│   │   ├── Dockerfile
│   │   └── docker-compose.yml
│   └── global-site/         # сайт 2: Python-сервер для AWS
│       ├── app.py
│       ├── static/index.html
│       ├── aws/user-data.sh #   автозапуск на EC2
│       ├── Dockerfile
│       └── docker-compose.yml
├── sro2-apps/
│   ├── passkit/             # приложение 1: утилита для паролей (Python)
│   └── docker-quiz/         # приложение 2: викторина (Go, FROM scratch)
├── scripts/publish.sh       # сборка amd64+arm64 и push на Docker Hub
└── screenshots/
```

---

## Очистка

```bash
docker rm -f sapar board
docker rmi abdigani/sapar-local-site:1.0 abdigani/cloud-board:1.0 \
           abdigani/passkit:1.0 abdigani/docker-quiz:1.0
```

## Автор

Букебаев Әбдіғани · GitHub: [`gon4idon4i`](https://github.com/gon4idon4i) · Docker Hub: [`abdigani`](https://hub.docker.com/u/abdigani)
