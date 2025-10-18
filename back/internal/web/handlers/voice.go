package handlers

import (
	"database/sql"
	"fmt"
	"io"
	"jabki/internal/client"
	"jabki/internal/s3"

	"github.com/gofiber/fiber/v2"
	"github.com/google/uuid"
	"github.com/minio/minio-go"
	"github.com/sirupsen/logrus"
)

type Voice struct {
	model      *client.Client
	recognizer *client.Client
	db         *sql.DB
	s3         *minio.Client
	logger     *logrus.Logger
}

func NewVoice(client *client.Client, recognizer *client.Client, db *sql.DB, s3 *minio.Client, logger *logrus.Logger) *Voice {
	return &Voice{
		model:      client,
		recognizer: recognizer,
		db:         db,
		s3:         s3,
		logger:     logger,
	}
}

func (vh *Voice) Handler(c *fiber.Ctx) error {
	uuid := c.Locals("uuid").(uuid.UUID)
	var err error

	file, err := c.FormFile("voice")
	if err != nil {
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{
			"error": "Не удалось получить файл: " + err.Error(),
		})
	}

	if len(file.Filename) < 5 || file.Filename[len(file.Filename)-5:] != ".webm" {
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{
			"error": "Файл должен быть в формате .webm",
		})
	}

	uploadedFile, err := file.Open()
	if err != nil {
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error": "Не удалось открыть файл: " + err.Error(),
		})
	}
	defer uploadedFile.Close()

	fileBytes, err := io.ReadAll(uploadedFile)
	if err != nil {
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error": "Не удалось прочитать файл: " + err.Error(),
		})
	}

	url, err := s3.UploadMP3ToMinIO(vh.s3, "voices", uuid.String(), fileBytes)
	if err != nil {
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{
			"error":   "Error upload to S3",
			"details": err.Error(),
		})
	}

	jsonBytes := fmt.Sprintf("{\"voice_url\":\"%s\"}", url)

	question, err := vh.recognizer.Mock([]byte(jsonBytes))
	if err != nil {
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{
			"error":   "Error send message",
			"details": err.Error(),
		})
	}

	messageOut := voiceOut{
		Question: question.Message,
		VoiceURL: url,
	}

	return c.JSON(messageOut)
}

type voiceOut struct {
	Question string `json:"question"`
	VoiceURL string `json:"voice_url"`
}
