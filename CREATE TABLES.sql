CREATE TABLE SUBJECTS (
	subject_id INT NOT NULL auto_increment PRIMARY KEY,
    subject_name VARCHAR(60) NOT NULL,
    hours_per_week INT
);

CREATE TABLE CLASS (
	class_id INT NOT NULL auto_increment PRIMARY KEY,
    class_name VARCHAR(60)
);

CREATE TABLE TEACHERS (
	staff_id INT NOT NULL auto_increment PRIMARY KEY,
	first_name VARCHAR(60) NOT NULL,
    last_name VARCHAR(60) NOT NULL,
    phone VARCHAR(30) NOT NULL,
    email VARCHAR(60) NOT NULL,
    home_address VARCHAR(200),
    hours_per_week INT,
    subject_id INT,
    FOREIGN KEY (subject_id) REFERENCES SUBJECTS(subject_id)
);

CREATE TABLE STUDENTS (
	student_id INT NOT NULL auto_increment PRIMARY KEY,
    first_name VARCHAR(60) NOT NULL,
    last_name VARCHAR(60) NOT NULL,
    email VARCHAR(60) NOT NULL,
    class_id INT,
	FOREIGN KEY (class_id) REFERENCES CLASS(class_id)
);




