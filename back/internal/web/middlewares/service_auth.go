package middlewares

import (
	"strings"

	"github.com/gofiber/fiber/v2"
	"github.com/google/uuid"
	"github.com/sirupsen/logrus"
)

type serviceAuthentication struct {
	secret string
	logger *logrus.Logger
}

func NewServiceAuthentication(secret string, logger *logrus.Logger) *serviceAuthentication {
	return &serviceAuthentication{
		secret: secret,
		logger: logger,
	}
}

func (sa *serviceAuthentication) Handler(c *fiber.Ctx) error {
	userUUIDStr := c.Params("uuid")

	if userUUIDStr == "" {
		return errNoUUID
	}

	userUUID, err := uuid.Parse(userUUIDStr)
	if err != nil {
		return errInvalidUUID
	}

	authHeader := c.Get("Authorization")
	if authHeader == "" {
		return ErrMissingToken
	}

	const prefix = "Token "
	if !strings.HasPrefix(authHeader, prefix) {
		return ErrInvalidToken
	}

	token := strings.TrimPrefix(authHeader, prefix)
	if token != sa.secret {
		return ErrInvalidToken
	}

	c.Locals("uuid", userUUID)

	return c.Next()
}
