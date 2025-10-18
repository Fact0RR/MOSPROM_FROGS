package pkg

import (
	"time"

	"github.com/golang-jwt/jwt/v5"
)

func GetJWT(userUUID string, secret string) string {
	claims := jwt.MapClaims{}
	now := time.Now()
	// Добавляем поля
	claims["exp"] = now.Add(32 * time.Hour).Unix() // текущее время + 1 час
	claims["iat"] = now.Unix()                     // текущее время
	claims["uuid"] = userUUID
	token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
	tokenString, err := token.SignedString([]byte(secret))
	if err != nil {
		panic(err)
	}

	return tokenString
}
