package handlers

import (
	"database/sql"
	"jabki/internal/database"
	"strconv"
	"strings"

	"github.com/gofiber/fiber/v2"
	"github.com/google/uuid"
	"github.com/sirupsen/logrus"
)

type History struct {
	db     *sql.DB
	logger *logrus.Logger
}

func NewHistory(db *sql.DB, logger *logrus.Logger) *History {
	return &History{
		db:     db,
		logger: logger,
	}
}

func (hh *History) Handler(c *fiber.Ctx) error {
	uuid := c.Locals("uuid").(uuid.UUID)
	chatIDStr := c.Params("chat_id")

	chatID, err := strconv.Atoi(chatIDStr)
	if err != nil {
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{
			"error": "Invalid chat ID format",
		})
	}

	isCorresponds, err := database.CheckChat(hh.db, uuid.String(), chatID, hh.logger)
	if err != nil || !isCorresponds {
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{
			"error": "Chat ID is not corresponds to user uuid",
		})
	}

	messages, err := database.GetHistory(hh.db, chatID, hh.logger)
	if err != nil {
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{
			"error":   "Error in database",
			"details": err.Error(),
		})
	}

	authHeader := c.Get("Authorization")
	const prefix = "Token "
	if strings.HasPrefix(authHeader, prefix) {
		var messageToModel messageOutToModel
		for _, message := range messages {
			messageToModel.Messages = append(messageToModel.Messages, 
				messageModel{
					Role: "user",
					Content: message.Question,
				},
				messageModel{
					Role: "assistant",
					Content: message.Answer,
				},
			)
		}
		return c.JSON(messageToModel)
	}

	return c.JSON(messages)
}

type messageOutToModel struct {
	Messages []messageModel `json:"messages"`
}

type messageModel struct {
	Role    string `json:"role"`
	Content string `json:"content"`
}
