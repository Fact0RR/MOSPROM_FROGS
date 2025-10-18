SELECT EXISTS(
    SELECT 1
    FROM chats c
    JOIN users u ON c.user_id = u.id
    WHERE u.uuid = $1 AND c.id = $2
);