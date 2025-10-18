SELECT uuid 
FROM users 
WHERE login = $1
AND password_hash = crypt($2 , password_hash);