/*
  Academic results integrity checks (SQLite)
  Expected table: student_records_source
*/

SELECT 'missing_or_invalid_score' AS check_name, COUNT(*) AS issue_count
FROM student_records_source
WHERE score IS NULL OR score < 0 OR score > 100

UNION ALL

SELECT 'duplicate_student_id' AS check_name, COUNT(*) AS issue_count
FROM (
  SELECT student_id
  FROM student_records_source
  GROUP BY student_id
  HAVING COUNT(*) > 1
) d

UNION ALL

SELECT 'missing_required_fields' AS check_name, COUNT(*) AS issue_count
FROM student_records_source
WHERE student_id IS NULL OR TRIM(student_id) = ''
   OR email IS NULL OR TRIM(email) = ''
   OR department IS NULL OR TRIM(department) = ''

UNION ALL

SELECT 'invalid_status_values' AS check_name, COUNT(*) AS issue_count
FROM student_records_source
WHERE status IS NULL
   OR LOWER(TRIM(status)) NOT IN ('open', 'closed', 'in_progress', 'completed')

UNION ALL

SELECT 'completed_after_due_date' AS check_name, COUNT(*) AS issue_count
FROM student_records_source
WHERE completed_at IS NOT NULL
  AND due_date IS NOT NULL
  AND completed_at > due_date;

-- Detailed duplicate rows
SELECT s.*
FROM student_records_source s
JOIN (
  SELECT student_id
  FROM student_records_source
  GROUP BY student_id
  HAVING COUNT(*) > 1
) d ON d.student_id = s.student_id
ORDER BY s.student_id;
