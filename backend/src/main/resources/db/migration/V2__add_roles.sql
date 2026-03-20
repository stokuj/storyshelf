ALTER TABLE users
    ADD COLUMN username TEXT,
    ADD COLUMN provider TEXT,
    ADD COLUMN provider_id TEXT,
    ADD COLUMN bio TEXT,
    ADD COLUMN avatar_url TEXT,
    ADD COLUMN profile_public BOOLEAN NOT NULL DEFAULT TRUE,
    ADD COLUMN created_at TIMESTAMPTZ NOT NULL DEFAULT NOW();

UPDATE users SET role = 'USER' WHERE role = 'ROLE_USER';
UPDATE users SET role = 'MODERATOR' WHERE role = 'ROLE_MODERATOR';
UPDATE users SET role = 'ADMIN' WHERE role = 'ROLE_ADMIN';

UPDATE users SET username = email WHERE username IS NULL;

ALTER TABLE users
    ALTER COLUMN username SET NOT NULL;

ALTER TABLE users
    ADD CONSTRAINT uq_users_username UNIQUE (username);

ALTER TABLE users
    ADD CONSTRAINT chk_users_role
        CHECK (role IN ('USER', 'MODERATOR', 'ADMIN'));