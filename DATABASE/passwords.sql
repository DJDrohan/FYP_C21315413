CREATE TABLE "FaceUsers".passwords (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES "FaceUsers".users(id) ON DELETE CASCADE,
    hashed_password TEXT NOT NULL,
    salt TEXT NOT NULL
);
