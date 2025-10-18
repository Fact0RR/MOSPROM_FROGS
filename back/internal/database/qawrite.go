package database

import (
	"database/sql"
	_ "embed"
	"time"

	"github.com/sirupsen/logrus"
)

//go:embed queries/question.sql
var questionQuery string

//go:embed queries/answer.sql
var answerQuery string

func WriteMessage(
	db *sql.DB,
	chatID int,
	question, answer string,
	questionTime, answerTime time.Time,
	voiceURL string,
	logger *logrus.Logger,
) (
	questionID int,
	answerID int,
	err error,
) {
	tx, err := db.Begin()
	if err != nil {
		logger.WithError(err).Error("Failed to begin transaction")
		return 0, 0, err
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

	if answer != "" {
		err = tx.QueryRow(answerQuery, answerTime, answer, chatID).Scan(&answerID)
		if err != nil {
			logger.WithError(err).Error("Failed to insert answer")
			return 0, 0, err
		}
		logger.WithFields(logrus.Fields{
			"answer_id": answerID,
			"chat_id":   chatID,
		}).Info("Answer inserted successfully")
	}

	if question != "" {
		err = tx.QueryRow(questionQuery, questionTime, question, chatID, answerID, voiceURL).Scan(&questionID)
		if err != nil {
			logger.WithError(err).Error("Failed to insert question")
			return 0, 0, err
		}
		logger.WithFields(logrus.Fields{
			"question_id": questionID,
			"chat_id":     chatID,
		}).Info("Question inserted successfully")
	}

	return questionID, answerID, nil
}
