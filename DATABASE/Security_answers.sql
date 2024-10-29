CREATE TABLE "FaceUsers".security_answers (
    answer_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES "FaceUsers".users(id) ON DELETE CASCADE,
    question_id INTEGER REFERENCES "FaceUsers".security_questions(question_id) ON DELETE CASCADE,
    answer TEXT NOT NULL,
    salt TEXT NOT NULL,
    UNIQUE (user_id)  -- Ensures each user can have only one question-answer pair
);
