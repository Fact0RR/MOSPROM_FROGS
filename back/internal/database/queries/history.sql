SELECT 
    q.question_id,
    a.answer_id,
    q.message,
    a.message,
    q.time_utc,
    a.time_utc,
    q.voice_url,
    a.rating
FROM questions q
LEFT JOIN answers a ON q.answer_id = a.answer_id
WHERE q.chat_id = $1
AND a.visible = true;