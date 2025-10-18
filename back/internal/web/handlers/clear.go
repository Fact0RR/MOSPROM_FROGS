package handlers

import (
	"database/sql"
	"jabki/internal/database"
	"strconv"

	"github.com/gofiber/fiber/v2"
	"github.com/google/uuid"
	"github.com/sirupsen/logrus"
)

type Clear struct {
	db     *sql.DB
	logger *logrus.Logger
}

func NewClear(db *sql.DB, logger *logrus.Logger) *Clear {
	return &Clear{
		db:     db,
		logger: logger,
	}
}

func (ch *Clear) Handler(c *fiber.Ctx) error {
	uuid := c.Locals("uuid").(uuid.UUID)
	chatIDStr := c.Params("chat_id")

	chatID, err := strconv.Atoi(chatIDStr)
	if err != nil {
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{
			"error": "Invalid chat ID format",
		})
	}

	isCorresponds, err := database.CheckChat(ch.db, uuid.String(), chatID, ch.logger)
	if err != nil || !isCorresponds {
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{
			"error": "Chat ID is not corresponds to user uuid",
		})
	}

	if err := database.HideMessages(ch.db, chatID, ch.logger); err != nil {
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{
			"error":   "Error in database",
			"details": err.Error(),
		})
	}

	return c.SendString("")
}
