CREATE TABLE "FaceUsers".sessions (
    user_id INTEGER REFERENCES "FaceUsers".users(id) ON DELETE CASCADE,
    session_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id),  -- Ensure only one entry per user_id
    UNIQUE (user_id)  -- Enforce unique sessions per user
);
