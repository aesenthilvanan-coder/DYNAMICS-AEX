-- Caly360 Initial Schema (apply with: psql $DATABASE_URL -f migrations/versions/001_initial.sql)

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS jobs (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_type    VARCHAR(20) NOT NULL CHECK (job_type IN ('dynamics')),
    status      VARCHAR(20) NOT NULL DEFAULT 'pending'
                  CHECK (status IN ('pending', 'running', 'complete', 'failed')),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    error_message TEXT,
    celery_task_id VARCHAR(200),
    metadata    JSONB DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_type ON jobs(job_type);
CREATE INDEX IF NOT EXISTS idx_jobs_created ON jobs(created_at DESC);

CREATE TABLE IF NOT EXISTS dynamics_results (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id              UUID REFERENCES jobs(id) ON DELETE CASCADE,
    simulated_time_ns   FLOAT,
    wall_time_seconds   FLOAT,
    use_aex             BOOLEAN DEFAULT FALSE,
    aex_speedup         FLOAT DEFAULT 1.0,
    output_zip_path     TEXT,
    trajectory_xtc_path TEXT,
    energy_edr_path     TEXT,
    performance_ns_per_day FLOAT,
    aex_report          JSONB,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
