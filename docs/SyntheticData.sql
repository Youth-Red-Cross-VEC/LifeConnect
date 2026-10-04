-- LifeConnect development data. FULLY SYNTHETIC: no real people, emails or phone numbers.
-- Schema: current ORM tables (apply `alembic upgrade head` first).
-- Every account password is the documented DEV-ONLY password: DevOnly#2026
-- NEVER load this into a production database.

INSERT INTO admin_details (id, email, password, username, authentication_id, vec_registration_number, date_of_birth, mobile_number, department, active_status, last_login_date, approved_donation_count, closed_requests_count, created_at) VALUES
('ADM-DEV001', 'admin1@example.com', '$2b$12$rmqkEn1uq9q49EzESySvo.FC0mMOk.oE5nweRGb0M9uxJiRNucn0S', 'Dev Admin 1', 'AUTHADM-DEV001', 'VEC-DEV-0001', '1990-01-01', '9000000001', 'Operations', 'Active', NULL, 0, 0, '2026-01-01 00:00:00'),
('ADM-DEV002', 'admin2@example.com', '$2b$12$rmqkEn1uq9q49EzESySvo.FC0mMOk.oE5nweRGb0M9uxJiRNucn0S', 'Dev Admin 2', 'AUTHADM-DEV002', 'VEC-DEV-0002', '1990-01-02', '9000000002', 'Operations', 'Active', NULL, 0, 0, '2026-01-01 00:00:00');

INSERT INTO terms_and_conditions (id, version, effective_date) VALUES
('TC-DEV001', '1.0', '2026-01-01');

INSERT INTO personal_details (id, first_name, last_name, age, date_of_birth, contact_number, secondary_contact_number, marital_status, created_at) VALUES
('PD-DEV001', 'Asha', 'Rao', 26, '1998-02-11', '9000010001', NULL, 'Single', '2026-01-01 00:00:00'),
('PD-DEV002', 'Ravi', 'Kumar', 27, '1997-03-12', '9000010002', NULL, 'Single', '2026-01-01 00:00:00'),
('PD-DEV003', 'Meena', 'Iyer', 28, '1996-04-13', '9000010003', NULL, 'Single', '2026-01-01 00:00:00'),
('PD-DEV004', 'Karthik', 'Nair', 29, '1995-05-14', '9000010004', NULL, 'Single', '2026-01-01 00:00:00'),
('PD-DEV005', 'Divya', 'Menon', 30, '1994-06-15', '9000010005', NULL, 'Single', '2026-01-01 00:00:00'),
('PD-DEV006', 'Arun', 'Das', 31, '1993-07-16', '9000010006', NULL, 'Single', '2026-01-01 00:00:00'),
('PD-DEV007', 'Priya', 'Sharma', 32, '1992-08-17', '9000010007', NULL, 'Single', '2026-01-01 00:00:00'),
('PD-DEV008', 'Vikram', 'Singh', 33, '1991-09-18', '9000010008', NULL, 'Single', '2026-01-01 00:00:00'),
('PD-DEV009', 'Sana', 'Khan', 34, '1990-01-10', '9000010009', NULL, 'Single', '2026-01-01 00:00:00'),
('PD-DEV010', 'Tom', 'Joseph', 35, '1989-02-11', '9000010010', NULL, 'Single', '2026-01-01 00:00:00');

