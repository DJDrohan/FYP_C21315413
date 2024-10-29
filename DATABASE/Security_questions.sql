CREATE TABLE "FaceUsers".security_questions (
    question_id SERIAL PRIMARY KEY,
    question_text TEXT NOT NULL
);


INSERT INTO "FaceUsers".security_questions (question_text) VALUES
('First pet\'s name'),
('First car make'),
('Mother\'s maiden name'),
('Name of first school');


