-- ============================================================
-- KNOWLEDGE FACTS SCHEMA
-- ============================================================
--
-- Knowledge = Certain facts with NO strength.
-- Different from beliefs which have strength and learn.
--
-- Change mechanism: REPLACE (supersede old, insert new)
-- Not learning - facts don't have feedback loops.
--
-- Scope hierarchy: global → industry → org → person
-- Narrower scope wins at resolution time.
-- ============================================================

-- Main facts table
CREATE TABLE IF NOT EXISTS knowledge_facts (
    -- Identity
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    fact_key TEXT NOT NULL,  -- Semantic key (e.g., "fiscal_year_end", "uses_accrual_basis")

    -- Scope: determines which contexts this fact applies to
    scope_type TEXT NOT NULL CHECK (scope_type IN ('global', 'industry', 'org', 'person')),
    scope_id TEXT,  -- NULL for global; industry name; org_id; person_id

    -- The fact itself
    statement TEXT NOT NULL,  -- Human-readable: "Fiscal year ends December 31"

    -- Classification
    category TEXT NOT NULL CHECK (category IN (
        'accounting',    -- GAAP, double-entry, accrual basis
        'regulatory',    -- SEC, SOX, ASC standards, compliance requirements
        'process',       -- How things work: "Month-end close takes 5 days"
        'entity',        -- Identity facts: company name, person role, size
        'temporal',      -- Time-related: fiscal year, timezone, deadlines
        'context'        -- Situational: rapport hooks, working preferences
    )),

    -- Provenance: where did this fact come from?
    source_type TEXT NOT NULL CHECK (source_type IN (
        'system',        -- Seeded at init (global accounting principles)
        'knowledge_pack', -- From industry knowledge packs
        'apollo',        -- Enriched from Apollo API
        'user',          -- User explicitly stated this
        'admin',         -- Admin/config portal
        'inferred',      -- Derived from other facts or patterns
        'integration'    -- From connected system (ERP, bank, etc.)
    )),
    source_ref JSONB DEFAULT '{}',  -- Reference to source: {"apollo_person_id": "...", "stated_in_message": "..."}

    -- Lifecycle
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN (
        'active',        -- Current, valid fact
        'superseded',    -- Replaced by newer fact
        'deleted'        -- Explicitly removed (soft delete)
    )),

    -- Supersession chain (for "replace" mechanism)
    superseded_by UUID REFERENCES knowledge_facts(id),
    supersedes UUID REFERENCES knowledge_facts(id),  -- What this fact replaced
    supersession_reason TEXT,  -- "User correction", "Apollo update", "Admin override"

    -- Validity window (facts can be time-bounded)
    valid_from TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    valid_until TIMESTAMPTZ,  -- NULL = indefinitely valid

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ,

    -- Extensibility
    tags TEXT[] DEFAULT '{}',  -- ["gaap", "revenue", "asc_606"]
    metadata JSONB DEFAULT '{}',  -- Additional structured data

    -- Confidence (NOT strength! This is "how certain are we this fact is correct")
    -- Used for inferred facts. System/user facts are 1.0.
    confidence FLOAT DEFAULT 1.0 CHECK (confidence >= 0 AND confidence <= 1),

    -- Constraints for data integrity
    CONSTRAINT chk_scope_id_not_empty CHECK (scope_id IS NULL OR length(scope_id) > 0),
    CONSTRAINT chk_no_self_supersession CHECK (superseded_by IS NULL OR superseded_by != id),
    CONSTRAINT chk_statement_length CHECK (length(statement) BETWEEN 1 AND 2000),
    CONSTRAINT chk_fact_key_length CHECK (length(fact_key) BETWEEN 1 AND 200),
    CONSTRAINT chk_valid_window CHECK (valid_until IS NULL OR valid_until > valid_from)
);

-- Unique active fact per key within scope
-- Prevents two active "fiscal_year_end" facts for same org
CREATE UNIQUE INDEX idx_facts_unique_active
ON knowledge_facts(scope_type, COALESCE(scope_id, ''), fact_key)
WHERE status = 'active';

-- Fast scope queries for mount
CREATE INDEX idx_facts_global
ON knowledge_facts(category)
WHERE scope_type = 'global' AND status = 'active';

CREATE INDEX idx_facts_industry
ON knowledge_facts(scope_id, category)
WHERE scope_type = 'industry' AND status = 'active';

CREATE INDEX idx_facts_org
ON knowledge_facts(scope_id, category)
WHERE scope_type = 'org' AND status = 'active';

CREATE INDEX idx_facts_person
ON knowledge_facts(scope_id, category)
WHERE scope_type = 'person' AND status = 'active';

-- Tag-based queries (GIN for array containment)
CREATE INDEX idx_facts_tags
ON knowledge_facts USING GIN(tags)
WHERE status = 'active';

