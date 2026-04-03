CREATE DATABASE IF NOT EXISTS alfit_auth;
CREATE DATABASE IF NOT EXISTS alfit_gym;
CREATE DATABASE IF NOT EXISTS alfit_member;
CREATE DATABASE IF NOT EXISTS alfit_notification;
CREATE DATABASE IF NOT EXISTS alfit_ai;
CREATE DATABASE IF NOT EXISTS alfit_evolution;
CREATE DATABASE IF NOT EXISTS alfit_billing;
CREATE DATABASE IF NOT EXISTS alfit_analytics;
CREATE DATABASE IF NOT EXISTS alfit_admin;
CREATE DATABASE IF NOT EXISTS alfit_storage;
CREATE DATABASE IF NOT EXISTS alfit_email;
CREATE DATABASE IF NOT EXISTS alfit_message;

GRANT ALL PRIVILEGES ON alfit_auth.* TO 'alfit'@'%';
GRANT ALL PRIVILEGES ON alfit_gym.* TO 'alfit'@'%';
GRANT ALL PRIVILEGES ON alfit_member.* TO 'alfit'@'%';
GRANT ALL PRIVILEGES ON alfit_notification.* TO 'alfit'@'%';
GRANT ALL PRIVILEGES ON alfit_ai.* TO 'alfit'@'%';
GRANT ALL PRIVILEGES ON alfit_evolution.* TO 'alfit'@'%';
GRANT ALL PRIVILEGES ON alfit_billing.* TO 'alfit'@'%';
GRANT ALL PRIVILEGES ON alfit_analytics.* TO 'alfit'@'%';
GRANT ALL PRIVILEGES ON alfit_admin.* TO 'alfit'@'%';
GRANT ALL PRIVILEGES ON alfit_storage.* TO 'alfit'@'%';
GRANT ALL PRIVILEGES ON alfit_email.* TO 'alfit'@'%';
GRANT ALL PRIVILEGES ON alfit_message.* TO 'alfit'@'%';

FLUSH PRIVILEGES;
