package database

import (
	"database/sql"
	_ "embed"
	"errors"

	"github.com/google/uuid"
	"github.com/sirupsen/logrus"
)

//go:embed queries/registration.sql
var regQuery string

var ErrUserAlreadyExists = errors.New("user with this login already exists")

func RegistrateUser(db *sql.DB, login, password string, logger *logrus.Logger) (*uuid.UUID, error) {
	var userUUID uuid.UUID

	err := db.QueryRow(regQuery, login, password).Scan(&userUUID)
	if err != nil {
		if errors.Is(err, sql.ErrNoRows) {
			logger.WithFields(logrus.Fields{
				"login": login,
				"error": err,
			}).Warn("registration failed: user already exists")
			return nil, ErrUserAlreadyExists
		}

		logger.WithFields(logrus.Fields{
			"login": login,
			"error": err,
		}).Error("database error during registration")
		return nil, err
	}

	logger.WithFields(logrus.Fields{
		"login": login,
		"uuid":  userUUID.String(),
	}).Info("user registered successfully")

	return &userUUID, nil
}
