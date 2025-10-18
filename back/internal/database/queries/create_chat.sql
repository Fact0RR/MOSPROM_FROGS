INSERT INTO chats (name, user_id) VALUES ($1, (SELECT id FROM users WHERE uuid = $2)) RETURNING id;
