package database

import (
	"context"
	"database/sql"

	_ "github.com/lib/pq"
	"github.com/sirupsen/logrus"
)

func InitDBWithPing(ctx context.Context, postgresURL string, logger *logrus.Logger) (*sql.DB, error) {
	db, err := sql.Open("postgres", postgresURL)
	if err != nil {
		logger.Errorf("Ошибка подключения к БД: %v", err)
		return nil, err
	}

	// Проверка подключения
	err = db.Ping()
	if err != nil {
		logger.Errorf("Ошибка ping БД: %v", err)
		return nil, err
	}

	return db, nil
}
