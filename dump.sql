-- First, drop all tables in reverse dependency order
BEGIN;

DROP TABLE IF EXISTS webinar_webinarattendees CASCADE;
DROP TABLE IF EXISTS exam_portal_evalqr CASCADE;
DROP TABLE IF EXISTS exam_portal_testqr CASCADE;
DROP TABLE IF EXISTS webinar_comment CASCADE;
DROP TABLE IF EXISTS webinar_speaker CASCADE;
DROP TABLE IF EXISTS login_userprofile CASCADE;
DROP TABLE IF EXISTS webinar_webinar CASCADE;
DROP TABLE IF EXISTS exam_portal_certificatetemplate CASCADE;
DROP TABLE IF EXISTS exam_portal_testresult CASCADE;
DROP TABLE IF EXISTS webinar_testresponse CASCADE;
DROP TABLE IF EXISTS webinar_choice CASCADE;
DROP TABLE IF EXISTS webinar_test_question CASCADE;
DROP TABLE IF EXISTS webinar_responsequestionaire CASCADE;
DROP TABLE IF EXISTS django_session CASCADE;
DROP TABLE IF EXISTS auth_user_user_permissions CASCADE;
DROP TABLE IF EXISTS auth_user_groups CASCADE;
DROP TABLE IF EXISTS auth_group_permissions CASCADE;
DROP TABLE IF EXISTS auth_permission CASCADE;
DROP TABLE IF EXISTS auth_group CASCADE;
DROP TABLE IF EXISTS auth_user CASCADE;
DROP TABLE IF EXISTS django_admin_log CASCADE;
DROP TABLE IF EXISTS django_content_type CASCADE;
DROP TABLE IF EXISTS django_migrations CASCADE;

COMMIT;

-- Now create tables in proper dependency order
BEGIN;

-- 1. Basic tables without foreign keys
CREATE TABLE django_content_type (
    id SERIAL PRIMARY KEY,
    app_label VARCHAR(100) NOT NULL,
    model VARCHAR(100) NOT NULL
);

CREATE TABLE auth_group (
    id SERIAL PRIMARY KEY,
    name VARCHAR(150) NOT NULL UNIQUE
);

CREATE TABLE auth_user (
    id SERIAL PRIMARY KEY,
    password VARCHAR(128) NOT NULL,
    last_login TIMESTAMP,
    is_superuser BOOLEAN NOT NULL,
    username VARCHAR(150) NOT NULL UNIQUE,
    last_name VARCHAR(150) NOT NULL,
    email VARCHAR(254) NOT NULL,
    is_staff BOOLEAN NOT NULL,
    is_active BOOLEAN NOT NULL,
    date_joined TIMESTAMP NOT NULL,
    first_name VARCHAR(150) NOT NULL
);

CREATE TABLE django_migrations (
    id SERIAL PRIMARY KEY,
    app VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    applied TIMESTAMP NOT NULL
);

-- 2. Tables with basic foreign keys
CREATE TABLE auth_permission (
    id SERIAL PRIMARY KEY,
    content_type_id INTEGER NOT NULL REFERENCES django_content_type(id) DEFERRABLE INITIALLY DEFERRED,
    codename VARCHAR(100) NOT NULL,
    name VARCHAR(255) NOT NULL
);

CREATE TABLE django_admin_log (
    id SERIAL PRIMARY KEY,
    object_id TEXT,
    object_repr VARCHAR(200) NOT NULL,
    action_flag SMALLINT NOT NULL CHECK (action_flag >= 0),
    change_message TEXT NOT NULL,
    content_type_id INTEGER REFERENCES django_content_type(id) DEFERRABLE INITIALLY DEFERRED,
    user_id INTEGER NOT NULL REFERENCES auth_user(id) DEFERRABLE INITIALLY DEFERRED,
    action_time TIMESTAMP NOT NULL
);

CREATE TABLE django_session (
    session_key VARCHAR(40) PRIMARY KEY,
    session_data TEXT NOT NULL,
    expire_date TIMESTAMP NOT NULL
);

-- 3. Junction tables
CREATE TABLE auth_group_permissions (
    id SERIAL PRIMARY KEY,
    group_id INTEGER NOT NULL REFERENCES auth_group(id) DEFERRABLE INITIALLY DEFERRED,
    permission_id INTEGER NOT NULL REFERENCES auth_permission(id) DEFERRABLE INITIALLY DEFERRED
);

CREATE TABLE auth_user_groups (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES auth_user(id) DEFERRABLE INITIALLY DEFERRED,
    group_id INTEGER NOT NULL REFERENCES auth_group(id) DEFERRABLE INITIALLY DEFERRED
);

CREATE TABLE auth_user_user_permissions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES auth_user(id) DEFERRABLE INITIALLY DEFERRED,
    permission_id INTEGER NOT NULL REFERENCES auth_permission(id) DEFERRABLE INITIALLY DEFERRED
);

-- 4. Application-specific tables
CREATE TABLE webinar_webinar (
    id SERIAL PRIMARY KEY,
    title VARCHAR(20) NOT NULL,
    description VARCHAR(1000) NOT NULL,
    number_of_speaker INTEGER NOT NULL,
    event_type VARCHAR(20),
    start_date DATE,
    until_date DATE,
    banner VARCHAR(100) NOT NULL,
    venue VARCHAR(40) NOT NULL,
    time TIME NOT NULL
);

CREATE TABLE login_userprofile (
    id SERIAL PRIMARY KEY,
    school_id VARCHAR(100),
    number VARCHAR(100),
    user_id INTEGER NOT NULL UNIQUE REFERENCES auth_user(id) DEFERRABLE INITIALLY DEFERRED,
    school VARCHAR(100),
    img VARCHAR(100)
);

-- [Continue creating all other tables in proper order...]

-- After all tables are created, insert data in proper order
-- First insert into tables without foreign key dependencies
INSERT INTO django_content_type (id, app_label, model) VALUES 
(1,'login','number'),
(2,'webinar','webinar'),
-- [All other content types...]
(20,'exam_portal','evalqr');

INSERT INTO auth_user (id, password, last_login, is_superuser, username, last_name, email, is_staff, is_active, date_joined, first_name) VALUES
(1,'pbkdf2_sha256$1000000$l3qa3NmfE429hIbG6IUN8C$IZFUinYlnX7/KF2Rhz4O/Ltqjy9Rz4Z59HCLg9tzXH0=','2025-07-17 10:30:47.757772',true,'pc','mark','johnphilipbaylon3@gmail.com',true,true,'2025-03-26 04:15:54','john'),
-- [All other users...]
(8,'pbkdf2_sha256$1000000$2GwDUZlVnu3PojdBa3LdCD$L/7Q9zYUWuYc0UlkF8Z7010fXcte8+N/NwQ+lKHPmWA=','2025-07-16 05:55:26.381707',false,'juan','dela cruz','juan@gmail.com',true,true,'2025-07-16 05:54:22.581930','juan');

-- [Continue inserting data in proper order...]

COMMIT;

-- Finally create indexes
CREATE UNIQUE INDEX auth_group_permissions_group_id_permission_id_uniq ON auth_group_permissions (group_id, permission_id);
CREATE INDEX auth_group_permissions_group_id ON auth_group_permissions (group_id);
-- [All other indexes...]