DROP DATABASE db;
CREATE DATABASE db;

CREATE TABLE IMAGE(
    id INT AUTO_INCREMENT,
    name VARCHAR(50) NOT NULL,
    prediction_level VARCHAR(5),
    detection DECIMAL(3,2),
    pathology VARCHAR(6),
    birads_score TINYINT,
    shape VARCHAR(9),
    PRIMARY KEY(id)
);

INSERT INTO IMAGE(
    name
)VALUES(

);