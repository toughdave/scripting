-- Demo academic dataset seed (MySQL)

DROP TABLE IF EXISTS exam_tasks;
DROP TABLE IF EXISTS student_records_target;
DROP TABLE IF EXISTS student_records_source;

CREATE TABLE student_records_source (
  student_id VARCHAR(20),
  first_name VARCHAR(100),
  last_name VARCHAR(100),
  email VARCHAR(255),
  department VARCHAR(120),
  admission_year INT,
  score INT,
  status VARCHAR(30),
  due_date DATE,
  completed_at DATE
);

CREATE TABLE student_records_target (
  student_id VARCHAR(20),
  first_name VARCHAR(100),
  last_name VARCHAR(100),
  email VARCHAR(255),
  department VARCHAR(120),
  admission_year INT,
  score INT,
  status VARCHAR(30),
  due_date DATE,
  completed_at DATE
);

CREATE TABLE exam_tasks (
  task_id VARCHAR(20),
  owner VARCHAR(120),
  checkpoint VARCHAR(200),
  status VARCHAR(30),
  due_date DATE,
  completed_at DATE,
  priority VARCHAR(20)
);

INSERT INTO student_records_source VALUES
('STU001','Alice','Nguyen','alice.nguyen@example.edu','Computer Science',2022,78,'open','2026-02-10','2026-02-08'),
('STU002','Bob','Mensah','bob.mensah@example.edu','Mathematics',2022,92,'open','2026-02-09',NULL),
('STU003','Chidi','Okoro','chidi.okoro@example.edu','Physics',2021,NULL,'open','2026-02-07',NULL),
('STU004','Diana','Smith','diana.smith@example.edu','Chemistry',2022,65,'closed','2026-02-06','2026-02-10'),
('STU004','Diana','Smith','diana.s@example.edu','Chemistry',2022,65,'closed','2026-02-06','2026-02-10'),
('STU005','Emeka','Johnson','emeka.j@example.edu','Biology',2020,44,'open','2026-02-08','2026-02-12');

INSERT INTO student_records_target VALUES
('STU001','Alice','Nguyen','alice.nguyen@example.edu','Computer Science',2022,78,'closed','2026-02-10','2026-02-08'),
('STU002','Bob','Mensah','bob.mensah@example.edu','Mathematics',2022,90,'open','2026-02-09',NULL),
('STU003','Chidi','Okoro','chidi.okoro@example.edu','Physics',2021,56,'open','2026-02-07',NULL),
('STU006','Fatima','Bello','fatima.bello@example.edu','Statistics',2023,81,'open','2026-02-11',NULL);

INSERT INTO exam_tasks VALUES
('TSK001','Ops Team','Device Compliance','open','2026-02-08',NULL,'high'),
('TSK002','Invigilation','Hall Readiness','in_progress','2026-02-10',NULL,'medium'),
('TSK003','Network Team','CCTV Connectivity','completed','2026-02-07','2026-02-06','high'),
('TSK004','Support Team','Biometric Calibration','open','2026-02-09',NULL,'high'),
('TSK005','Facilities','Power Backup Check','completed','2026-02-05','2026-02-07','medium'),
('TSK006','Audit Desk','Evidence Packet Review','open','2026-02-11',NULL,'low');
