-- schema.sql
--
-- This script defines the complete database schema for the Dual-Signal 'Smart Money' Tracker project.
-- It creates the necessary tables, columns, constraints, and indexes to store data on
-- curated funds, their quarterly holdings (from 13F filings), and insider transactions (from Form 4 filings).
-- The schema is designed for PostgreSQL and leverages its advanced features like JSONB and MVCC.

-- Drop existing tables in reverse order of dependency to avoid foreign key conflicts
-- This allows the script to be re-run on an existing database for a clean setup.
DROP TABLE IF EXISTS "Insider_Transactions";
DROP TABLE IF EXISTS "Quarterly_Holdings";
DROP TABLE IF EXISTS "Funds";

-- ================================================================================= --
-- TABLE: Funds
-- ================================================================================= --
-- Stores the curated list of "smart money" institutional investment managers.
-- This table serves as the primary source of truth for which funds to track.
CREATE TABLE "Funds" (
    "cik" VARCHAR(10) PRIMARY KEY, -- Central Index Key, the unique identifier assigned by the SEC.
    "fund_name" VARCHAR(255) NOT NULL UNIQUE, -- The full legal name of the investment fund.
    "strategy" VARCHAR(255) -- A brief description of the fund's primary investment strategy archetype.
);

-- Add comments to the table and columns for clarity.
COMMENT ON TABLE "Funds" IS 'Stores the curated list of institutional investment managers ("whales") to be tracked.';
COMMENT ON COLUMN "Funds"."cik" IS 'SEC Central Index Key. Primary key.';
COMMENT ON COLUMN "Funds"."fund_name" IS 'The legal name of the fund or investment manager.';
COMMENT ON COLUMN "Funds"."strategy" IS 'Primary investment strategy archetype(s), e.g., Activist, Deep Fundamental.';


-- ================================================================================= --
-- TABLE: Quarterly_Holdings
-- ================================================================================= --
-- Stores the holdings data extracted from the quarterly 13F filings of the tracked funds.
-- Each row represents a specific asset held by a fund at the end of a quarter.
CREATE TABLE "Quarterly_Holdings" (
    "id" BIGSERIAL PRIMARY KEY, -- Unique identifier for each holding record.
    "fund_cik" VARCHAR(10) NOT NULL REFERENCES "Funds"("cik") ON DELETE CASCADE, -- Foreign key linking to the fund.
    "report_date" DATE NOT NULL, -- The "as of" date for the holding report (end of the quarter).
    "filing_date" TIMESTAMP WITH TIME ZONE NOT NULL, -- The date the 13F form was filed with the SEC.
    "cusip" VARCHAR(9) NOT NULL, -- CUSIP identifier for the security held.
    "company_name" VARCHAR(255) NOT NULL, -- The name of the company whose stock is held.
    "shares" BIGINT NOT NULL CHECK ("shares" >= 0), -- The number of shares held.
    "value_usd" BIGINT NOT NULL CHECK ("value_usd" >= 0), -- The total market value of the shares held, in USD.
    "raw_json" JSONB NOT NULL, -- The complete, original JSON response from the API for this holding.

    -- A fund cannot report the same security twice for the same reporting period.
    CONSTRAINT uq_holding UNIQUE ("fund_cik", "report_date", "cusip")
);

-- Add comments to the table and columns.
COMMENT ON TABLE "Quarterly_Holdings" IS 'Stores asset holdings data from quarterly 13F filings for the tracked funds.';
COMMENT ON COLUMN "Quarterly_Holdings"."id" IS 'Unique identifier for the holding record.';
COMMENT ON COLUMN "Quarterly_Holdings"."fund_cik" IS 'Foreign key referencing the CIK of the fund in the Funds table.';
COMMENT ON COLUMN "Quarterly_Holdings"."report_date" IS 'The end-of-quarter date for which the holdings are reported.';
COMMENT ON COLUMN "Quarterly_Holdings"."filing_date" IS 'The timestamp when the 13F form was filed.';
COMMENT ON COLUMN "Quarterly_Holdings"."cusip" IS 'The CUSIP identifier of the reported security.';
COMMENT ON COLUMN "Quarterly_Holdings"."shares" IS 'The number of shares held.';
COMMENT ON COLUMN "Quarterly_Holdings"."value_usd" IS 'The total market value of the position in US dollars.';
COMMENT ON COLUMN "Quarterly_Holdings"."raw_json" IS 'Stores the original, complete JSON API response for archival and reprocessing.';

