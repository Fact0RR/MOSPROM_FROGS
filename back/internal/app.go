package internal

import (
	"context"
	"jabki/internal/client"
	"jabki/internal/database"
	"jabki/internal/s3"
	"jabki/internal/settings"
	"jabki/internal/web"

	"database/sql"

	"github.com/gofiber/fiber/v2"
	"github.com/minio/minio-go"
	"github.com/sirupsen/logrus"
)

type App struct {
	Config *settings.Settings
	Server *fiber.App
	DB     *sql.DB
	S3     *minio.Client
	logger *logrus.Logger
}

func InitApp(config *settings.Settings, logger *logrus.Logger) (*App, error) {
	ctx := context.Background()
	server := fiber.New()

	var err error
	db, err := database.InitDBWithPing(ctx, config.PostgresURL, logger)
	if err != nil {
		return nil, err
	}
	logger.Info("Есть подключение к БД postgres! 🐘")

	s3client, err := s3.InitMinioClient(config.S3URL, config.S3Login, config.S3Password, false)
	if err != nil {

		return nil, err
	}
	logger.Info("Есть подключение к S3 MINIO! 🐦")

	err = client.Ping(config.Model)
	if err != nil {
		logger.Fatalf("Нет подключение к model %v", err)
	}
	logger.Info("Есть подключение к model! ⚙️")

	// err = client.Ping(config.Recognizer)
	// if err != nil {
	// 	logger.Fatalf("Нет подключение к recognizer %v", err)
	// }
	// logger.Info("Есть подключение к recognizer! 🔊")

	modelClient := client.NewClient("POST", config.Model, "/mock")
	recognizerClient := client.NewClient("POST", config.Recognizer, "/mock")

	web.InitServiceRoutes(server, db, config.SecretSerice, logger)
	web.InitPublicRoutes(server, db, config.SecretUser, config.FrontOrigin, logger)
	web.InitJWTMiddleware(server, config.SecretUser, config.FrontOrigin, logger)
	web.InitPrivateRoutes(server, db, s3client, modelClient, recognizerClient, logger)

	return newApp(config, server, db, s3client, logger), nil
}

func newApp(
	config *settings.Settings,
	server *fiber.App,
	db *sql.DB,
	s3 *minio.Client,
	logger *logrus.Logger,
) *App {
	return &App{
		Config: config,
		Server: server,
		DB:     db,
		S3:     s3,
		logger: logger,
	}
}

func (a *App) Start() error {
	return a.Server.Listen(a.Config.Port)
}

func (a *App) Stop() error {
	err := a.DB.Close()
	return err
}
