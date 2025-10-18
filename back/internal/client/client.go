package client

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
)

type Client struct {
	method string
	url    string
	path   string
	client *http.Client
}

func NewClient(method, url, path string) *Client {
	return &Client{
		method: method,
		url:    url,
		path:   path,
		client: &http.Client{},
	}
}

func (c *Client) Mock(data []byte) (*AnswerModel, error) {
	fullURL := c.url + c.path

	req, err := http.NewRequest(c.method, fullURL, bytes.NewBuffer(data))
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Accept", "application/json")

	resp, err := c.client.Do(req)
	if err != nil {
		return nil, fmt.Errorf("failed to execute request: %w", err)
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read response body: %w", err)
	}

	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return nil, fmt.Errorf("request failed with status %d: %s", resp.StatusCode, string(body))
	}

	var answerModel AnswerModel
	if err := json.Unmarshal(body, &answerModel); err != nil {
		return nil, fmt.Errorf("failed to unmarshal response: %w", err)
	}

	return &answerModel, nil
}

type AnswerModel struct {
	Message         string `json:"message"`
	IsSupportNeeded bool   `json:"is_support_needed"`
}
