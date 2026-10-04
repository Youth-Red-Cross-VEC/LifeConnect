-- Tiny SYNTHETIC legacy dump (old Flask/MySQL schema). No real data.
CREATE TABLE `termsandconditions` (
  `id` varchar(36) NOT NULL,
  `version` varchar(20) NOT NULL,
  `effective_date` date NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
INSERT INTO `termsandconditions` VALUES ('TC001','1.0','2024-01-01');
CREATE TABLE `personaldetailsuser` (
  `id` varchar(36) NOT NULL,
  `first_name` varchar(45) NOT NULL,
  `last_name` varchar(45) DEFAULT NULL,
  `age` int NOT NULL,
  `date_of_birth` date NOT NULL,
  `contact_number` varchar(15) NOT NULL,
  `secondary_contact_number` varchar(15) DEFAULT NULL,
  `marital_status` varchar(10) DEFAULT NULL,
  `aadhar_number` varchar(20) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
INSERT INTO `personaldetailsuser` VALUES ('PD001','Test','O\'Brien',30,'1994-05-12','9000000001',NULL,'Single','0000-0000-0000'),('PD002','Jane','Doe',28,'1996-02-15','9000000002','9000000003','Married',NULL);
CREATE TABLE `addressdetailsuser` (
  `id` varchar(36) NOT NULL,
  `address` varchar(200) NOT NULL,
  `pincode` varchar(10) NOT NULL,
  `country` varchar(45) NOT NULL,
  `state` varchar(45) NOT NULL,
  `city` varchar(45) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
INSERT INTO `addressdetailsuser` VALUES ('AD001','1 Sample St, Line\\2','600001','India','Tamil Nadu','Chennai'),('AD002','2 Sample St','600002','India','Tamil Nadu','Chennai');
CREATE TABLE `diseasedetailsuser` (
  `id` varchar(36) NOT NULL,
  `name` varchar(100) NOT NULL,
  `description` varchar(200) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
INSERT INTO `diseasedetailsuser` VALUES ('DS001','None',NULL),('DS002','None',NULL);
CREATE TABLE `donordetail` (
  `id` varchar(36) NOT NULL,
  `name` varchar(100) NOT NULL,
  `email` varchar(100) NOT NULL,
  `password` varchar(500) NOT NULL,
  `blood_group` varchar(10) NOT NULL,
  `personal_details_id` varchar(36) NOT NULL,
  `terms_and_conditions_id` varchar(36) NOT NULL,
  `address_id` varchar(36) NOT NULL,
  `active_status` tinyint(1) NOT NULL,
  `disease_id` varchar(36) NOT NULL,
  `authentication_id` varchar(36) NOT NULL,
  `last_donated_date` datetime DEFAULT NULL,
  `number_of_times_donated` int NOT NULL,
  `last_login_date` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
INSERT INTO `donordetail` VALUES ('DNR001','Test OBrien','legacy1@example.com','scrypt:32768:8:1$salt$abcdef','O+','PD001','TC001','AD001',1,'DS001','AUTH001','2024-02-01 10:30:00',2,NULL),('DNR002','Jane Doe','legacy2@example.com','scrypt:32768:8:1$salt$123456','A+','PD002','TC001','AD002',0,'DS002','AUTH002',NULL,0,'2024-03-01 08:00:00');
CREATE TABLE `admindetails` (
  `id` varchar(36) NOT NULL,
  `email` varchar(100) NOT NULL,
  `password` varchar(250) NOT NULL,
  `username` varchar(45) NOT NULL,
  `authentication_id` varchar(36) NOT NULL,
  `vec_registration_number` varchar(36) NOT NULL,
  `data_of_birth` date NOT NULL,
  `mobile_number` varchar(36) NOT NULL,
  `department` varchar(50) DEFAULT NULL,
  `active_status` varchar(36) NOT NULL,
  `last_login_date` datetime DEFAULT NULL,
  `approved_donation_count` int NOT NULL,
  `closed_requests_count` int NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
INSERT INTO `admindetails` VALUES ('ADMIN001','legacyadmin@example.com','scrypt:32768:8:1$salt$aa','Legacy Admin','AUTHADM001','VEC001','1990-01-01','9000000009','IT','Active',NULL,1,0);
CREATE TABLE `hospitaldetails` (
  `id` varchar(36) NOT NULL,
  `hospital_name` varchar(100) NOT NULL,
  `hospital_address` varchar(200) NOT NULL,
  `pincode` varchar(10) NOT NULL,
  `city` varchar(45) NOT NULL,
  `state` varchar(45) NOT NULL,
  `country` varchar(45) NOT NULL,
  `branch` varchar(45) DEFAULT NULL,
  `landmark` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
INSERT INTO `hospitaldetails` VALUES ('HOSP001','Example Hospital','1 Road','600001','Chennai','Tamil Nadu','India',NULL,NULL);
CREATE TABLE `responsedetails` (
  `id` varchar(36) NOT NULL,
  `status` varchar(45) DEFAULT NULL,
  `report` varchar(255) DEFAULT NULL,
  `units_donated` int DEFAULT NULL,
  `certificate_status` varchar(36) DEFAULT NULL,
  `donation_date` date DEFAULT NULL,
  `donor_ids` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
INSERT INTO `responsedetails` VALUES ('RESP001','Completed','ok',1,'Sent','2024-02-01','DNR001');
CREATE TABLE `bloodrequestdetails` (
  `id` varchar(36) NOT NULL,
  `patient_name` varchar(100) NOT NULL,
  `blood_group` varchar(10) NOT NULL,
  `hospital_name` varchar(100) NOT NULL,
  `hospital_id` varchar(36) NOT NULL,
  `contact_number` varchar(15) NOT NULL,
  `patient_age` int NOT NULL,
  `due_date` datetime NOT NULL,
  `request_reason` varchar(200) DEFAULT NULL,
  `status` varchar(45) NOT NULL,
  `units_required` int NOT NULL,
  `attendant_name` varchar(100) DEFAULT NULL,
  `response_id` varchar(36) NOT NULL,
  `approved_admin_id` varchar(36) DEFAULT NULL,
  `closed_admin_id` varchar(36) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
INSERT INTO `bloodrequestdetails` VALUES ('REQ001','Sample Patient','O+','Example Hospital','HOSP001','9000200001',40,'2024-02-10 00:00:00','Surgery','Closed',1,'Attendant','RESP001','ADMIN001','ADMIN001');
CREATE TABLE `querytable` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_name` varchar(55) NOT NULL,
  `user_email` varchar(55) NOT NULL,
  `admin_id` varchar(55) NOT NULL,
  `admin_name` varchar(55) NOT NULL,
  `user_query` varchar(555) DEFAULT NULL,
  `admin_response` varchar(555) DEFAULT NULL,
  `user_query_date` date DEFAULT NULL,
  `admin_response_date` date DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4;
INSERT INTO `querytable` VALUES (1,'Sample User','user@example.com','PENDING','PENDING','How do I register?',NULL,'2024-01-05',NULL);
