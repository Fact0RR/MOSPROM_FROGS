package handlers

import (
	"database/sql"
	"encoding/json"
	"errors"
	"jabki/internal/database"

	"github.com/gofiber/fiber/v2"
	"github.com/google/uuid"
	"github.com/sirupsen/logrus"
)

type Chat struct {
	db     *sql.DB
	logger *logrus.Logger
}

func NewChat(db *sql.DB, logger *logrus.Logger) *Chat {
	return &Chat{
		db:     db,
		logger: logger,
	}
}

type createChatIn struct {
	Name string `json:"name"`
}

type createChatOut struct {
	ChatID int `json:"chat_id"`
}

func (ch *Chat) CreateHandler(c *fiber.Ctx) error {
	userUUID := c.Locals("uuid").(uuid.UUID)
	var chatIn createChatIn
	var err error

	if err = json.Unmarshal(c.Body(), &chatIn); err != nil {
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{
			"error":   "Invalid JSON format",
			"details": err.Error(),
		})
	}

	chatID, err := database.CreateChat(ch.db, chatIn.Name, userUUID.String(), ch.logger)
	if err != nil {
		if errors.Is(err, database.ErrUserNotFound) {
			return c.Status(fiber.StatusNotFound).JSON(fiber.Map{
				"error":   "User not found",
				"details": err.Error(),
			})
		}
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{
			"error":   "Error creating chat",
			"details": err.Error(),
		})
	}

	return c.Status(fiber.StatusCreated).JSON(createChatOut{
		ChatID: chatID,
	})
}

func (ch *Chat) GetHandler(c *fiber.Ctx) error {
	userUUID := c.Locals("uuid").(uuid.UUID)

	chats, err := database.GetChats(ch.db, userUUID.String(), ch.logger)
	if err != nil {
		ch.logger.WithFields(logrus.Fields{
			"user_uuid": userUUID,
			"error":     err,
		}).Error("failed to get chats from database")

		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error":   "Failed to retrieve chats",
			"details": err.Error(),
		})
	}

	// Если чатов нет, возвращаем пустой массив вместо null
	if chats == nil {
		chats = []database.Chat{}
	}

	ch.logger.WithFields(logrus.Fields{
		"user_uuid":  userUUID,
		"chat_count": len(chats),
	}).Debug("chats retrieved successfully")

	return c.JSON(chats)
}
