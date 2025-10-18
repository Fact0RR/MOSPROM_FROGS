SELECT id, name, create_date FROM chats WHERE user_id = (SELECT id FROM users WHERE uuid = $1);
