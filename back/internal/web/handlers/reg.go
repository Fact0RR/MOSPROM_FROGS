package handlers

import (
	"database/sql"
	"encoding/json"
	"jabki/internal/database"
	"jabki/pkg"

	"github.com/gofiber/fiber/v2"
	"github.com/sirupsen/logrus"
)

type Reg struct {
	db     *sql.DB
	secret string
	logger *logrus.Logger
}

func NewReg(db *sql.DB, secret string, logger *logrus.Logger) *Reg {
	return &Reg{
		db:     db,
		secret: secret,
		logger: logger,
	}
}

type regIn struct {
	Login    string `json:"login"`
	Password string `json:"password"`
}

func (rh *Reg) Handler(c *fiber.Ctx) error {
	var regIn authIn
	var err error
	if err = json.Unmarshal(c.Body(), &regIn); err != nil {
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{
			"error":   "Invalid JSON format",
			"details": err.Error(),
		})
	}
	var regOut authOut

	userUUID, err := database.RegistrateUser(rh.db, regIn.Login, regIn.Password, rh.logger)
	if err != nil {
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{
			"error":   "fail registration",
			"details": err.Error(),
		})
	}

	regOut.Jwt = pkg.GetJWT(userUUID.String(), rh.secret)

	return c.JSON(regOut)
}

type regOut struct {
	Jwt string `json:"jwt"`
}
