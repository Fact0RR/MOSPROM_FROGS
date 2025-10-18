package database

import (
	"database/sql"
	_ "embed"
	"fmt"
	"time"

	"github.com/sirupsen/logrus"
)

//go:embed queries/get_supports.sql
var getSupportsQuery string

//go:embed queries/set_support.sql
var setSupportQuery string

// GetSupports получает все сообщения поддержки по ID чата
func GetSupports(
    db *sql.DB,
    chatID int,
    logger *logrus.Logger,
) (
    supports []Support,
    err error,
) {
    rows, err := db.Query(getSupportsQuery, chatID)
    if err != nil {
        logger.WithError(err).Error("Failed to query supports")
        return nil, err
    }
    defer rows.Close()

    for rows.Next() {
        var support Support
        err := rows.Scan(
            &support.ID,
            &support.Message,
            &support.UserUUID,
            &support.CreateDate,
        )
        if err != nil {
            logger.WithError(err).Error("Failed to scan support row")
            continue
        }
        support.ChatID = chatID
        supports = append(supports, support)
    }

    if err = rows.Err(); err != nil {
        logger.WithError(err).Error("Error during supports rows iteration")
        return nil, err
    }

    return supports, nil
}

// CreateSupport создает новое сообщение поддержки
func CreateSupport(
    db *sql.DB,
	userUUID string,
    chatID int,
	message string,
    logger *logrus.Logger,
) error {
    result, err := db.Exec(setSupportQuery, message, userUUID, chatID)
    if err != nil {
        logger.WithError(err).Error("Failed to create support message")
        return err
    }

    rowsAffected, err := result.RowsAffected()
    if err != nil {
        logger.WithError(err).Error("Failed to get rows affected")
        return err
    }

    if rowsAffected == 0 {
        err := fmt.Errorf("no support message created - user with UUID %s may not exist", userUUID)
        logger.WithError(err).Error("Support creation failed")
        return err
    }

    logger.WithFields(logrus.Fields{
        "user_uuid": userUUID,
        "chat_id":   chatID,
    }).Info("Support message created successfully")

    return nil
}

type Support struct {
    ID         int       `json:"id"`
    Message    string    `json:"message"`
    UserUUID   string    `json:"user_uuid"`
    ChatID     int       `json:"chat_id"`
    CreateDate time.Time `json:"create_date"`
}