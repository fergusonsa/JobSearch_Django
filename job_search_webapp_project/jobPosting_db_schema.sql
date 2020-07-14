--
-- File generated with SQLiteStudio v3.0.3 on Mon Jan 30 10:09:39 2017
--
-- Text encoding used: windows-1252
--
PRAGMA foreign_keys = off;
BEGIN TRANSACTION;

-- Table: auth_group
CREATE TABLE "auth_group" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "name" varchar(80) NOT NULL UNIQUE);

-- Table: django_admin_log
CREATE TABLE "django_admin_log" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "object_id" text NULL, "object_repr" varchar(200) NOT NULL, "action_flag" smallint unsigned NOT NULL, "change_message" text NOT NULL, "content_type_id" integer NULL REFERENCES "django_content_type" ("id"), "user_id" integer NOT NULL REFERENCES "auth_user" ("id"), "action_time" datetime NOT NULL);

-- Table: django_session
CREATE TABLE "django_session" ("session_key" varchar(40) NOT NULL PRIMARY KEY, "session_data" text NOT NULL, "expire_date" datetime NOT NULL);

-- Table: django_content_type
CREATE TABLE "django_content_type" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "app_label" varchar(100) NOT NULL, "model" varchar(100) NOT NULL);

-- Table: auth_user_user_permissions
CREATE TABLE "auth_user_user_permissions" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "user_id" integer NOT NULL REFERENCES "auth_user" ("id"), "permission_id" integer NOT NULL REFERENCES "auth_permission" ("id"));

-- Table: django_migrations
CREATE TABLE "django_migrations" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "app" varchar(255) NOT NULL, "name" varchar(255) NOT NULL, "applied" datetime NOT NULL);

-- Table: auth_permission
CREATE TABLE "auth_permission" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "content_type_id" integer NOT NULL REFERENCES "django_content_type" ("id"), "codename" varchar(100) NOT NULL, "name" varchar(255) NOT NULL);

-- Table: auth_user_groups
CREATE TABLE "auth_user_groups" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "user_id" integer NOT NULL REFERENCES "auth_user" ("id"), "group_id" integer NOT NULL REFERENCES "auth_group" ("id"));

-- Table: auth_user
CREATE TABLE "auth_user" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "password" varchar(128) NOT NULL, "last_login" datetime NULL, "is_superuser" bool NOT NULL, "first_name" varchar(30) NOT NULL, "last_name" varchar(30) NOT NULL, "email" varchar(254) NOT NULL, "is_staff" bool NOT NULL, "is_active" bool NOT NULL, "date_joined" datetime NOT NULL, "username" varchar(150) NOT NULL UNIQUE);

-- Table: auth_group_permissions
CREATE TABLE "auth_group_permissions" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "group_id" integer NOT NULL REFERENCES "auth_group" ("id"), "permission_id" integer NOT NULL REFERENCES "auth_permission" ("id"));

-- Index: auth_user_user_permissions_user_id_14a6b632_uniq
CREATE UNIQUE INDEX "auth_user_user_permissions_user_id_14a6b632_uniq" ON "auth_user_user_permissions" ("user_id", "permission_id");

-- Index: auth_user_user_permissions_8373b171
CREATE INDEX "auth_user_user_permissions_8373b171" ON "auth_user_user_permissions" ("permission_id");

-- Index: auth_group_permissions_0e939a4f
CREATE INDEX "auth_group_permissions_0e939a4f" ON "auth_group_permissions" ("group_id");

-- Index: django_content_type_app_label_76bd3d3b_uniq
CREATE UNIQUE INDEX "django_content_type_app_label_76bd3d3b_uniq" ON "django_content_type" ("app_label", "model");

-- Index: auth_user_user_permissions_e8701ad4
CREATE INDEX "auth_user_user_permissions_e8701ad4" ON "auth_user_user_permissions" ("user_id");

-- Index: auth_group_permissions_group_id_0cd325b0_uniq
CREATE UNIQUE INDEX "auth_group_permissions_group_id_0cd325b0_uniq" ON "auth_group_permissions" ("group_id", "permission_id");

