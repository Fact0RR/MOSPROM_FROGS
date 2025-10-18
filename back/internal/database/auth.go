package database

import (
	"database/sql"
	_ "embed"
	"errors"

	"github.com/google/uuid"
	"github.com/sirupsen/logrus"
)

//go:embed queries/authentication.sql
var authQuery string

var ErrUserNotFound = errors.New("user not found or invalid credentials")

func AuthenticatUser(db *sql.DB, login, password string, logger *logrus.Logger) (*uuid.UUID, error) {
	var userUUID uuid.UUID

	err := db.QueryRow(authQuery, login, password).Scan(&userUUID)
	if err != nil {
		if errors.Is(err, sql.ErrNoRows) {
			logger.WithFields(logrus.Fields{
				"login": login,
				"error": err,
			}).Warn("authentication failed: user not found or invalid password")
			return nil, ErrUserNotFound
		}

		logger.WithFields(logrus.Fields{
			"login": login,
			"error": err,
		}).Error("database error during authentication")
		return nil, err
	}

	logger.WithFields(logrus.Fields{
		"login": login,
		"uuid":  userUUID.String(),
	}).Info("user authenticated successfully")

	return &userUUID, nil
}
