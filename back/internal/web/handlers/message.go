package handlers

import (
	"database/sql"
	"encoding/json"
	"jabki/internal/client"
	"jabki/internal/database"
	"strconv"
	"time"

	"github.com/gofiber/fiber/v2"
	"github.com/google/uuid"
	"github.com/sirupsen/logrus"
)

type Message struct {
	client *client.Client
	db     *sql.DB
	logger *logrus.Logger
}

type messageIn struct {
	Question string `json:"question"`
	VoiceURL string `json:"voice_url"`
}

type messageToModel struct {
	ChatID      int            `json:"chat_id"`
	UserUUID    uuid.UUID      `json:"user_uuid"`
	UserRequest string         `json:"user_request"`
	Messages    []messageModel `json:"messages"`
}

func NewMessage(client *client.Client, db *sql.DB, logger *logrus.Logger) *Message {
	return &Message{
		client: client,
		db:     db,
		logger: logger,
	}
}

func (mh *Message) Handler(c *fiber.Ctx) error {
	questionTime := time.Now().UTC()
	var messageIn messageIn
	var err error

	uuid := c.Locals("uuid").(uuid.UUID)
	chatIDStr := c.Params("chat_id")

	chatID, err := strconv.Atoi(chatIDStr)
	if err != nil {
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{
			"error": "Invalid chat ID format",
		})
	}

	isCorresponds, err := database.CheckChat(mh.db, uuid.String(), chatID, mh.logger)
	if err != nil || !isCorresponds {
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{
			"error": "Chat ID is not corresponds to user uuid",
		})
	}

	if err = json.Unmarshal(c.Body(), &messageIn); err != nil {
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{
			"error":   "Invalid JSON format",
			"details": err.Error(),
		})
	}

	messages, err := database.GetHistory(mh.db, chatID, mh.logger)
	if err != nil {
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{
			"error":   "Error in database",
			"details": err.Error(),
		})
	}

	var messageHistory messageOutToModel
	for _, message := range messages {
		messageHistory.Messages = append(messageHistory.Messages, 
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

	dataToModel, err := json.Marshal(messageToModel{
		ChatID:      chatID,
		UserUUID:    uuid,
		UserRequest: messageIn.Question,
		Messages: messageHistory.Messages,
	})
	if err != nil {
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{
			"error":   "Error to create json",
			"details": err.Error(),
		})
	}

	answer, err := mh.client.Mock(dataToModel)
	if err != nil {
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{
			"error":   "Error send message",
			"details": err.Error(),
		})
	}
	answerTime := time.Now().UTC()

	questionID, answerID, err := database.WriteMessage(
		mh.db,
		chatID,
		messageIn.Question,
		answer.Message,
		questionTime,
		answerTime,
		messageIn.VoiceURL,
		mh.logger,
	)
	if err != nil {
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{
			"error":   "Error write message to DB",
			"details": err.Error(),
		})
	}

	messageOut := messageOut{
		QuestionID:      questionID,
		AnswerID:        answerID,
		Answer:          answer.Message,
		QuestionTime:    questionTime,
		AnswerTime:      answerTime,
		IsSupportNeeded: answer.IsSupportNeeded,
	}

	return c.JSON(messageOut)
}

type messageOut struct {
	QuestionID      int       `json:"question_id"`
	AnswerID        int       `json:"answer_id"`
	Answer          string    `json:"answer"`
	QuestionTime    time.Time `json:"question_time"`
	AnswerTime      time.Time `json:"answer_time"`
	IsSupportNeeded bool      `json:"is_support_needed"`
}
