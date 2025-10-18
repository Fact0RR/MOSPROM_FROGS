package database

import (
	"database/sql"
	_ "embed"
	"time"

	"github.com/sirupsen/logrus"
)

//go:embed queries/history.sql
var historyQuery string

func GetHistory(
	db *sql.DB,
	chatID int,
	logger *logrus.Logger,
) (
	messages []Message,
	err error,
) {
	rows, err := db.Query(historyQuery, chatID)
	if err != nil {
		logger.WithError(err).Error("Failed to query history")
		return nil, err
	}
	defer rows.Close()

	for rows.Next() {
		var msg Message
		err := rows.Scan(
			&msg.QuestionID,
			&msg.AnswerID,
			&msg.Question,
			&msg.Answer,
			&msg.QuestionTime,
			&msg.AnswerTime,
			&msg.VoiceURL,
			&msg.Rating,
		)
		if err != nil {
			logger.WithError(err).Error("Failed to scan row")
			continue
		}
		messages = append(messages, msg)
	}

	if err = rows.Err(); err != nil {
		logger.WithError(err).Error("Error during rows iteration")
		return nil, err
	}

	return messages, nil
}

type Message struct {
	QuestionID   int       `json:"question_id"`
	AnswerID     int       `json:"answer_id"`
	Question     string    `json:"question"`
	Answer       string    `json:"answer"`
	QuestionTime time.Time `json:"question_time"`
	AnswerTime   time.Time `json:"answer_time"`
	VoiceURL     string    `json:"voice_url"`
	Rating       *int      `json:"rating"`
}
