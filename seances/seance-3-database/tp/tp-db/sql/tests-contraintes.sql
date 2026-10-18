-- All test data is rolled back; only SERIAL sequence gaps can remain.
\set ON_ERROR_STOP on
\pset pager off
BEGIN;

-- Require the right SQLSTATE AND constraint name, not just any error.
CREATE FUNCTION pg_temp.expect_failure(statement TEXT, expected_state TEXT,
                                        expected_constraint TEXT)
RETURNS TABLE (constraint_name TEXT, sqlstate TEXT, message TEXT, detail TEXT)
LANGUAGE plpgsql AS $$
DECLARE
    actual_state TEXT;
    actual_constraint TEXT;
    actual_message TEXT;
    actual_detail TEXT;
BEGIN
    BEGIN
        EXECUTE statement;
    EXCEPTION WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS
            actual_state = RETURNED_SQLSTATE,
            actual_constraint = CONSTRAINT_NAME,
            actual_message = MESSAGE_TEXT,
            actual_detail = PG_EXCEPTION_DETAIL;
        IF actual_state IS DISTINCT FROM expected_state
           OR actual_constraint IS DISTINCT FROM expected_constraint THEN
            RAISE EXCEPTION 'Wrong failure: expected %/%, got %/%: %',
                expected_state, expected_constraint, actual_state,
                actual_constraint, actual_message;
        END IF;
        RETURN QUERY SELECT actual_constraint, actual_state,
                            actual_message, actual_detail;
        RETURN;
    END;
    RAISE EXCEPTION 'Statement unexpectedly succeeded: %', statement;
END;
$$;

\echo '1. Score 6: CHECK, not a duplicate review'
SELECT * FROM pg_temp.expect_failure($sql$
    INSERT INTO avis (reservation_id, note) VALUES (1, 6)
$sql$, '23514', 'avis_note_check');

-- Valid fixture: Bob's completed reservation 1, with optional comment omitted.
INSERT INTO avis (reservation_id, note) VALUES (1, 5);

\echo '2. Two reviews for the same reservation: UNIQUE'
SELECT * FROM pg_temp.expect_failure($sql$
    INSERT INTO avis (reservation_id, note) VALUES (1, 4)
$sql$, '23505', 'avis_reservation_key');

INSERT INTO tags (libelle) VALUES ('velo'), ('sport');

\echo '3. Duplicate tag label: UNIQUE'
SELECT * FROM pg_temp.expect_failure($sql$
    INSERT INTO tags (libelle) VALUES ('velo')
$sql$, '23505', 'tags_libelle_key');

\echo '4. Review for nonexistent reservation: FOREIGN KEY'
SELECT * FROM pg_temp.expect_failure($sql$
    INSERT INTO avis (reservation_id, note) VALUES (-1, 4)
$sql$, '23503', 'avis_reservation_fkey');

\echo '5. Review for an active reservation: composite FOREIGN KEY'
SELECT * FROM pg_temp.expect_failure($sql$
    INSERT INTO avis (reservation_id, note) VALUES (2, 4)
$sql$, '23503', 'avis_reservation_fkey');

\echo '6. Uppercase tag: CHECK'
SELECT * FROM pg_temp.expect_failure($sql$
    INSERT INTO tags (libelle) VALUES ('Sport')
$sql$, '23514', 'tags_libelle_lower_check');

\echo '7. Overlapping active reservations: EXCLUSION'
SELECT * FROM pg_temp.expect_failure($sql$
    INSERT INTO reservations (item_id, borrower_id, date_debut, date_fin)
    VALUES (3, 3, '2026-09-11', '2026-09-13')
$sql$, '23P01', 'reservations_active_no_overlap');

-- Allowed: adjacent dates, another item, and overlapping inactive bookings.
INSERT INTO reservations (item_id, borrower_id, date_debut, date_fin, statut)
VALUES (3, 3, '2026-09-12', '2026-09-14', 'active'),
       (2, 3, '2026-09-10', '2026-09-12', 'active'),
       (3, 3, '2026-09-10', '2026-09-12', 'annulee');

\echo '8. Changing an overlapping booking to active: EXCLUSION'
SELECT * FROM pg_temp.expect_failure($sql$
    UPDATE reservations SET statut = 'active'
    WHERE item_id = 3 AND statut = 'annulee'
      AND date_debut = DATE '2026-09-10'
$sql$, '23P01', 'reservations_active_no_overlap');

-- Two tags on one item, and the same tag on another item: both allowed.
INSERT INTO item_tags (item_id, tag_id)
SELECT 1, id FROM tags WHERE libelle IN ('velo', 'sport');
INSERT INTO item_tags (item_id, tag_id)
SELECT 2, id FROM tags WHERE libelle = 'sport';

\echo '9. Duplicate item/tag pair: composite PRIMARY KEY'
SELECT * FROM pg_temp.expect_failure($sql$
    INSERT INTO item_tags (item_id, tag_id)
    SELECT 1, id FROM tags WHERE libelle = 'velo'
$sql$, '23505', 'item_tags_pkey');

\echo '10. Cannot change a reviewed booking away from terminee'
SELECT * FROM pg_temp.expect_failure($sql$
    UPDATE reservations SET statut = 'active' WHERE id = 1
$sql$, '23503', 'avis_reservation_fkey');

\echo '11. Cannot bypass completion by supplying another review status'
SELECT * FROM pg_temp.expect_failure($sql$
    INSERT INTO avis (reservation_id, reservation_statut, note)
    VALUES (2, 'active', 4)
$sql$, '23514', 'avis_reservation_statut_check');

\echo '12. Score 0: lower CHECK boundary'
SELECT * FROM pg_temp.expect_failure($sql$
    INSERT INTO avis (reservation_id, note) VALUES (-1, 0)
$sql$, '23514', 'avis_note_check');

\echo 'All 12 expected failures matched the correct SQLSTATE and constraint.'
ROLLBACK;
