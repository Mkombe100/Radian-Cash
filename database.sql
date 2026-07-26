CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    middle_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(50) UNIQUE NOT NULL,
    phone_number VARCHAR(50) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE networks (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    agent_number INT NOT NULL,
    lipa_number INT NOT NULL
);

CREATE TABLE transactions(
    id BIGSERIAL PRIMARY KEY,
    transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    network_id INT NOT NULL REFERENCES networks(id),
    transaction_type VARCHAR(30) NOT NULL,
    service_name VARCHAR(50),
    amount NUMERIC(15,2) NOT NULL,
    commission NUMERIC(15,2) DEFAULT 0,
    reference_number VARCHAR(100),
    customer_phone VARCHAR(20),
    notes TEXT,
    user_id INT NOT NULL REFERENCES users(id)
);

CREATE TABLE expenses (
    id BIGSERIAL PRIMARY KEY,
    expense_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    category VARCHAR(50) NOT NULL,
    description TEXT,
    amount NUMERIC(15,2) NOT NULL,
    user_id INT NOT NULL REFERENCES users(id)
);