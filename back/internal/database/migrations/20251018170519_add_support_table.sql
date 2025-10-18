-- +goose Up
-- +goose StatementBegin
CREATE TABLE IF NOT EXISTS supports (
    id SERIAL PRIMARY KEY,
    message text NOT NULL,
    user_id INTEGER NOT NULL,
    chat_id INTEGER NOT NULL,
    create_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (chat_id) REFERENCES chats(id) ON DELETE CASCADE
)
-- +goose StatementEnd

-- +goose Down
-- +goose StatementBegin
DROP TABLE IF EXISTS supports;
-- +goose StatementEnd