-- Source queries (for auditing)
CREATE INDEX idx_facts_source
ON knowledge_facts(source_type, created_at DESC)
WHERE status = 'active';

-- Supersession chain queries
CREATE INDEX idx_facts_superseded_by
ON knowledge_facts(superseded_by)
WHERE superseded_by IS NOT NULL;


-- ============================================================
-- ORG INDUSTRIES MAPPING
-- ============================================================
-- An org can operate in multiple industries.
-- Used to determine which industry facts apply.

CREATE TABLE IF NOT EXISTS org_industries (
    org_id TEXT NOT NULL,
    industry TEXT NOT NULL,  -- Matches scope_id for industry-scoped facts
    is_primary BOOLEAN DEFAULT FALSE,  -- Primary industry for this org
    source TEXT NOT NULL CHECK (source IN ('apollo', 'admin', 'inferred')),
    confidence FLOAT DEFAULT 1.0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (org_id, industry)
);

CREATE INDEX idx_org_industries_org ON org_industries(org_id);


-- ============================================================
-- FACT CORRECTIONS LOG
-- ============================================================
-- Detailed audit trail for when facts are corrected.
-- Supersession chain shows WHAT changed, this shows WHY and HOW.

CREATE TABLE IF NOT EXISTS knowledge_corrections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- What was corrected
    old_fact_id UUID NOT NULL REFERENCES knowledge_facts(id),
    new_fact_id UUID REFERENCES knowledge_facts(id),  -- NULL if just deleted

    -- Who corrected it
    corrected_by_type TEXT NOT NULL CHECK (corrected_by_type IN (
        'user',          -- User said "that's wrong"
        'admin',         -- Admin portal correction
        'system',        -- Automatic correction (e.g., Apollo refresh)
        'integration'    -- Connected system provided update
    )),
    corrected_by_ref TEXT,  -- user_id, admin_id, integration_name

    -- Why
    reason TEXT NOT NULL,  -- "User stated fiscal year ends June 30"
    correction_type TEXT NOT NULL CHECK (correction_type IN (
        'factual_error',     -- The fact was simply wrong
        'outdated',          -- Fact was true but no longer is
        'more_specific',     -- Replacing with more precise fact
        'scope_change',      -- Moving fact to different scope
        'source_upgrade'     -- Better source available (user > inferred)
    )),

    -- Context
    context JSONB DEFAULT '{}',  -- Message ID, conversation context, etc.

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_corrections_old_fact ON knowledge_corrections(old_fact_id);
CREATE INDEX idx_corrections_new_fact ON knowledge_corrections(new_fact_id);
CREATE INDEX idx_corrections_time ON knowledge_corrections(created_at DESC);


-- ============================================================
-- VIEWS FOR COMMON QUERIES
-- ============================================================

-- Active facts only (most common query)
CREATE OR REPLACE VIEW active_facts AS
SELECT * FROM knowledge_facts
WHERE status = 'active'
AND (valid_until IS NULL OR valid_until > NOW());

-- Facts with their correction history
CREATE OR REPLACE VIEW facts_with_history AS
SELECT
    f.*,
    c.reason as correction_reason,
    c.correction_type,
    c.corrected_by_type,
    c.created_at as corrected_at,
    prev.statement as previous_statement
FROM knowledge_facts f
LEFT JOIN knowledge_corrections c ON c.new_fact_id = f.id
LEFT JOIN knowledge_facts prev ON f.supersedes = prev.id;


-- ============================================================
-- FUNCTIONS
-- ============================================================

-- Get all facts for a mount context (org + person)
CREATE OR REPLACE FUNCTION get_facts_for_context(
    p_org_id TEXT,
    p_person_id TEXT DEFAULT NULL,
    p_max_facts INTEGER DEFAULT 30
)
RETURNS TABLE (
    id UUID,
    fact_key TEXT,
    scope_type TEXT,
    scope_id TEXT,
    statement TEXT,
    category TEXT,
    source_type TEXT,
    tags TEXT[],
    scope_priority INTEGER
) AS $$
BEGIN
    RETURN QUERY
    WITH org_ind AS (
        SELECT industry FROM org_industries WHERE org_id = p_org_id
    )
    SELECT
        f.id,
        f.fact_key,
        f.scope_type,
        f.scope_id,
        f.statement,
        f.category,
        f.source_type,
        f.tags,
        CASE f.scope_type
            WHEN 'person' THEN 1
            WHEN 'org' THEN 2
            WHEN 'industry' THEN 3
            WHEN 'global' THEN 4
        END as scope_priority
    FROM knowledge_facts f
    WHERE f.status = 'active'
    AND (f.valid_until IS NULL OR f.valid_until > NOW())
    AND (
        f.scope_type = 'global'
        OR (f.scope_type = 'industry' AND f.scope_id IN (SELECT industry FROM org_ind))
        OR (f.scope_type = 'org' AND f.scope_id = p_org_id)
        OR (f.scope_type = 'person' AND f.scope_id = p_person_id)
    )
    ORDER BY scope_priority, f.category, f.created_at DESC
    LIMIT p_max_facts;
