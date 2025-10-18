package database

import (
	"database/sql"
	_ "embed"
	"time"

	"github.com/sirupsen/logrus"
)

//go:embed queries/like.sql
var likeyQuery string

func SetLike(
	db *sql.DB,
	chatID int,
	answerID int,
	rating *int,
	logger *logrus.Logger,
) (
	err error,
) {
	startTime := time.Now()

	// Execute the SQL query
	result, err := db.Exec(likeyQuery, chatID, answerID, rating)
	if err != nil {
		logger.WithFields(logrus.Fields{
			"chatID":   chatID,
			"answerID": answerID,
			"error":    err,
			"duration": time.Since(startTime),
		}).Error("Failed to set like visibility")
		return err
	}

	// Check if any rows were affected
	rowsAffected, err := result.RowsAffected()
	if err != nil {
		logger.WithFields(logrus.Fields{
			"chatID":   chatID,
			"answerID": answerID,
			"error":    err,
			"duration": time.Since(startTime),
		}).Error("Failed to get rows affected after setting like")
		return err
	}

	logger.WithFields(logrus.Fields{
		"chatID":       chatID,
		"answerID":     answerID,
		"rowsAffected": rowsAffected,
		"duration":     time.Since(startTime),
	}).Info("Successfully set like visibility")

	return nil
}
