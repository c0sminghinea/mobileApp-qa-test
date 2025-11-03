-- ========================================
-- Macadam Streaks Test Data Setup
-- ========================================
-- This script initializes test data for automated testing
-- of the streaks functionality
-- ========================================

-- Clean up existing test data (optional - uncomment if needed)
-- DELETE FROM Steps WHERE userId IN ('test-user-new', 'test-user-active-streak', 'test-user-with-freezers', 'test-user-no-freezers', 'test-user-buyer');
-- DELETE FROM FreezeDays WHERE freezeID IN (SELECT freezeID FROM Streaks WHERE userId IN ('test-user-new', 'test-user-active-streak', 'test-user-with-freezers', 'test-user-no-freezers', 'test-user-buyer'));
-- DELETE FROM Streaks WHERE userId IN ('test-user-new', 'test-user-active-streak', 'test-user-active-streak', 'test-user-with-freezers', 'test-user-no-freezers', 'test-user-buyer');

-- ========================================
-- SCENARIO 1: New User - No Existing Streak
-- ========================================
-- Purpose: Test streak creation from scratch
-- Expected: POST /steps should create first streak with counter = 1

-- No Streaks record needed - will be created by API
-- No FreezeDays record needed
-- No Steps record needed initially


-- ========================================
-- SCENARIO 2: Active Streak User
-- ========================================
-- Purpose: Test streak increment on consecutive day
-- Expected: POST /steps should increment counter from 5 to 6

INSERT INTO Streaks (userId, startDate, endDate, counter, freezeID)
VALUES (
  'test-user-active-streak',
  DATE_SUB(NOW(), INTERVAL 5 DAY), -- Started 5 days ago
  NULL, -- Active streak (no end date)
  5,
  NULL -- No freeze days used
);

-- Insert historical steps for the last 5 days
INSERT INTO Steps (userId, stepsNumber, createdAt)
VALUES 
  ('test-user-active-streak', 10000, DATE_SUB(NOW(), INTERVAL 5 DAY)),
  ('test-user-active-streak', 11000, DATE_SUB(NOW(), INTERVAL 4 DAY)),
  ('test-user-active-streak', 9500, DATE_SUB(NOW(), INTERVAL 3 DAY)),
  ('test-user-active-streak', 12000, DATE_SUB(NOW(), INTERVAL 2 DAY)),
  ('test-user-active-streak', 10500, DATE_SUB(NOW(), INTERVAL 1 DAY));


-- ========================================
-- SCENARIO 3: User with Freezers Available
-- ========================================
-- Purpose: Test automatic freezer consumption when missing a day
-- Expected: /streaks/check should show toolsUsed = 1, streak preserved

INSERT INTO Streaks (userId, startDate, endDate, counter, freezeID)
VALUES (
  'test-user-with-freezers',
  DATE_SUB(NOW(), INTERVAL 8 DAY), -- Started 8 days ago
  NULL, -- Active streak
  8,
  'freeze-group-1' -- Reference to freeze days
);

-- Insert 2 available freezers for this user
INSERT INTO FreezeDays (freezeID, freezeStartDate, freezeEndDate, freezePrice)
VALUES 
  ('freeze-group-1', NULL, NULL, 50), -- Available freezer 1
  ('freeze-group-1', NULL, NULL, 50); -- Available freezer 2

-- Insert steps for last 8 days, but SKIP yesterday to trigger freezer usage
INSERT INTO Steps (userId, stepsNumber, createdAt)
VALUES 
  ('test-user-with-freezers', 10000, DATE_SUB(NOW(), INTERVAL 8 DAY)),
  ('test-user-with-freezers', 11000, DATE_SUB(NOW(), INTERVAL 7 DAY)),
  ('test-user-with-freezers', 9500, DATE_SUB(NOW(), INTERVAL 6 DAY)),
  ('test-user-with-freezers', 12000, DATE_SUB(NOW(), INTERVAL 5 DAY)),
  ('test-user-with-freezers', 10500, DATE_SUB(NOW(), INTERVAL 4 DAY)),
  ('test-user-with-freezers', 11500, DATE_SUB(NOW(), INTERVAL 3 DAY)),
  ('test-user-with-freezers', 10000, DATE_SUB(NOW(), INTERVAL 2 DAY));
  -- MISSING: yesterday's steps (will trigger freezer)


-- ========================================
-- SCENARIO 4: User without Freezers - Streak Lost
-- ========================================
-- Purpose: Test streak reset when missing a day without freezers
-- Expected: /streaks/check should show hasLost = true