END;
$$ LANGUAGE plpgsql STABLE;


-- Replace a fact (the "replace" mechanism)
CREATE OR REPLACE FUNCTION replace_fact(
    p_old_fact_id UUID,
    p_new_statement TEXT,
    p_reason TEXT,
    p_correction_type TEXT,
    p_corrected_by_type TEXT,
    p_corrected_by_ref TEXT DEFAULT NULL
)
RETURNS UUID AS $$
DECLARE
    v_old_fact knowledge_facts%ROWTYPE;
    v_new_fact_id UUID;
BEGIN
    -- Get the old fact
    SELECT * INTO v_old_fact FROM knowledge_facts WHERE id = p_old_fact_id;

    IF v_old_fact.id IS NULL THEN
        RAISE EXCEPTION 'Fact not found: %', p_old_fact_id;
    END IF;

    IF v_old_fact.status != 'active' THEN
        RAISE EXCEPTION 'Cannot replace non-active fact: %', p_old_fact_id;
    END IF;

    -- Create new fact
    INSERT INTO knowledge_facts (
        fact_key, scope_type, scope_id, statement, category,
        source_type, source_ref, supersedes, tags, metadata
    )
    VALUES (
        v_old_fact.fact_key,
        v_old_fact.scope_type,
        v_old_fact.scope_id,
        p_new_statement,
        v_old_fact.category,
        p_corrected_by_type,
        jsonb_build_object('correction_of', p_old_fact_id, 'corrected_by', p_corrected_by_ref),
        p_old_fact_id,
        v_old_fact.tags,
        v_old_fact.metadata
    )
    RETURNING id INTO v_new_fact_id;

    -- Supersede old fact
    UPDATE knowledge_facts
    SET status = 'superseded',
        superseded_by = v_new_fact_id,
        supersession_reason = p_reason,
        valid_until = NOW(),
        updated_at = NOW()
    WHERE id = p_old_fact_id;

    -- Log the correction
    INSERT INTO knowledge_corrections (
        old_fact_id, new_fact_id, corrected_by_type, corrected_by_ref,
        reason, correction_type
    )
    VALUES (
        p_old_fact_id, v_new_fact_id, p_corrected_by_type, p_corrected_by_ref,
        p_reason, p_correction_type
    );

    RETURN v_new_fact_id;
END;
$$ LANGUAGE plpgsql;


-- Soft delete a fact
CREATE OR REPLACE FUNCTION delete_fact(
    p_fact_id UUID,
    p_reason TEXT,
    p_deleted_by_type TEXT,
    p_deleted_by_ref TEXT DEFAULT NULL
)
RETURNS VOID AS $$
BEGIN
    UPDATE knowledge_facts
    SET status = 'deleted',
        deleted_at = NOW(),
        supersession_reason = p_reason,
        updated_at = NOW()
    WHERE id = p_fact_id;

    INSERT INTO knowledge_corrections (
        old_fact_id, new_fact_id, corrected_by_type, corrected_by_ref,
        reason, correction_type
    )
    VALUES (
        p_fact_id, NULL, p_deleted_by_type, p_deleted_by_ref,
        p_reason, 'factual_error'
    );
END;
$$ LANGUAGE plpgsql;


-- Get fact history (follow supersession chain)
CREATE OR REPLACE FUNCTION get_fact_history(p_fact_key TEXT, p_scope_type TEXT, p_scope_id TEXT)
RETURNS TABLE (
    id UUID,
    statement TEXT,
    status TEXT,
    source_type TEXT,
    created_at TIMESTAMPTZ,
    valid_until TIMESTAMPTZ,
    supersession_reason TEXT,
    version_number BIGINT
) AS $$
BEGIN
    RETURN QUERY
    WITH RECURSIVE fact_chain AS (
        -- Start with current active fact (or most recent)
        SELECT f.*, 1::BIGINT as version_num
        FROM knowledge_facts f
        WHERE f.fact_key = p_fact_key
        AND f.scope_type = p_scope_type
        AND COALESCE(f.scope_id, '') = COALESCE(p_scope_id, '')
        AND f.superseded_by IS NULL  -- Head of chain

        UNION ALL

        -- Walk back through supersession chain
        SELECT f.*, fc.version_num + 1
        FROM knowledge_facts f
        JOIN fact_chain fc ON f.superseded_by = fc.id
    )
    SELECT
        fc.id,
        fc.statement,
        fc.status,
        fc.source_type,
        fc.created_at,
        fc.valid_until,
        fc.supersession_reason,
        fc.version_num
    FROM fact_chain fc
    ORDER BY fc.version_num ASC;
END;
$$ LANGUAGE plpgsql STABLE;
