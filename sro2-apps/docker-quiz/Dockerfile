# Приложение №2: викторина на Go, multi-stage сборка
# --- этап 1: компиляция ---
FROM --platform=$BUILDPLATFORM golang:1.23-alpine AS build
ARG TARGETOS TARGETARCH
WORKDIR /src
COPY go.mod main.go questions.json ./
# Статический бинарник без libc, кросс-компиляция под платформу образа
RUN CGO_ENABLED=0 GOOS=$TARGETOS GOARCH=$TARGETARCH go build -ldflags="-s -w" -o /quiz .

# --- этап 2: пустой образ, внутри только бинарник ---
FROM scratch

LABEL org.opencontainers.image.title="docker-quiz" \
      org.opencontainers.image.description="СРО 2: консольная викторина по Docker и Linux, образ FROM scratch"

COPY --from=build /quiz /quiz
USER 65534:65534
ENTRYPOINT ["/quiz"]
