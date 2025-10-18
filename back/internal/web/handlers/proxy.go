package handlers

import (
	"errors"
	"fmt"
	"io"
	"jabki/internal/s3"
	"regexp"

	"github.com/gofiber/fiber/v2"
	"github.com/minio/minio-go"
	"github.com/sirupsen/logrus"
)

var ErrFileIsNotAnAudioMpegFile = errors.New("File is not an audio/mpeg file")

// Регулярное выражение для проверки пути
// Формат: voices/{uuid}_{timestamp}.webm
var voicePathRegex = regexp.MustCompile(`^/voices/([a-f0-9-]+)_(\d+)\.webm$`)

type Proxy struct {
	s3     *minio.Client
	logger *logrus.Logger
}

func NewProxy(s3 *minio.Client, logger *logrus.Logger) *Proxy {
	return &Proxy{
		s3:     s3,
		logger: logger,
	}
}

func (ph *Proxy) Handler(c *fiber.Ctx) error {
	path := c.Path()

	bucket, fileName, err := parseVoicePath(path)
	if err != nil {
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{
			"error": err.Error(),
		})
	}

	object, err := s3.GetMpegFile(ph.s3, bucket, fileName)
	if err != nil {
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{
			"error": err.Error(),
		})
	}
	defer object.Close()

	c.Set("Content-Type", "audio/mpeg")
	c.Set("Content-Disposition", fmt.Sprintf("inline; filename=\"%s\"", fileName))
	c.Set("Cache-Control", "public, max-age=3600")

	_, err = io.Copy(c.Response().BodyWriter(), object)
	if err != nil {
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error": fmt.Sprintf("Failed to stream file: %v", err),
		})
	}

	return nil
}

func parseVoicePath(path string) (bucket, fileName string, err error) {
	matches := voicePathRegex.FindStringSubmatch(path)
	if matches == nil {
		return "", "", ErrFileIsNotAnAudioMpegFile
	}

	bucket = "voices"
	fileName = matches[1] + "_" + matches[2] + ".webm"

	return bucket, fileName, nil
}
