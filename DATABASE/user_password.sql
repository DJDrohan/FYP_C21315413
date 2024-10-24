-- Create the users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE
);

-- Create the passwords table with a one-to-one relationship and salt
CREATE TABLE passwords (
    id SERIAL PRIMARY KEY,
    hashed_password VARCHAR(255) NOT NULL,
    salt VARCHAR(255) NOT NULL,  -- New column to store the salt
    user_id INT NOT NULL UNIQUE,
    CONSTRAINT fk_user
        FOREIGN KEY(user_id) 
        REFERENCES users(id)
        ON DELETE CASCADE
);
