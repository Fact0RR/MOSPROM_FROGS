package handlers

import (
	"database/sql"
	"jabki/internal/database"
	"jabki/internal/web/ws"
	"strconv"

	"github.com/gofiber/fiber/v2"
	"github.com/gofiber/websocket/v2"
	"github.com/google/uuid"
	"github.com/sirupsen/logrus"
)

func SupportHandler(db *sql.DB, logger *logrus.Logger) fiber.Handler {
	return websocket.New(func(c *websocket.Conn) {
		// Получаем chat_id из параметров пути
		chatID := c.Params("chat_id")
		userUUID := c.Locals("uuid").(uuid.UUID).String()

		// Добавляем соединение в хранилище
		ws.AddConnection(chatID, userUUID, c)
		defer ws.RemoveConnection(chatID, userUUID)

		logger.Infof("WebSocket соединение установлено для чата: %s, пользователь: %s\n", chatID, userUUID)

		// Отправляем пользователю подтверждение подключения
		c.WriteJSON(map[string]string{
			"type": "connection_established",
			"uuid": userUUID,
		})

		for {
			var msg ws.Message

			// Читаем сообщение от клиента
			err := c.ReadJSON(&msg)
			if err != nil {
				logger.Errorf("Ошибка чтения сообщения: %v\n", err)
				break
			}

			// Выводим сообщение в консоль
			logger.Debugf("Чат %s | Пользователь %s: %s\n", chatID, userUUID, msg.Message)
			chatIDint, err := strconv.Atoi(chatID)
			if err != nil {
				logger.Error("chatID не число:", err)

			}

			err = database.CreateSupport(db, userUUID, chatIDint, msg.Message, logger)
			if err != nil {
				logger.Error("Ошибка записи сообщений в тех. поддержке")
			}

			// Отправляем сообщение всем пользователям в чате, кроме отправителя
			ws.BroadcastMessage(chatID, userUUID, msg)
		}
	})
}
