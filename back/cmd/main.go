package main

import (
	"jabki/internal"
	"jabki/internal/settings"

	"github.com/sirupsen/logrus"
)

func main() {
	logger := logrus.New()
	logger.SetLevel(logrus.DebugLevel)
	settings := settings.InitSettings(logger)
	app, err := internal.InitApp(&settings, logger)
	if err != nil {
		app.Stop()
		logger.Fatal("Ошибка инициализации проекта")
	}
	defer app.Stop()
	logger.Fatal(app.Start())
}
