-- LifeConnect development data. FULLY SYNTHETIC: no real people, emails or phone numbers.
-- Schema: current ORM tables (apply `alembic upgrade head` first).
-- Every account password is the documented DEV-ONLY password: DevOnly#2026
-- NEVER load this into a production database.

-- Bootstrap admin so the first invite can be sent. Change/remove outside local dev.
INSERT INTO admin_details (id, email, password, username, authentication_id, vec_registration_number, date_of_birth, mobile_number, department, active_status, last_login_date, approved_donation_count, closed_requests_count, created_at) VALUES
('ADM-DEV001', 'admin1@example.com', '$2b$12$rmqkEn1uq9q49EzESySvo.FC0mMOk.oE5nweRGb0M9uxJiRNucn0S', 'Dev Admin One', 'AUTHADM-DEV001', 'VEC-DEV-0001', '1990-01-01', '9000000001', 'Operations', 'Active', NULL, 0, 0, '2026-01-01 00:00:00');