-- Index: django_admin_log_417f1b1c
CREATE INDEX "django_admin_log_417f1b1c" ON "django_admin_log" ("content_type_id");

-- Index: django_session_de54fa62
CREATE INDEX "django_session_de54fa62" ON "django_session" ("expire_date");

-- Index: auth_permission_417f1b1c
CREATE INDEX "auth_permission_417f1b1c" ON "auth_permission" ("content_type_id");

-- Index: auth_user_groups_user_id_94350c0c_uniq
CREATE UNIQUE INDEX "auth_user_groups_user_id_94350c0c_uniq" ON "auth_user_groups" ("user_id", "group_id");

-- Index: auth_group_permissions_8373b171
CREATE INDEX "auth_group_permissions_8373b171" ON "auth_group_permissions" ("permission_id");

-- Index: auth_permission_content_type_id_01ab375a_uniq
CREATE UNIQUE INDEX "auth_permission_content_type_id_01ab375a_uniq" ON "auth_permission" ("content_type_id", "codename");

-- Index: django_admin_log_e8701ad4
CREATE INDEX "django_admin_log_e8701ad4" ON "django_admin_log" ("user_id");

-- Index: auth_user_groups_0e939a4f
CREATE INDEX "auth_user_groups_0e939a4f" ON "auth_user_groups" ("group_id");

-- Index: auth_user_groups_e8701ad4
CREATE INDEX "auth_user_groups_e8701ad4" ON "auth_user_groups" ("user_id");

-- Table: JobPostings
CREATE TABLE JobPostings (Id TEXT NOT NULL UNIQUE, Company TEXT, Title TEXT NOT NULL, Locale TEXT, URL TEXT NOT NULL, postedDate DATETIME, insertedDate DATETIME DEFAULT ((datetime('now', 'localtime'))), City TEXT, Province TEXT, SearchTerms TEXT, ElementHtml TEXT);

-- Table: RecruitingCompanies
CREATE TABLE RecruitingCompanies (Name TEXT PRIMARY KEY UNIQUE, DateContacted DATETIME, Comment TEXT, ResumeSubmitted BOOLEAN DEFAULT (0), NotInterested BOOLEAN DEFAULT (0), URL TEXT, CannotSubmitResume BOOLEAN DEFAULT (0), DateInserted DATETIME, Telephone TEXT DEFAULT (''), ContactPerson TEXT DEFAULT (''), NearestOffice TEXT DEFAULT (''));

-- Table: CompanyAliases
CREATE TABLE CompanyAliases (CompanyName CHAR REFERENCES RecruitingCompanies (Name) NOT NULL, Alias CHAR PRIMARY KEY UNIQUE NOT NULL);

-- View: CompNotContactedByProvWMoreThan2Postings
CREATE VIEW CompNotContactedByProvWMoreThan2Postings AS SELECT * FROM (SELECT Company, Province, count(id) AS num FROM JobPostings LEFT JOIN RecruitingCompanies ON Company = Name WHERE Name IS NULL OR ((NOT ResumeSubmitted) AND NOT (NotInterested OR CannotSubmitResume)) GROUP BY Province, Company ORDER BY Province, num DESC, Company) WHERE num > 2;

-- View: GroupByLocale
CREATE VIEW GroupByLocale AS SELECT locale, count(id) AS num FROM JobPostings GROUP BY locale ORDER BY num DESC;

-- View: GroupByCompany
CREATE VIEW GroupByCompany AS SELECT company, count(id) AS num FROM JobPostings GROUP BY company ORDER BY num DESC;

-- View: GroupByProvinceCompany
CREATE VIEW GroupByProvinceCompany AS SELECT Province, company, count(id) AS num FROM JobPostings GROUP BY Province, company ORDER BY Province, company;

-- View: GroupByCompanyLocale
CREATE VIEW GroupByCompanyLocale AS SELECT company, city || ', ' || province AS location, count(id) AS num FROM JobPostings GROUP BY company, location ORDER BY company, location DESC;

COMMIT TRANSACTION;