INSERT INTO address_details (id, address, pincode, country, state, city, created_at) VALUES
('AD-DEV001', '1 Sample Street, Example Nagar', '600001', 'India', 'Tamil Nadu', 'Chennai', '2026-01-01 00:00:00'),
('AD-DEV002', '2 Sample Street, Example Nagar', '600002', 'India', 'Tamil Nadu', 'Chennai', '2026-01-01 00:00:00'),
('AD-DEV003', '3 Sample Street, Example Nagar', '600003', 'India', 'Tamil Nadu', 'Coimbatore', '2026-01-01 00:00:00'),
('AD-DEV004', '4 Sample Street, Example Nagar', '600004', 'India', 'Tamil Nadu', 'Madurai', '2026-01-01 00:00:00'),
('AD-DEV005', '5 Sample Street, Example Nagar', '600005', 'India', 'Tamil Nadu', 'Chennai', '2026-01-01 00:00:00'),
('AD-DEV006', '6 Sample Street, Example Nagar', '600006', 'India', 'Tamil Nadu', 'Trichy', '2026-01-01 00:00:00'),
('AD-DEV007', '7 Sample Street, Example Nagar', '600007', 'India', 'Tamil Nadu', 'Salem', '2026-01-01 00:00:00'),
('AD-DEV008', '8 Sample Street, Example Nagar', '600008', 'India', 'Tamil Nadu', 'Chennai', '2026-01-01 00:00:00'),
('AD-DEV009', '9 Sample Street, Example Nagar', '600009', 'India', 'Tamil Nadu', 'Madurai', '2026-01-01 00:00:00'),
('AD-DEV010', '10 Sample Street, Example Nagar', '600010', 'India', 'Tamil Nadu', 'Coimbatore', '2026-01-01 00:00:00');

INSERT INTO disease_details (id, name, description) VALUES
('DS-DEV001', 'None', NULL),
('DS-DEV002', 'None', NULL),
('DS-DEV003', 'None', NULL),
('DS-DEV004', 'None', NULL),
('DS-DEV005', 'None', NULL),
('DS-DEV006', 'None', NULL),
('DS-DEV007', 'None', NULL),
('DS-DEV008', 'None', NULL),
('DS-DEV009', 'None', NULL),
('DS-DEV010', 'None', NULL);

INSERT INTO donor_details (id, name, email, password, blood_group, active_status, authentication_id, last_donated_date, number_of_times_donated, last_login_date, personal_details_id, address_id, disease_id, terms_and_conditions_id, created_at) VALUES
('DON-DEV001', 'Asha Rao', 'donor1@example.com', '$2b$12$rmqkEn1uq9q49EzESySvo.FC0mMOk.oE5nweRGb0M9uxJiRNucn0S', 'A+', true, 'AUTH-DEV001', NULL, 0, NULL, 'PD-DEV001', 'AD-DEV001', 'DS-DEV001', 'TC-DEV001', '2026-01-01 00:00:00'),
('DON-DEV002', 'Ravi Kumar', 'donor2@example.com', '$2b$12$rmqkEn1uq9q49EzESySvo.FC0mMOk.oE5nweRGb0M9uxJiRNucn0S', 'B+', true, 'AUTH-DEV002', NULL, 0, NULL, 'PD-DEV002', 'AD-DEV002', 'DS-DEV002', 'TC-DEV001', '2026-01-01 00:00:00'),
('DON-DEV003', 'Meena Iyer', 'donor3@example.com', '$2b$12$rmqkEn1uq9q49EzESySvo.FC0mMOk.oE5nweRGb0M9uxJiRNucn0S', 'O+', true, 'AUTH-DEV003', NULL, 0, NULL, 'PD-DEV003', 'AD-DEV003', 'DS-DEV003', 'TC-DEV001', '2026-01-01 00:00:00'),
('DON-DEV004', 'Karthik Nair', 'donor4@example.com', '$2b$12$rmqkEn1uq9q49EzESySvo.FC0mMOk.oE5nweRGb0M9uxJiRNucn0S', 'AB+', true, 'AUTH-DEV004', NULL, 0, NULL, 'PD-DEV004', 'AD-DEV004', 'DS-DEV004', 'TC-DEV001', '2026-01-01 00:00:00'),
('DON-DEV005', 'Divya Menon', 'donor5@example.com', '$2b$12$rmqkEn1uq9q49EzESySvo.FC0mMOk.oE5nweRGb0M9uxJiRNucn0S', 'O-', true, 'AUTH-DEV005', NULL, 0, NULL, 'PD-DEV005', 'AD-DEV005', 'DS-DEV005', 'TC-DEV001', '2026-01-01 00:00:00'),
('DON-DEV006', 'Arun Das', 'donor6@example.com', '$2b$12$rmqkEn1uq9q49EzESySvo.FC0mMOk.oE5nweRGb0M9uxJiRNucn0S', 'A-', true, 'AUTH-DEV006', NULL, 0, NULL, 'PD-DEV006', 'AD-DEV006', 'DS-DEV006', 'TC-DEV001', '2026-01-01 00:00:00'),
('DON-DEV007', 'Priya Sharma', 'donor7@example.com', '$2b$12$rmqkEn1uq9q49EzESySvo.FC0mMOk.oE5nweRGb0M9uxJiRNucn0S', 'B-', true, 'AUTH-DEV007', NULL, 0, NULL, 'PD-DEV007', 'AD-DEV007', 'DS-DEV007', 'TC-DEV001', '2026-01-01 00:00:00'),
('DON-DEV008', 'Vikram Singh', 'donor8@example.com', '$2b$12$rmqkEn1uq9q49EzESySvo.FC0mMOk.oE5nweRGb0M9uxJiRNucn0S', 'AB-', true, 'AUTH-DEV008', NULL, 0, NULL, 'PD-DEV008', 'AD-DEV008', 'DS-DEV008', 'TC-DEV001', '2026-01-01 00:00:00'),
('DON-DEV009', 'Sana Khan', 'donor9@example.com', '$2b$12$rmqkEn1uq9q49EzESySvo.FC0mMOk.oE5nweRGb0M9uxJiRNucn0S', 'O+', true, 'AUTH-DEV009', NULL, 0, NULL, 'PD-DEV009', 'AD-DEV009', 'DS-DEV009', 'TC-DEV001', '2026-01-01 00:00:00'),
('DON-DEV010', 'Tom Joseph', 'donor10@example.com', '$2b$12$rmqkEn1uq9q49EzESySvo.FC0mMOk.oE5nweRGb0M9uxJiRNucn0S', 'A+', false, 'AUTH-DEV010', NULL, 0, NULL, 'PD-DEV010', 'AD-DEV010', 'DS-DEV010', 'TC-DEV001', '2026-01-01 00:00:00');

