FROM golang:1.23-alpine AS builder

# Устанавливаем goose
RUN go install github.com/pressly/goose/v3/cmd/goose@latest

FROM alpine:latest

# Устанавливаем postgresql-client для проверки готовности БД
RUN apk --no-cache add postgresql-client

# Копируем goose из builder stage
COPY --from=builder /go/bin/goose /usr/local/bin/goose

# Копируем миграции в контейнер
COPY . /migrations

WORKDIR /migrations

# Команда которая ждет готовности БД и затем запускает миграции
CMD ["sh", "-c", "echo 'Waiting for PostgreSQL...'; until pg_isready -h postgres -p 5432; do sleep 2; done; echo 'Running migrations...'; goose postgres \"postgres://app:app123@postgres:5432/app?sslmode=disable\" up"]