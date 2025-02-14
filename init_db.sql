CREATE TABLE IF NOT EXISTS uploads (
  id SERIAL PRIMARY KEY,
  username VARCHAR(50) NOT NULL,
  archive_name VARCHAR(255) NOT NULL,
  file_count INT NOT NULL,
  filesize BIGINT NOT NULL,
  upload_time TIMESTAMP DEFAULT NOW()
);
ALTER SYSTEM SET timezone TO 'Europe/Yekaterinburg';
SELECT pg_reload_conf();