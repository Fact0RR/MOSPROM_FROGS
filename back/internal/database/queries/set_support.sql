INSERT INTO supports (message, user_id, chat_id) 
VALUES ($1, (SELECT id FROM users WHERE uuid = $2), $3);