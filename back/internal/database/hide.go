package database

import (
	"database/sql"
	_ "embed"

	"github.com/sirupsen/logrus"
)

//go:embed queries/hide_answers.sql
var hideAnswersQuery string

//go:embed queries/hide_questions.sql
var hideQuestionsQuery string

func HideMessages(
	db *sql.DB,
	chatID int,
	logger *logrus.Logger,
) error {
	tx, err := db.Begin()
	if err != nil {
		logger.WithError(err).Error("Failed to begin transaction")
		return err
	}

	defer func() {
		if p := recover(); p != nil {
			tx.Rollback()
			panic(p)
		} else if err != nil {
			tx.Rollback()
		} else {
			err = tx.Commit()
			if err != nil {
				logger.WithError(err).Error("Failed to commit transaction")
			}
		}
	}()

	// Сначала скрываем ответы
	_, err = tx.Exec(hideAnswersQuery, chatID)
	if err != nil {
		logger.WithError(err).WithField("uuid", chatID).Error("Failed to hide answers")
		return err
	}

	// Затем скрываем вопросы
	_, err = tx.Exec(hideQuestionsQuery, chatID)
	if err != nil {
		logger.WithError(err).WithField("uuid", chatID).Error("Failed to hide questions")
		return err
	}

	logger.WithField("uuid", chatID).Info("User messages hidden successfully")
	return nil
}
