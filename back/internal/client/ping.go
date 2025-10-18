package client

import (
	"errors"
	"net/http"
	"strconv"
)

func Ping(url string) error {
	resp, err := http.Get(url + "/ping")
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	// Проверяем статус код
	if resp.StatusCode != http.StatusOK {
		return errors.New("ответ 200 != " + strconv.Itoa(resp.StatusCode))
	}
	return nil
}
