-- Migration: Add Centralized Reward Pool System
-- Date: 2024-11-17
-- Description: Create college reward pool to prevent unlimited reward creation and admin abuse

-- =====================================================
-- 1. CREATE COLLEGE REWARD POOL TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS college_reward_pools (
    id SERIAL PRIMARY KEY,
    college_id INTEGER UNIQUE NOT NULL REFERENCES colleges(id) ON DELETE CASCADE,
    total_balance INTEGER DEFAULT 0 NOT NULL CHECK (total_balance >= 0),
    reserved_balance INTEGER DEFAULT 0 NOT NULL CHECK (reserved_balance >= 0),
    available_balance INTEGER GENERATED ALWAYS AS (total_balance - reserved_balance) STORED,
    initial_allocation INTEGER DEFAULT 0 NOT NULL,  -- Track initial allocation
    lifetime_credits INTEGER DEFAULT 0 NOT NULL,     -- Total credits ever added
    lifetime_debits INTEGER DEFAULT 0 NOT NULL,      -- Total debits ever deducted
    low_balance_threshold INTEGER DEFAULT 1000 NOT NULL,  -- Alert threshold
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for fast college lookup
CREATE INDEX IF NOT EXISTS idx_reward_pools_college_id ON college_reward_pools(college_id);

-- =====================================================
-- 2. CREATE POOL TRANSACTION LOG TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS pool_transactions (
    id SERIAL PRIMARY KEY,
    college_id INTEGER NOT NULL REFERENCES colleges(id) ON DELETE CASCADE,
    transaction_type VARCHAR(50) NOT NULL,  -- 'CREDIT', 'DEBIT'
    amount INTEGER NOT NULL CHECK (amount > 0),
    balance_before INTEGER NOT NULL,
    balance_after INTEGER NOT NULL,
    reason VARCHAR(100) NOT NULL,  -- 'welcome_bonus', 'post_reward', 'admin_gift', 'manual_topup', 'admin_reward'
    description TEXT,
    reference_type VARCHAR(50),  -- 'user', 'post', 'reward', 'manual'
    reference_id INTEGER,
    beneficiary_user_id INTEGER REFERENCES users(id),  -- Who received the points (for DEBIT)
    created_by INTEGER REFERENCES users(id),  -- Who initiated the transaction
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB  -- Additional data like approval info, etc.
);

-- Indexes for fast queries
CREATE INDEX IF NOT EXISTS idx_pool_transactions_college_id ON pool_transactions(college_id);
CREATE INDEX IF NOT EXISTS idx_pool_transactions_created_at ON pool_transactions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_pool_transactions_type ON pool_transactions(transaction_type);
CREATE INDEX IF NOT EXISTS idx_pool_transactions_reason ON pool_transactions(reason);
CREATE INDEX IF NOT EXISTS idx_pool_transactions_beneficiary ON pool_transactions(beneficiary_user_id);

-- =====================================================
-- 3. INITIALIZE POOLS FOR EXISTING COLLEGES
-- =====================================================
-- Give each existing college an initial allocation of 10,000 points
INSERT INTO college_reward_pools (college_id, total_balance, reserved_balance, initial_allocation, lifetime_credits, lifetime_debits)
SELECT 
    id as college_id,
    10000 as total_balance,
    0 as reserved_balance,
    10000 as initial_allocation,
    10000 as lifetime_credits,
    0 as lifetime_debits
FROM colleges
ON CONFLICT (college_id) DO NOTHING;

-- Log the initial allocation
INSERT INTO pool_transactions (
    college_id,
    transaction_type,
    amount,
    balance_before,
    balance_after,
    reason,
    description,
    reference_type
)
SELECT 
    id as college_id,
    'CREDIT' as transaction_type,
    10000 as amount,
    0 as balance_before,
    10000 as balance_after,
    'manual_topup' as reason,
    'Initial college reward pool allocation' as description,
    'system' as reference_type
FROM colleges
WHERE NOT EXISTS (
    SELECT 1 FROM pool_transactions 
    WHERE college_id = colleges.id 
    AND reason = 'manual_topup'
);

-- =====================================================
-- 4. CREATE TRIGGER TO UPDATE LIFETIME STATS
-- =====================================================
CREATE OR REPLACE FUNCTION update_pool_lifetime_stats()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.transaction_type = 'CREDIT' THEN
        UPDATE college_reward_pools 
        SET lifetime_credits = lifetime_credits + NEW.amount
        WHERE college_id = NEW.college_id;
    ELSIF NEW.transaction_type = 'DEBIT' THEN
        UPDATE college_reward_pools 
        SET lifetime_debits = lifetime_debits + NEW.amount
        WHERE college_id = NEW.college_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_pool_lifetime_stats
AFTER INSERT ON pool_transactions
FOR EACH ROW
EXECUTE FUNCTION update_pool_lifetime_stats();

-- =====================================================
-- 5. CREATE TRIGGER TO AUTO-UPDATE updated_at
-- =====================================================
CREATE OR REPLACE FUNCTION update_pool_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_pool_updated_at
BEFORE UPDATE ON college_reward_pools
FOR EACH ROW
EXECUTE FUNCTION update_pool_updated_at();

-- =====================================================
-- 6. CREATE VIEW FOR POOL ANALYTICS
-- =====================================================
CREATE OR REPLACE VIEW pool_analytics AS
SELECT 
    crp.college_id,
    c.name as college_name,
    crp.total_balance,
    crp.reserved_balance,
    crp.available_balance,
    crp.initial_allocation,
    crp.lifetime_credits,
    crp.lifetime_debits,
    crp.low_balance_threshold,
    CASE 
        WHEN crp.available_balance < crp.low_balance_threshold THEN true
        ELSE false
    END as is_low_balance,
    (SELECT COUNT(*) FROM pool_transactions WHERE college_id = crp.college_id AND transaction_type = 'CREDIT') as total_credit_transactions,
    (SELECT COUNT(*) FROM pool_transactions WHERE college_id = crp.college_id AND transaction_type = 'DEBIT') as total_debit_transactions,
    (SELECT COUNT(*) FROM pool_transactions WHERE college_id = crp.college_id AND reason = 'welcome_bonus') as welcome_bonuses_given,
    (SELECT COUNT(*) FROM pool_transactions WHERE college_id = crp.college_id AND reason = 'post_reward') as post_rewards_given,
    (SELECT COUNT(*) FROM pool_transactions WHERE college_id = crp.college_id AND reason = 'admin_reward') as admin_rewards_given,
    crp.created_at,
    crp.updated_at
FROM college_reward_pools crp
JOIN colleges c ON c.id = crp.college_id;

-- =====================================================
-- MIGRATION COMPLETE
-- =====================================================
-- Summary:
-- ✅ Created college_reward_pools table
-- ✅ Created pool_transactions log table
-- ✅ Initialized pools for existing colleges (10,000 points each)
-- ✅ Created triggers for automatic stats updates
-- ✅ Created analytics view
-- ✅ Added indexes for performance