-- Create indexes to optimize query performance for common lookup patterns.
CREATE INDEX idx_quarterly_holdings_fund_cik ON "Quarterly_Holdings" ("fund_cik");
CREATE INDEX idx_quarterly_holdings_report_date ON "Quarterly_Holdings" ("report_date");
CREATE INDEX idx_quarterly_holdings_cusip ON "Quarterly_Holdings" ("cusip");


-- ================================================================================= --
-- TABLE: Insider_Transactions
-- ================================================================================= --
-- Stores data on insider transactions from SEC Form 4 filings.
-- This table captures the "trigger" events for the dual-signal strategy.
CREATE TABLE "Insider_Transactions" (
    "id" BIGSERIAL PRIMARY KEY, -- Unique identifier for each transaction record.
    "accession_no" VARCHAR(255) NOT NULL UNIQUE, -- The unique accession number of the SEC filing. A reliable unique key.
    "issuer_cik" VARCHAR(10) NOT NULL, -- The CIK of the company whose shares were transacted.
    "issuer_ticker" VARCHAR(10), -- The stock ticker of the issuer.
    "insider_cik" VARCHAR(10), -- The CIK of the insider (reporting person).
    "insider_name" VARCHAR(255) NOT NULL, -- The name of the insider.
    "insider_relation" VARCHAR(255), -- The insider's relationship to the company (e.g., CEO, CFO, Director).
    "filing_date" TIMESTAMP WITH TIME ZONE NOT NULL, -- The timestamp when the Form 4 was filed.
    "transaction_date" DATE NOT NULL, -- The date the actual transaction occurred.
    "transaction_code" CHAR(1), -- The code for the transaction type (e.g., 'P' for purchase, 'S' for sale).
    "shares" BIGINT NOT NULL, -- The number of shares transacted. Can be negative for dispositions.
    "price_per_share" NUMERIC(18, 4), -- The price per share of the transaction.
    "shares_owned_after" BIGINT CHECK ("shares_owned_after" >= 0), -- Total shares owned by the insider after the transaction.
    "raw_json" JSONB NOT NULL -- The complete, original JSON response from the API for this filing.
);

-- Add comments to the table and columns.
COMMENT ON TABLE "Insider_Transactions" IS 'Stores insider transaction data from SEC Form 4 filings.';
COMMENT ON COLUMN "Insider_Transactions"."accession_no" IS 'The unique accession number of the filing, acting as a natural key.';
COMMENT ON COLUMN "Insider_Transactions"."issuer_cik" IS 'The CIK of the company (the issuer).';
COMMENT ON COLUMN "Insider_Transactions"."issuer_ticker" IS 'The stock ticker of the company.';
COMMENT ON COLUMN "Insider_Transactions"."insider_name" IS 'The name of the corporate insider who made the transaction.';
COMMENT ON COLUMN "Insider_Transactions"."insider_relation" IS 'Relationship of the insider to the issuer (e.g., CEO, CFO).';
COMMENT ON COLUMN "Insider_Transactions"."filing_date" IS 'The timestamp when the Form 4 was filed.';
COMMENT ON COLUMN "Insider_Transactions"."transaction_date" IS 'The date on which the transaction occurred.';
COMMENT ON COLUMN "Insider_Transactions"."transaction_code" IS 'SEC code for the transaction type (P=Purchase, S=Sale).';
COMMENT ON COLUMN "Insider_Transactions"."shares_owned_after" IS 'Number of shares beneficially owned after the transaction.';
COMMENT ON COLUMN "Insider_Transactions"."raw_json" IS 'Stores the original, complete JSON API response for archival and reprocessing.';

-- Create indexes to optimize queries for finding triggers, which are often based on the
-- issuer, transaction date, and transaction code.
CREATE INDEX idx_insider_transactions_issuer_cik ON "Insider_Transactions" ("issuer_cik");
CREATE INDEX idx_insider_transactions_issuer_ticker ON "Insider_Transactions" ("issuer_ticker");
CREATE INDEX idx_insider_transactions_transaction_date ON "Insider_Transactions" ("transaction_date");
CREATE INDEX idx_insider_transactions_transaction_code ON "Insider_Transactions" ("transaction_code");