INSERT INTO Streaks (userId, startDate, endDate, counter, freezeID)
VALUES (
  'test-user-no-freezers',
  DATE_SUB(NOW(), INTERVAL 10 DAY), -- Started 10 days ago
  NULL, -- Was active, will be ended by system
  10,
  NULL -- No freezers available
);

-- Insert steps for 10 days, but SKIP yesterday and today
INSERT INTO Steps (userId, stepsNumber, createdAt)
VALUES 
  ('test-user-no-freezers', 10000, DATE_SUB(NOW(), INTERVAL 10 DAY)),
  ('test-user-no-freezers', 11000, DATE_SUB(NOW(), INTERVAL 9 DAY)),
  ('test-user-no-freezers', 9500, DATE_SUB(NOW(), INTERVAL 8 DAY)),
  ('test-user-no-freezers', 12000, DATE_SUB(NOW(), INTERVAL 7 DAY)),
  ('test-user-no-freezers', 10500, DATE_SUB(NOW(), INTERVAL 6 DAY)),
  ('test-user-no-freezers', 11500, DATE_SUB(NOW(), INTERVAL 5 DAY)),
  ('test-user-no-freezers', 10000, DATE_SUB(NOW(), INTERVAL 4 DAY)),
  ('test-user-no-freezers', 12500, DATE_SUB(NOW(), INTERVAL 3 DAY)),
  ('test-user-no-freezers', 11000, DATE_SUB(NOW(), INTERVAL 2 DAY));
  -- MISSING: yesterday's steps (streak will be lost)


-- ========================================
-- SCENARIO 5: User Ready to Buy Freezers
-- ========================================
-- Purpose: Test freezer purchase functionality
-- Expected: POST /streaks/recovery-tools/buy should succeed

-- This user has no streak yet, but has coins to buy freezers
-- Note: Coins are likely in a separate Users table not provided in schema
-- Assuming the API handles coin balance separately

-- No Streaks record needed initially
-- No FreezeDays record needed initially


-- ========================================
-- SCENARIO 6: User with Maximum Freezers
-- ========================================
-- Purpose: Test purchase limit enforcement
-- Expected: POST /streaks/recovery-tools/buy should return error

INSERT INTO Streaks (userId, startDate, endDate, counter, freezeID)
VALUES (
  'test-user-max-freezers',
  DATE_SUB(NOW(), INTERVAL 3 DAY),
  NULL,
  3,
  'freeze-group-2'
);

-- Insert 2 freezers (maximum allowed)
INSERT INTO FreezeDays (freezeID, freezeStartDate, freezeEndDate, freezePrice)
VALUES 
  ('freeze-group-2', NULL, NULL, 50), -- Available freezer 1
  ('freeze-group-2', NULL, NULL, 50); -- Available freezer 2 (MAX)


-- ========================================
-- SCENARIO 7: Monthly History Test Data
-- ========================================
-- Purpose: Test /streaks/month-history endpoint
-- Expected: Returns correct history for January 2025

INSERT INTO Streaks (userId, startDate, endDate, counter, freezeID)
VALUES 
  ('test-user-history', '2025-01-01 00:00:00', '2025-01-05 23:59:59', 5, NULL),
  ('test-user-history', '2025-01-10 00:00:00', NULL, 15, NULL); -- Active streak

INSERT INTO Steps (userId, stepsNumber, createdAt)
VALUES 
  ('test-user-history', 10000, '2025-01-01 12:00:00'),
  ('test-user-history', 11000, '2025-01-02 12:00:00'),
  ('test-user-history', 9500, '2025-01-03 12:00:00'),
  ('test-user-history', 12000, '2025-01-04 12:00:00'),
  ('test-user-history', 10500, '2025-01-05 12:00:00'),
  -- Gap from Jan 6-9
  ('test-user-history', 11500, '2025-01-10 12:00:00'),
  ('test-user-history', 10000, '2025-01-11 12:00:00'),
  ('test-user-history', 12500, '2025-01-12 12:00:00');


-- ========================================
-- Verification Queries (Optional)
-- ========================================
-- Run these to verify data was inserted correctly

-- Check all test users' streaks
-- SELECT userId, counter, startDate, endDate, freezeID 
-- FROM Streaks 
-- WHERE userId LIKE 'test-user%'
-- ORDER BY userId;

-- Check freezer availability
-- SELECT freezeID, COUNT(*) as freezer_count
-- FROM FreezeDays 
-- WHERE freezeStartDate IS NULL
-- GROUP BY freezeID;

-- Check steps history
-- SELECT userId, COUNT(*) as steps_count, MIN(createdAt) as first_step, MAX(createdAt) as last_step
-- FROM Steps 
-- WHERE userId LIKE 'test-user%'
-- GROUP BY userId
-- ORDER BY userId;