package middlewares

import (
	"github.com/gofiber/fiber/v2"
	"github.com/gofiber/fiber/v2/middleware/cors"
)

func Cors(allowOrigins string) fiber.Handler {
	return cors.New(cors.Config{
		AllowOrigins:     allowOrigins,                   // Разрешенные источники
		AllowMethods:     "GET,POST,PUT,DELETE",          // Разрешенные методы
		AllowHeaders:     "Origin, Content-Type, Accept, Authorization", // Разрешенные заголовки
		AllowCredentials: true,
	})
}
