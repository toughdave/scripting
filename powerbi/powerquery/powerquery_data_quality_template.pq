let
    // Power Query data-quality staging template
    // Replace Source with your connector query (Excel.Workbook, Csv.Document, Sql.Database, etc.)
    Source = #table(
        {"student_id", "email", "score", "status"},
        {
            {"STU001", "alice.nguyen@example.edu", 78, "open"},
            {"STU002", "bob.mensah@example.edu", null, "open"},
            {"", "bad-email", 101, "closed"}
        }
    ),

    Typed = Table.TransformColumnTypes(
        Source,
        {
            {"student_id", type text},
            {"email", type text},
            {"score", Int64.Type},
            {"status", type text}
        }
    ),

    AddDQFlags = Table.AddColumn(
        Typed,
        "dq_issue",
        each
            if [student_id] = null or Text.Trim([student_id]) = "" then "missing_student_id"
            else if [email] = null or Text.PositionOf([email], "@") < 1 then "invalid_email"
            else if [score] = null then "missing_score"
            else if [score] < 0 or [score] > 100 then "invalid_score_range"
            else if [status] = null or not List.Contains({"open", "closed", "in_progress", "completed"}, Text.Lower(Text.Trim([status]))) then "invalid_status"
            else null,
        type text
    ),

    AddDQStatus = Table.AddColumn(
        AddDQFlags,
        "dq_status",
        each if [dq_issue] = null then "pass" else "fail",
        type text
    ),

    // Keep everything for audit; optionally filter to fails in a separate query.
    Result = AddDQStatus
in
    Result