INSERT INTO hospital_details (id, hospital_name, hospital_address, pincode, city, state, country, branch, landmark, created_at) VALUES
('HOSP-DEV001', 'Example General Hospital 1', '1 Hospital Road', '600101', 'Chennai', 'Tamil Nadu', 'India', 'Main', 'Near Example Park', '2026-01-01 00:00:00'),
('HOSP-DEV002', 'Example General Hospital 2', '2 Hospital Road', '600102', 'Chennai', 'Tamil Nadu', 'India', 'Main', 'Near Example Park', '2026-01-01 00:00:00'),
('HOSP-DEV003', 'Example General Hospital 3', '3 Hospital Road', '600103', 'Coimbatore', 'Tamil Nadu', 'India', 'Main', 'Near Example Park', '2026-01-01 00:00:00');

INSERT INTO response_details (id, status, report, units_donated, certificate_status, donation_date, donor_ids, created_at) VALUES
('RESP-DEV001', NULL, NULL, NULL, NULL, NULL, NULL, '2026-01-01 00:00:00'),
('RESP-DEV002', NULL, NULL, NULL, NULL, NULL, NULL, '2026-01-01 00:00:00');

INSERT INTO blood_request_details (id, patient_name, blood_group, hospital_name, contact_number, patient_age, due_date, request_reason, status, units_required, attendant_name, hospital_id, response_id, created_at) VALUES
('REQ-DEV001', 'Sample Patient A', 'O+', 'Example General Hospital 1', '9000200001', 40, '2026-12-31 00:00:00', 'Surgery', 'Pending', 2, 'Sample Attendant', 'HOSP-DEV001', 'RESP-DEV001', '2026-01-01 00:00:00'),
('REQ-DEV002', 'Sample Patient B', 'A+', 'Example General Hospital 2', '9000200002', 30, '2026-12-31 00:00:00', 'Accident', 'Approved', 1, 'Sample Attendant', 'HOSP-DEV002', 'RESP-DEV002', '2026-01-01 00:00:00');

INSERT INTO query_table (user_name, user_email, admin_id, admin_name, user_query, admin_response, user_query_date, admin_response_date, created_at) VALUES
('Sample User', 'user@example.com', 'PENDING', 'PENDING', 'How do I update my donor details?', NULL, '2026-01-02', NULL, '2026-01-01 00:00:00');
