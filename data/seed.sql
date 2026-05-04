-- Seed data for the Checkup API
-- Data product health metrics:
--   - measurements: metric measurements fact table
--   - metrics:      catalog of metrics
--   - products:     data products dimension
--   - entities:     owning entities dimension

CREATE TABLE IF NOT EXISTS entities (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(255) NOT NULL,
    slug        VARCHAR(255) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS products (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(255) NOT NULL,
    slug        VARCHAR(255) NOT NULL UNIQUE,
    entity_id   INTEGER NOT NULL REFERENCES entities(id),
    owner_email VARCHAR(255) NOT NULL,
    created_at  TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS metrics (
    id                   SERIAL PRIMARY KEY,
    name                 VARCHAR(255) NOT NULL UNIQUE,
    category             VARCHAR(64)  NOT NULL,
    description          TEXT,
    higher_is_better     BOOLEAN      NOT NULL,
    threshold_warn       NUMERIC,
    threshold_critical   NUMERIC
);

CREATE TABLE IF NOT EXISTS measurements (
    name             VARCHAR(255) NOT NULL,
    value            VARCHAR(255),
    unit             VARCHAR(255),
    diagnostic       TEXT,
    description      TEXT,
    tag_entity       VARCHAR(255),
    tag_pbac_prefix  VARCHAR(255),
    tag_product      VARCHAR(255) NOT NULL,
    measured_at      TIMESTAMP    NOT NULL,
    PRIMARY KEY (name, tag_product, measured_at)
);

INSERT INTO entities (name, slug) VALUES
    ('Analytics',        'analytics'),
    ('Operations',       'operations'),
    ('Marketing',        'marketing'),
    ('Customer Success', 'customer_success');

INSERT INTO products (name, slug, entity_id, owner_email, created_at) VALUES
    ('Stellar Sales',     'stellar_sales',     (SELECT id FROM entities WHERE slug = 'analytics'),        'stellar.sales@example.com',     '2024-01-15 09:00:00'),
    ('Cosmic Inventory',  'cosmic_inventory',  (SELECT id FROM entities WHERE slug = 'operations'),       'cosmic.inventory@example.com',  '2024-06-01 09:00:00'),
    ('Quantum Marketing', 'quantum_marketing', (SELECT id FROM entities WHERE slug = 'marketing'),        'quantum.marketing@example.com', '2025-01-10 09:00:00'),
    ('Nebula Customers',  'nebula_customers',  (SELECT id FROM entities WHERE slug = 'customer_success'), 'nebula.customers@example.com',  '2025-06-20 09:00:00');

-- status rules:
--   higher_is_better = TRUE:
--     value >= threshold_warn      -> healthy
--     threshold_critical <= value  -> warn
--     value < threshold_critical   -> critical
--   higher_is_better = FALSE:
--     value <= threshold_warn      -> healthy
--     value <= threshold_critical  -> warn
--     value > threshold_critical   -> critical
INSERT INTO metrics (name, category, description, higher_is_better, threshold_warn, threshold_critical) VALUES
    ('dbt_column_test_coverage',       'data_quality',   'Percentage of columns with at least one test',       TRUE,  80,  50),
    ('dbt_models_without_description', 'dbt',            'Number of dbt models missing a description',         FALSE, 10,  30),
    ('dbt_columns_without_description','dbt',            'Number of dbt columns missing a description',        FALSE, 20,  50),
    ('git_days_since_last_update',     'freshness',      'Days since the last git commit',                     FALSE, 7,   30),
    ('cruft_file_exists',              'infrastructure', 'Whether .cruft.json exists in the repository',       TRUE,  1,   1),
    ('minerva_config_exists',          'infrastructure', 'Whether minerva.yml exists in the repository',       TRUE,  1,   1),
    ('airflow_dag_count',              'infrastructure', 'Number of Airflow DAG files for this product',       TRUE,  1,   1),
    ('dbt_supported_version',          'infrastructure', 'Whether dbt version meets minimum requirement',      TRUE,  1,   1),
    ('pbac_proxy_configured',          'infrastructure', 'Whether the dbt profile uses the PBAC proxy',        TRUE,  1,   1);

-- stellar_sales: needs work on test coverage, otherwise healthy
INSERT INTO measurements (name, value, unit, diagnostic, description, tag_entity, tag_pbac_prefix, tag_product, measured_at) VALUES
    ('git_days_since_last_update',      '1',  'days',    'Last commit: 2026-04-22',                    'Days since the last git commit',                  'analytics', 'analytics-stellar-sales', 'stellar_sales', '2026-04-23 12:45:20'),
    ('dbt_models_without_description',  '45', 'models',  '',                                           'Number of models without descriptions',           'analytics', 'analytics-stellar-sales', 'stellar_sales', '2026-04-23 12:45:20'),
    ('dbt_columns_without_description', '4',  'columns', '',                                           'Number of columns without descriptions',          'analytics', 'analytics-stellar-sales', 'stellar_sales', '2026-04-23 12:45:20'),
    ('cruft_file_exists',               '0',  'files',   'No files matching pattern: .cruft.json',     'Whether .cruft.json exists',                      'analytics', 'analytics-stellar-sales', 'stellar_sales', '2026-04-23 12:45:20'),
    ('minerva_config_exists',           '1',  'files',   'Matched files: minerva.yml',                 'Whether minerva.yml exists',                      'analytics', 'analytics-stellar-sales', 'stellar_sales', '2026-04-23 12:45:20'),
    ('airflow_dag_count',               '1',  'files',   'Matched files: dags/stellar_sales.py',       'Number of DAG files',                             'analytics', 'analytics-stellar-sales', 'stellar_sales', '2026-04-23 12:45:20'),
    ('dbt_supported_version',           '1',  'boolean', '',                                           'Whether dbt version meets minimum requirement',   'analytics', 'analytics-stellar-sales', 'stellar_sales', '2026-04-23 12:45:20'),
    ('pbac_proxy_configured',           '1',  'boolean', 'Expected: analytics-stellar-sales.example', 'Whether the dbt profile uses the PBAC proxy',    'analytics', 'analytics-stellar-sales', 'stellar_sales', '2026-04-23 12:45:20'),
    ('dbt_column_test_coverage',        '33', 'percent', '',                                           'Percentage of columns with at least one test',    'analytics', 'analytics-stellar-sales', 'stellar_sales', '2026-04-23 12:45:20');

-- cosmic_inventory: well-maintained
INSERT INTO measurements (name, value, unit, diagnostic, description, tag_entity, tag_pbac_prefix, tag_product, measured_at) VALUES
    ('git_days_since_last_update',      '15', 'days',    'Last commit: 2026-04-08',                                 'Days since the last git commit',                'operations', 'operations-cosmic-inventory', 'cosmic_inventory', '2026-04-23 12:45:20'),
    ('dbt_models_without_description',  '7',  'models',  '',                                                        'Number of models without descriptions',         'operations', 'operations-cosmic-inventory', 'cosmic_inventory', '2026-04-23 12:45:20'),
    ('dbt_columns_without_description', '12', 'columns', '',                                                        'Number of columns without descriptions',        'operations', 'operations-cosmic-inventory', 'cosmic_inventory', '2026-04-23 12:45:20'),
    ('dbt_column_test_coverage',        '78', 'percent', '',                                                        'Percentage of columns with at least one test',  'operations', 'operations-cosmic-inventory', 'cosmic_inventory', '2026-04-23 12:45:20'),
    ('dbt_supported_version',           '1',  'boolean', '',                                                        'Whether dbt version meets minimum requirement', 'operations', 'operations-cosmic-inventory', 'cosmic_inventory', '2026-04-23 12:45:20'),
    ('airflow_dag_count',               '2',  'files',   'Matched files: dags/cosmic_main.py, dags/cosmic_export.py','Number of DAG files',                          'operations', 'operations-cosmic-inventory', 'cosmic_inventory', '2026-04-23 12:45:20'),
    ('cruft_file_exists',               '1',  'files',   'Matched files: .cruft.json',                              'Whether .cruft.json exists',                    'operations', 'operations-cosmic-inventory', 'cosmic_inventory', '2026-04-23 12:45:20'),
    ('minerva_config_exists',           '1',  'files',   'Matched files: minerva.yml',                              'Whether minerva.yml exists',                    'operations', 'operations-cosmic-inventory', 'cosmic_inventory', '2026-04-23 12:45:20'),
    ('pbac_proxy_configured',           '1',  'boolean', 'Expected: operations-cosmic-inventory.example',           'Whether the dbt profile uses the PBAC proxy',   'operations', 'operations-cosmic-inventory', 'cosmic_inventory', '2026-04-23 12:45:20');

-- quantum_marketing: stale, struggling
INSERT INTO measurements (name, value, unit, diagnostic, description, tag_entity, tag_pbac_prefix, tag_product, measured_at) VALUES
    ('git_days_since_last_update',      '45', 'days',    'Last commit: 2026-03-09',                            'Days since the last git commit',                'marketing', 'marketing-quantum-marketing', 'quantum_marketing', '2026-04-23 12:45:20'),
    ('dbt_models_without_description',  '23', 'models',  '',                                                   'Number of models without descriptions',         'marketing', 'marketing-quantum-marketing', 'quantum_marketing', '2026-04-23 12:45:20'),
    ('dbt_columns_without_description', '89', 'columns', '',                                                   'Number of columns without descriptions',        'marketing', 'marketing-quantum-marketing', 'quantum_marketing', '2026-04-23 12:45:20'),
    ('dbt_column_test_coverage',        '12', 'percent', '',                                                   'Percentage of columns with at least one test',  'marketing', 'marketing-quantum-marketing', 'quantum_marketing', '2026-04-23 12:45:20'),
    ('dbt_supported_version',           '0',  'boolean', 'Found: 1.5.0, Required: >=1.7.0',                    'Whether dbt version meets minimum requirement', 'marketing', 'marketing-quantum-marketing', 'quantum_marketing', '2026-04-23 12:45:20'),
    ('airflow_dag_count',               '1',  'files',   'Matched files: dags/quantum_marketing.py',           'Number of DAG files',                           'marketing', 'marketing-quantum-marketing', 'quantum_marketing', '2026-04-23 12:45:20'),
    ('minerva_config_exists',           '0',  'files',   'No files matching pattern: minerva.yml',             'Whether minerva.yml exists',                    'marketing', 'marketing-quantum-marketing', 'quantum_marketing', '2026-04-23 12:45:20'),
    ('cruft_file_exists',               '0',  'files',   'No files matching pattern: .cruft.json',             'Whether .cruft.json exists',                    'marketing', 'marketing-quantum-marketing', 'quantum_marketing', '2026-04-23 12:45:20'),
    ('pbac_proxy_configured',           '0',  'boolean', 'Expected: marketing-quantum-marketing.example',      'Whether the dbt profile uses the PBAC proxy',   'marketing', 'marketing-quantum-marketing', 'quantum_marketing', '2026-04-23 12:45:20');

-- nebula_customers: gold-standard
INSERT INTO measurements (name, value, unit, diagnostic, description, tag_entity, tag_pbac_prefix, tag_product, measured_at) VALUES
    ('git_days_since_last_update',      '0',  'days',    'Last commit: 2026-04-23',                                                  'Days since the last git commit',                'customer_success', 'customer-success-nebula-customers', 'nebula_customers', '2026-04-23 12:45:20'),
    ('dbt_models_without_description',  '0',  'models',  '',                                                                         'Number of models without descriptions',         'customer_success', 'customer-success-nebula-customers', 'nebula_customers', '2026-04-23 12:45:20'),
    ('dbt_columns_without_description', '0',  'columns', '',                                                                         'Number of columns without descriptions',        'customer_success', 'customer-success-nebula-customers', 'nebula_customers', '2026-04-23 12:45:20'),
    ('dbt_column_test_coverage',        '95', 'percent', '',                                                                         'Percentage of columns with at least one test',  'customer_success', 'customer-success-nebula-customers', 'nebula_customers', '2026-04-23 12:45:20'),
    ('dbt_supported_version',           '1',  'boolean', '',                                                                         'Whether dbt version meets minimum requirement', 'customer_success', 'customer-success-nebula-customers', 'nebula_customers', '2026-04-23 12:45:20'),
    ('airflow_dag_count',               '3',  'files',   'Matched files: dags/nebula_main.py, dags/nebula_export.py, dags/nebula_alerts.py', 'Number of DAG files',                  'customer_success', 'customer-success-nebula-customers', 'nebula_customers', '2026-04-23 12:45:20'),
    ('minerva_config_exists',           '1',  'files',   'Matched files: minerva.yml',                                               'Whether minerva.yml exists',                    'customer_success', 'customer-success-nebula-customers', 'nebula_customers', '2026-04-23 12:45:20'),
    ('cruft_file_exists',               '1',  'files',   'Matched files: .cruft.json',                                               'Whether .cruft.json exists',                    'customer_success', 'customer-success-nebula-customers', 'nebula_customers', '2026-04-23 12:45:20'),
    ('pbac_proxy_configured',           '1',  'boolean', 'Expected: customer-success-nebula-customers.example',                     'Whether the dbt profile uses the PBAC proxy',   'customer_success', 'customer-success-nebula-customers', 'nebula_customers', '2026-04-23 12:45:20');

-- historical measurements (for trend analysis)
INSERT INTO measurements (name, value, unit, diagnostic, description, tag_entity, tag_pbac_prefix, tag_product, measured_at) VALUES
    ('dbt_column_test_coverage',       '28', 'percent', '', 'Percentage of columns with at least one test', 'analytics', 'analytics-stellar-sales', 'stellar_sales',     '2026-04-16 12:45:20'),
    ('dbt_column_test_coverage',       '25', 'percent', '', 'Percentage of columns with at least one test', 'analytics', 'analytics-stellar-sales', 'stellar_sales',     '2026-04-09 12:45:20'),
    ('dbt_column_test_coverage',       '20', 'percent', '', 'Percentage of columns with at least one test', 'analytics', 'analytics-stellar-sales', 'stellar_sales',     '2026-04-02 12:45:20'),
    ('dbt_models_without_description', '52', 'models',  '', 'Number of models without descriptions',        'analytics', 'analytics-stellar-sales', 'stellar_sales',     '2026-04-16 12:45:20'),
    ('dbt_models_without_description', '55', 'models',  '', 'Number of models without descriptions',        'analytics', 'analytics-stellar-sales', 'stellar_sales',     '2026-04-09 12:45:20'),
    ('dbt_column_test_coverage',       '74', 'percent', '', 'Percentage of columns with at least one test', 'operations', 'operations-cosmic-inventory', 'cosmic_inventory', '2026-04-16 12:45:20'),
    ('dbt_column_test_coverage',       '70', 'percent', '', 'Percentage of columns with at least one test', 'operations', 'operations-cosmic-inventory', 'cosmic_inventory', '2026-04-09 12:45:20'),
    ('dbt_column_test_coverage',       '15', 'percent', '', 'Percentage of columns with at least one test', 'marketing', 'marketing-quantum-marketing', 'quantum_marketing', '2026-04-16 12:45:20'),
    ('dbt_column_test_coverage',       '18', 'percent', '', 'Percentage of columns with at least one test', 'marketing', 'marketing-quantum-marketing', 'quantum_marketing', '2026-04-09 12:45:20');
