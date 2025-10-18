INSERT INTO answers
  (time_utc, message, chat_id)
VALUES
  ($1, $2, $3)
RETURNING answer_id;