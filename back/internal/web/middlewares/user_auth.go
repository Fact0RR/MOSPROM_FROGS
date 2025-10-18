package middlewares

import (
	"strings"

	"github.com/gofiber/fiber/v2"
	"github.com/golang-jwt/jwt/v5"
	"github.com/google/uuid"
	"github.com/sirupsen/logrus"
)

type userAuthentication struct {
	secret string
	logger *logrus.Logger
}

func NewUserAuthentication(secret string, logger *logrus.Logger) *userAuthentication {
	return &userAuthentication{
		secret: secret,
		logger: logger,
	}
}

func (ua *userAuthentication) Handler(c *fiber.Ctx) error {
	userUUID, errAuth := requestUserUUID(ua.secret, c.Get("Authorization", ""), ua.logger)
	if errAuth != nil {
		ua.logger.Debugf("Error Ошибка при обработки JWT error error: %s", errAuth)
		return errAuth
	} else {
		c.Locals("uuid", userUUID)
	}

	err := c.Next()

	return err
}

func requestUserUUID(secret string, authHeader string, logger *logrus.Logger) (uuid.UUID, error) {
	if len(authHeader) > 0 {
		authToken := strings.Replace(authHeader, "Bearer ", "", 1)
		secretKey := []byte(secret)
		tokenJWT, err := jwt.Parse(authToken, func(_ *jwt.Token) (interface{}, error) {
			// check token signing method etc.
			return secretKey, nil
		})
		if err != nil {
			logger.Debugf("Error parse jwt token  error %s ", err)
			return uuid.Nil, err
		}

		if claims, ok := tokenJWT.Claims.(jwt.MapClaims); ok && tokenJWT.Valid {
			rawProfileUuid, ok := claims["uuid"]
			if !ok {
				logger.Debug("Error parse jwt token - No uuid in token")
				return uuid.Nil, errNoUUID
			}

			profileUuid, err := uuid.Parse(rawProfileUuid.(string))
			if err != nil {
				logger.Debug("Error parse jwt token - Invalid uuid in token")
				return uuid.Nil, errInvalidUUID
			}

			return profileUuid, nil
		} else {
			logger.Debug("Error parse jwt token - Invalid JWT Token")

			return uuid.Nil, errInvalidJWTToken
		}
	} else {
		logger.Debug("Error parse jwt token - Auth header is empty")

		return uuid.Nil, errUnregisteredUser
	}
}
