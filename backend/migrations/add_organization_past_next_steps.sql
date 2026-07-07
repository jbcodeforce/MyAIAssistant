-- Add past_steps / next_steps JSON columns to organizations (same shape as projects steps).
ALTER TABLE organizations ADD COLUMN past_steps JSON;
ALTER TABLE organizations ADD COLUMN next_steps JSON;
