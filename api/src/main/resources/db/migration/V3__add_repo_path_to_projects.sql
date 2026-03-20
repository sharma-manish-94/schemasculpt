-- Add repository_path to projects table to link source code repositories
ALTER TABLE projects ADD COLUMN repository_path VARCHAR(1024);
