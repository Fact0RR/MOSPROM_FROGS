package handlers

import (
	"database/sql"
	"jabki/internal/database"
	"strconv"

	"github.com/gofiber/fiber/v2"
	"github.com/google/uuid"
	"github.com/sirupsen/logrus"
)

type supportHistory struct {
	db     *sql.DB
	logger *logrus.Logger
}

func NewSupportHistory(db *sql.DB, logger *logrus.Logger) *supportHistory {
	return &supportHistory{
		db:     db,
		logger: logger,
	}
}

func (sh *supportHistory) GetSupportsHistoryHandler(c *fiber.Ctx) error {
	userUUID := c.Locals("uuid").(uuid.UUID)
	chatIDStr := c.Params("chat_id")

	chatID, err := strconv.Atoi(chatIDStr)
	if err != nil {
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{
			"error": "Invalid chat ID format",
		})
	}

	// Проверяем, принадлежит ли чат пользователю
	isCorresponds, err := database.CheckChat(sh.db, userUUID.String(), chatID, sh.logger)
	if err != nil || !isCorresponds {
		return c.Status(fiber.StatusForbidden).JSON(fiber.Map{
			"error": "Chat does not belong to user",
		})
	}

	// Получаем сообщения поддержки
	supports, err := database.GetSupports(sh.db, chatID, sh.logger)
	if err != nil {
		sh.logger.WithFields(logrus.Fields{
			"user_uuid": userUUID.String(),
			"chat_id":   chatID,
			"error":     err.Error(),
		}).Error("Failed to get supports from database")
		
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error":   "Failed to retrieve support messages",
			"details": err.Error(),
		})
	}

	return c.JSON(supports)
}