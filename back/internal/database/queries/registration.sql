WITH inserted_user AS (
    INSERT INTO users (uuid, login, password_hash)
    VALUES (
        gen_random_uuid(), 
        $1, 
        crypt($2, gen_salt('bf'))
    )
    ON CONFLICT (login) DO NOTHING
    RETURNING uuid
)
SELECT uuid FROM inserted_user;