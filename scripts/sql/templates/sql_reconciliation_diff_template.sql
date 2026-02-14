/*
  Reconciliation diff template (portable pattern)

  Replace placeholders:
  - <SOURCE_TABLE>
  - <TARGET_TABLE>
  - <KEY_COLUMN>
  - <COMPARE_COL_1>, <COMPARE_COL_2>, ...

  Notes:
  - For Postgres, you can use FULL OUTER JOIN directly.
  - For MySQL, emulate FULL OUTER JOIN with UNION ALL of left/right joins.
  - Prefer NULL-safe comparisons where available.
*/

WITH source_data AS (
  SELECT
    <KEY_COLUMN> AS record_key,
    <COMPARE_COL_1>,
    <COMPARE_COL_2>
  FROM <SOURCE_TABLE>
),
target_data AS (
  SELECT
    <KEY_COLUMN> AS record_key,
    <COMPARE_COL_1>,
    <COMPARE_COL_2>
  FROM <TARGET_TABLE>
)
SELECT
  COALESCE(s.record_key, t.record_key) AS record_key,
  CASE
    WHEN s.record_key IS NULL THEN 'target_only'
    WHEN t.record_key IS NULL THEN 'source_only'
    WHEN (
      COALESCE(s.<COMPARE_COL_1>, '') <> COALESCE(t.<COMPARE_COL_1>, '')
      OR COALESCE(s.<COMPARE_COL_2>, '') <> COALESCE(t.<COMPARE_COL_2>, '')
    ) THEN 'mismatch'
    ELSE 'match'
  END AS reconciliation_status,
  s.<COMPARE_COL_1> AS source_<COMPARE_COL_1>,
  t.<COMPARE_COL_1> AS target_<COMPARE_COL_1>,
  s.<COMPARE_COL_2> AS source_<COMPARE_COL_2>,
  t.<COMPARE_COL_2> AS target_<COMPARE_COL_2>
FROM source_data s
FULL OUTER JOIN target_data t
  ON s.record_key = t.record_key
ORDER BY record_key;
