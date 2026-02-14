/*
  Duplicate finder (Postgres)
  Adapt table and key columns as needed.
*/

-- Example: duplicates by student_id + email
SELECT
  student_id,
  email,
  COUNT(*) AS duplicate_count
FROM student_records_source
GROUP BY student_id, email
HAVING COUNT(*) > 1
ORDER BY duplicate_count DESC, student_id, email;

-- Example: fetch full duplicate rows by student_id
SELECT s.*
FROM student_records_source s
JOIN (
  SELECT student_id
  FROM student_records_source
  GROUP BY student_id
  HAVING COUNT(*) > 1
) d ON d.student_id = s.student_id
ORDER BY s.student_id;
