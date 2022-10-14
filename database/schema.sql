
DROP DATABASE lab;
CREATE DATABASE lab;

DROP TABLE IF EXISTS APPUSER;
DROP TABLE IF EXISTS IMAGE;
DROP TABLE IF EXISTS ROL;

CREATE TABLE ACTION(
    id INT AUTO_INCREMENT,
    short_label VARCHAR(5),
    label VARCHAR(15),
    PRIMARY KEY(id)
);
CREATE TABLE ROL(
    id INT AUTO_INCREMENT,
    title VARCHAR(15),
    PRIMARY KEY(id)
);
CREATE TABLE ACTIONROL(
    action_id INT,
    rol_id INT,
    PRIMARY KEY(action_id, rol_id),
    FOREIGN KEY (action_id) REFERENCES ACTION(id),
    FOREIGN KEY (rol_id) REFERENCES ROL(id)
);
CREATE TABLE APPUSER(
    id INT AUTO_INCREMENT,
    first_name VARCHAR(15),
    last_name VARCHAR(20),
    email VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(60) NOT NULL,
    rol_id INT NOT NULL DEFAULT 1,
    is_verified TINYINT(1) NOT NULL DEFAULT 0,
    verification_token VARCHAR(61),
    PRIMARY KEY(id)
);

CREATE TABLE IMAGE(
    id INT AUTO_INCREMENT,
    name VARCHAR(50) NOT NULL,
    prediction_level VARCHAR(13),
    detection DECIMAL(3,2),
    pathology VARCHAR(6),
    birads_score TINYINT,
    shape VARCHAR(9),
    user_id INT NOT NULL,
    PRIMARY KEY(id),
    FOREIGN KEY (user_id) REFERENCES APPUSER(id)
);

INSERT INTO ACTION(
    short_label,
    label
) VALUES (
    'DFT',
    'Default'
);

INSERT INTO ROL(
    title
) VALUES (
    'Base'
);

INSERT INTO ACTIONROL(
    action_id,
    rol_id
) VALUES (
    1,
    1
);

INSERT INTO APPUSER(
    first_name,
    last_name,
    email,
    is_verified,
    password
) VALUES (
    'Lucas',
    'Camino',
    'lucas@camino.com',
    1,
    '$2b$12$lGB6N9dwOww37aGIRtQ3eezPXWyN36WF44IyZxmM12hdHFxYYqqr2'
);
