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
('STU005','Emeka','Johnson','emeka.j@example.edu','Biology',2020,44,'open','2026-02-08','2026-02-12'),
('STU006','Fatima','Bello','fatima.bello@example.edu','Statistics',2023,81,'open','2026-02-11',NULL),
('STU007','Grace','Adeyemi','grace.adeyemi@example.edu','Economics',2021,88,'completed','2026-02-12','2026-02-11'),
('STU008','Hamza','Yusuf','hamza.yusuf@example.edu','Computer Engineering',2022,73,'in_progress','2026-02-13',NULL),
('STU009','Ifeoma','Udo','ifeoma.udo@example.edu','Information Systems',2020,95,'completed','2026-02-08','2026-02-08'),
('STU010','Jacob','Obi','jacob.obi@example.edu','Civil Engineering',2021,59,'open','2026-02-05',NULL),
('STU010','Jacob','Obi','jacob.obi.alt@example.edu','Civil Engineering',2021,59,'open','2026-02-05',NULL),
('STU011','Kemi','Afolabi','kemi.afolabi@example.edu','Accounting',2023,67,'open','2026-02-14',NULL),
('STU012','Luis','Gomez','luis.gomez@example.edu','Mechanical Engineering',2022,83,'closed','2026-02-03','2026-02-01'),
('STU013','Mary','Nwosu','mary.nwosu@example.edu','Law',2023,0,'open','2026-02-15',NULL),
('STU014','Nia','Patel','nia.patel@example.edu','Nursing',2024,91,'completed','2026-02-10','2026-02-10'),
('STU015','Omar','Farouk','omar.farouk@example.edu','Architecture',2021,48,'pending_review','2026-02-09',NULL),
('STU016','Priya','Singh','priya.singh@example.edu','Computer Science',2024,76,'in_progress','2026-02-16',NULL),
('STU017','Qiang','Lee','qiang.lee@example.edu','Data Science',2023,85,'open','2026-02-18',NULL),
('STU018','Ruth','Danjuma','ruth.danjuma@example.edu','Public Administration',2022,62,'closed','2026-02-04','2026-02-05'),
('STU019','Samuel','Eze','samuel.eze@example.edu','Nursing',2020,54,'open','2026-02-07','2026-02-09'),
('STU020','Tolu','Ibrahim','tolu.ibrahim@example.edu','Cybersecurity',2024,89,'completed','2026-02-17','2026-02-15'),
('STU021','Uche','Okafor',NULL,'Computer Science',2022,72,'open','2026-02-11',NULL),
('STU022','Vera','Chen','vera.chen@example.edu',NULL,2021,79,'open','2026-02-12',NULL),
('STU023','Will','Brown','will.brown@example.edu','Mathematics',2022,-4,'open','2026-02-12',NULL),
('STU024','Xena','Ali','xena.ali@example.edu','Physics',2022,106,'open','2026-02-12',NULL);

INSERT INTO student_records_target VALUES
('STU001','Alice','Nguyen','alice.nguyen@example.edu','Computer Science',2022,78,'closed','2026-02-10','2026-02-08'),
('STU002','Bob','Mensah','bob.mensah@example.edu','Mathematics',2022,90,'open','2026-02-09',NULL),
('STU003','Chidi','Okoro','chidi.okoro@example.edu','Physics',2021,56,'open','2026-02-07',NULL),
('STU004','Diana','Smith','diana.smith@example.edu','Chemistry',2022,65,'closed','2026-02-06','2026-02-10'),
('STU006','Fatima','Bello','fatima.bello@example.edu','Statistics',2023,81,'open','2026-02-11',NULL),
('STU007','Grace','Adeyemi','grace.adeyemi@example.edu','Economics',2021,88,'completed','2026-02-12','2026-02-11'),
('STU008','Hamza','Yusuf','hamza.yusuf@example.edu','Computer Engineering',2022,75,'in_progress','2026-02-13',NULL),
('STU009','Ifeoma','Udo','ifeoma.udo@example.edu','Information Systems',2020,95,'completed','2026-02-08','2026-02-08'),
('STU011','Kemi','Afolabi','kemi.afolabi@example.edu','Accounting',2023,67,'open','2026-02-14',NULL),
('STU012','Luis','Gomez','luis.gomez@example.edu','Mechanical Engineering',2022,83,'closed','2026-02-03','2026-02-01'),
('STU013','Mary','Nwosu','mary.nwosu@example.edu','Law',2023,52,'open','2026-02-15',NULL),
('STU014','Nia','Patel','nia.patel@example.edu','Nursing',2024,91,'completed','2026-02-10','2026-02-10'),
('STU016','Priya','Singh','priya.singh@example.edu','Computer Science',2024,76,'open','2026-02-16',NULL),
('STU017','Qiang','Lee','qiang.lee@example.edu','Data Science',2023,85,'open','2026-02-18',NULL),
('STU018','Ruth','Danjuma','ruth.danjuma@example.edu','Public Administration',2022,62,'closed','2026-02-04','2026-02-05'),
('STU019','Samuel','Eze','samuel.eze@example.edu','Nursing',2020,54,'open','2026-02-07','2026-02-09'),
('STU020','Tolu','Ibrahim','tolu.ibrahim@example.edu','Cybersecurity',2024,89,'completed','2026-02-17','2026-02-15'),
('STU022','Vera','Chen','vera.chen@example.edu','Information Systems',2021,79,'open','2026-02-12',NULL),
('STU025','Yara','Abbas','yara.abbas@example.edu','Architecture',2024,84,'open','2026-02-19',NULL),
('STU026','Zain','Adeniji','zain.adeniji@example.edu','Physics',2023,77,'open','2026-02-20',NULL);

INSERT INTO exam_tasks VALUES
('TSK001','Ops Team','Device Compliance','open','2026-02-08',NULL,'high'),
('TSK002','Invigilation','Hall Readiness','in_progress','2026-02-10',NULL,'medium'),
('TSK003','Network Team','CCTV Connectivity','completed','2026-02-07','2026-02-06','high'),
('TSK004','Support Team','Biometric Calibration','open','2026-02-09',NULL,'high'),
('TSK005','Facilities','Power Backup Check','completed','2026-02-05','2026-02-07','medium'),
('TSK006','Audit Desk','Evidence Packet Review','open','2026-02-11',NULL,'low'),
('TSK007','Admissions Office','Applicant Identity Recheck','in_progress','2026-02-12',NULL,'high'),
('TSK008','Results Unit','Grade Sheet Consolidation','open','2026-02-13',NULL,'high'),
('TSK009','Registry','Result Approval Pack Assembly','open','2026-02-14',NULL,'high'),
('TSK010','Database Team','Result Backup Verification','completed','2026-02-09','2026-02-09','medium'),
('TSK011','QA Desk','Anomaly Revalidation','open','2026-02-10',NULL,'medium'),
('TSK012','Security Team','Exam Hall Access Audit','completed','2026-02-08','2026-02-08','high'),
('TSK013','Compliance Unit','CCTV Evidence Hashing','open','2026-02-15',NULL,'medium'),
('TSK014','IT Support','Biometric Device Firmware Check','in_progress','2026-02-16',NULL,'high'),
('TSK015','Reporting Team','Leadership KPI Snapshot','open','2026-02-17',NULL,'medium'),
('TSK016','Helpdesk','Candidate Ticket Clearance','completed','2026-02-11','2026-02-12','low'),
('TSK017','Network Team','Switch Port Validation','open','2026-02-12',NULL,'medium'),
('TSK018','Ops Team','Exam Script Pickup Chain Log','open','2026-02-18',NULL,'low');
