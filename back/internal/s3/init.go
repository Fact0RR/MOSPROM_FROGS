package s3

import (
	"fmt"

	"github.com/minio/minio-go"
)

// InitMinioClient инициализирует подключение к MinIO и проверяет наличие бакета voices
func InitMinioClient(host, accessKey, secretKey string, useSSL bool) (*minio.Client, error) {
	// Создаем клиент
	client, err := minio.New(host, accessKey, secretKey, useSSL)
	if err != nil {
		return nil, fmt.Errorf("не удалось создать MinIO клиент: %w", err)
	}

	// Проверяем существование бакета voices
	exists, err := client.BucketExists("voices")
	if err != nil {
		return nil, fmt.Errorf("ошибка проверки бакета 'voices': %w", err)
	}

	if !exists {
		return nil, fmt.Errorf("бакет 'voices' не существует")
	}

	return client, nil
}
