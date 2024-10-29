CREATE TABLE "FaceUsers".users (
    id SERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL
);
