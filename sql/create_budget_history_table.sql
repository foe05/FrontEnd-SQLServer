-- =============================================
-- Budget History Table Creation Script
-- =============================================
-- Purpose: Track project budget changes over time
-- Features: Time-based budget tracking, full audit trail
-- =============================================

-- Drop table if exists (for clean re-creation)
IF OBJECT_ID('dbo.BudgetHistory', 'U') IS NOT NULL
    DROP TABLE dbo.BudgetHistory;
GO

-- Create BudgetHistory table
CREATE TABLE dbo.BudgetHistory (
    -- Primary Key
    ID INT IDENTITY(1,1) PRIMARY KEY,

    -- Project and Activity identification
    ProjectID NVARCHAR(50) NOT NULL,
    Activity NVARCHAR(200) NOT NULL,

    -- Budget information
    Hours DECIMAL(10,2) NOT NULL,
    ChangeType NVARCHAR(50) NOT NULL, -- 'initial', 'extension', 'correction', 'reduction'

    -- Time validity
    ValidFrom DATE NOT NULL,

    -- Documentation
    Reason NVARCHAR(500) NOT NULL,
    Reference NVARCHAR(200) NULL, -- Contract number, change request, etc.

    -- Audit trail
    CreatedBy NVARCHAR(200) NOT NULL,
    CreatedAt DATETIME2 DEFAULT GETDATE(),

    -- Constraints
    CONSTRAINT CK_BudgetHistory_Hours CHECK (Hours >= 0),
    CONSTRAINT CK_BudgetHistory_ChangeType CHECK (
        ChangeType IN ('initial', 'extension', 'correction', 'reduction')
    )
);
GO

-- Create indexes for performance
CREATE NONCLUSTERED INDEX IX_BudgetHistory_Project_Activity
    ON dbo.BudgetHistory(ProjectID, Activity, ValidFrom DESC);
GO

CREATE NONCLUSTERED INDEX IX_BudgetHistory_ValidFrom
    ON dbo.BudgetHistory(ValidFrom);
GO

CREATE NONCLUSTERED INDEX IX_BudgetHistory_CreatedAt
    ON dbo.BudgetHistory(CreatedAt DESC);
GO

-- Add extended properties for documentation
EXEC sp_addextendedproperty
    @name = N'MS_Description',
    @value = N'Stores complete history of project budget changes with time-based validity',
    @level0type = N'SCHEMA', @level0name = N'dbo',
    @level1type = N'TABLE', @level1name = N'BudgetHistory';
GO

EXEC sp_addextendedproperty
    @name = N'MS_Description',
    @value = N'Date from which this budget entry is valid. Used for time-based budget calculation.',
    @level0type = N'SCHEMA', @level0name = N'dbo',
    @level1type = N'TABLE', @level1name = N'BudgetHistory',
    @level2type = N'COLUMN', @level2name = N'ValidFrom';
GO

-- Create view for current budgets (latest valid entry per project/activity)
CREATE OR ALTER VIEW dbo.vw_CurrentBudgets AS
WITH RankedBudgets AS (
    SELECT
        ProjectID,
        Activity,
        Hours,
        ChangeType,
        ValidFrom,
        Reason,
        Reference,
        CreatedBy,
        CreatedAt,
        ROW_NUMBER() OVER (
            PARTITION BY ProjectID, Activity
            ORDER BY ValidFrom DESC, CreatedAt DESC
        ) AS RowNum
    FROM dbo.BudgetHistory
    WHERE ValidFrom <= CAST(GETDATE() AS DATE)
)
SELECT
    ProjectID,
    Activity,
    SUM(Hours) as TotalHours,
    MAX(ValidFrom) as LastChangeDate,
    MAX(CreatedAt) as LastUpdated,
    MAX(CreatedBy) as LastUpdatedBy
FROM dbo.BudgetHistory
WHERE ValidFrom <= CAST(GETDATE() AS DATE)
GROUP BY ProjectID, Activity;
GO

PRINT 'BudgetHistory table, indexes, and views created successfully!';
PRINT '';
PRINT 'Usage:';
PRINT '  - Insert budget entries with INSERT INTO BudgetHistory (...)';
PRINT '  - Query current budgets: SELECT * FROM vw_CurrentBudgets';
PRINT '  - Query budget at specific date: Add WHERE ValidFrom <= @TargetDate';
GO
