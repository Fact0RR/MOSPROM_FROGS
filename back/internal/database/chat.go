package database

import (
	"database/sql"
	_ "embed"
	"errors"
	"time"

	"github.com/sirupsen/logrus"
)

//go:embed queries/create_chat.sql
var createChatQuery string

//go:embed queries/get_chats.sql
var getChatsQuery string

//go:embed queries/check_chat.sql
var checkChatQuery string

var ErrUserByUUIDNotFound = errors.New("user with this UUID not found")

func CreateChat(
	db *sql.DB,
	chatName string,
	userUUID string,
	logger *logrus.Logger,
) (
	chatID int,
	err error,
) {
	err = db.QueryRow(createChatQuery, chatName, userUUID).Scan(&chatID)
	if err != nil {
		if errors.Is(err, sql.ErrNoRows) {
			logger.WithFields(logrus.Fields{
				"chat_name": chatName,
				"user_uuid": userUUID,
				"error":     err,
			}).Warn("chat creation failed: user not found or other constraint violation")
			return 0, ErrUserByUUIDNotFound
		}

		logger.WithFields(logrus.Fields{
			"chat_name": chatName,
			"user_uuid": userUUID,
			"error":     err,
		}).Error("database error during chat creation")
		return 0, err
	}

	logger.WithFields(logrus.Fields{
		"chat_name": chatName,
		"user_uuid": userUUID,
		"chat_id":   chatID,
	}).Info("chat created successfully")

	return chatID, nil
}

func GetChats(
	db *sql.DB,
	userUUID string,
	logger *logrus.Logger,
) (
	chats []Chat,
	err error,
) {
	rows, err := db.Query(getChatsQuery, userUUID)
	if err != nil {
		logger.WithFields(logrus.Fields{
			"user_uuid": userUUID,
			"error":     err,
		}).Error("database error during fetching chats")
		return nil, err
	}
	defer rows.Close()

	for rows.Next() {
		var chat Chat
		err := rows.Scan(&chat.ChatID, &chat.Name, &chat.CreateTime)
		if err != nil {
			logger.WithFields(logrus.Fields{
				"user_uuid": userUUID,
				"error":     err,
			}).Error("error scanning chat row")
			return nil, err
		}
		chats = append(chats, chat)
	}

	if err = rows.Err(); err != nil {
		logger.WithFields(logrus.Fields{
			"user_uuid": userUUID,
			"error":     err,
		}).Error("error iterating chat rows")
		return nil, err
	}

	logger.WithFields(logrus.Fields{
		"user_uuid":  userUUID,
		"chat_count": len(chats),
	}).Info("chats fetched successfully")

	return chats, nil
}

type Chat struct {
	ChatID     int       `json:"chat_id"`
	Name       string    `json:"name"`
	CreateTime time.Time `json:"create_time"`
}

func CheckChat(
	db *sql.DB,
	userUUID string,
	chatID int,
	logger *logrus.Logger,
) (
	isCorresponds bool,
	err error,
) {
	err = db.QueryRow(checkChatQuery, userUUID, chatID).Scan(&isCorresponds)
	if err != nil {
		if err == sql.ErrNoRows {
			// Если запрос не вернул строк, считаем что чат не соответствует пользователю
			return false, nil
		}
		logger.WithError(err).Error("failed to check chat ownership")
		return false, err
	}

	return isCorresponds, nil
}
