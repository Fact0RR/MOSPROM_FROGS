SELECT id, message, user_id, create_date 
FROM supports 
WHERE chat_id = $1;