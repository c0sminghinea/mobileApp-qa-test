# Test Specification - Streaks Feature

## 📊 Overview
This document outlines the test strategy for the Macadam Streaks functionality. The streaks feature encourages users to maintain daily step validation through a consecutive day counter system with recovery tools (freezers).

---

## 🎯 Test Objectives
- Verify streak creation and increment logic
- Validate freezer (recovery tool) consumption mechanism
- Test edge cases and error handling
- Ensure data consistency across endpoints

---

## 🔍 Priority Test Scenarios

### **PRIORITY 1: Happy Path - Daily Streak Progression**
**Business Value**: Core functionality - users must be able to build streaks
**Risk Level**: HIGH

#### Scenario 1.1: New User First Streak Creation
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | User with no existing streak validates steps (10,000 steps) | HTTP 201 - Streak created with counter = 1 |
| 2 | GET /streaks | Returns counter = 1, hasValidatedToday = true |
| 3 | Verify database | Streaks table has new record with counter = 1, endDate = null |

**Test Data Required**:
- User: `test-user-new` (no existing streak)
- Steps: 10000

**Expected Response**:
```json
{
  "data": {
    "coinsEarned": 50,
    "streak": {
      "id": "streak-xxx",
      "counter": 1,
      "startDate": "2025-01-01T00:00:00Z",
      "endDate": null
    }
  }
}
```

#### Scenario 1.2: Consecutive Day Streak Increment
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | User has streak = 5 from yesterday | Database shows counter = 5 |
| 2 | User validates steps today (12,000 steps) | HTTP 201 - Streak counter increments to 6 |
| 3 | GET /streaks | Returns counter = 6, longestStreak = 6 (if new record) |
| 4 | Verify milestone tracking | If counter reaches 7, 14, or 30, milestone is recorded |

**Test Data Required**:
- User: `test-user-active-streak`
- Existing streak: counter = 5, created yesterday
- Steps: 12000

---

### **PRIORITY 2: Freezer Mechanism - Streak Recovery**
**Business Value**: Premium feature - keeps users engaged when they miss days
**Risk Level**: HIGH

#### Scenario 2.1: Automatic Freezer Consumption on Missed Day
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | User has streak = 8, available freezers = 2 | Database confirms initial state |
| 2 | User misses validation yesterday (simulate by not calling POST /steps) | System detects gap |
| 3 | GET /streaks/check | Returns hasLost = false, toolsUsed = 1, counter still = 8 |
| 4 | Verify database | FreezeDays record created with freezeStartDate = yesterday |
| 5 | GET /streaks | Shows available freezers = 1, counter = 8 |

**Test Data Required**:
- User: `test-user-with-freezers`
- Streak: counter = 8, last validation = 2 days ago
- Available freezers: 2

**Expected Response from /streaks/check**:
```json
{
  "hasLost": false,
  "streak": {
    "id": "streak-123",
    "counter": 8,
    "startDate": "2025-01-01T00:00:00Z",
    "endDate": null
  },
  "toolsUsed": 1
}
```

#### Scenario 2.2: Streak Lost - No Freezers Available
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | User has streak = 10, available freezers = 0 | Database confirms state |
| 2 | User misses validation yesterday | System detects gap |
| 3 | GET /streaks/check | Returns hasLost = true, streak = null, counterLastStreak = 10 |
| 4 | Verify database | Streaks table record has endDate populated |
| 5 | Next POST /steps creates NEW streak with counter = 1 | New streak ID generated |

**Test Data Required**:
- User: `test-user-no-freezers`
- Streak: counter = 10, last validation = 2 days ago
- Available freezers: 0

---

### **PRIORITY 3: Freezer Purchase and Limits**
**Business Value**: Monetization feature - users buy freezers with coins
**Risk Level**: MEDIUM

#### Scenario 3.1: Successful Freezer Purchase
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | User has 100 coins, 0 freezers | Database confirms initial state |
| 2 | POST /streaks/recovery-tools/buy with quantity = 1 | HTTP 200 - Purchase successful |
| 3 | GET /streaks | Shows tools.available = 1, user coins deducted |
| 4 | Verify database | FreezeDays record created with appropriate price |

**Test Data Required**:
- User: `test-user-buyer`
- Coins: 100
- Current freezers: 0

#### Scenario 3.2: Purchase Blocked - Insufficient Coins
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | User has 10 coins (below freezer price) | Database confirms low balance |
| 2 | POST /streaks/recovery-tools/buy with quantity = 1 | HTTP 400 - Error: "not_enough_coins" |
| 3 | GET /streaks | Freezers remain unchanged |

#### Scenario 3.3: Purchase Blocked - Maximum Freezers Reached
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | User has 2 freezers (maximum allowed) | Database confirms max freezers |
| 2 | POST /streaks/recovery-tools/buy with quantity = 1 | HTTP 400 - Error: "already_have_max_recovery_tools" |
| 3 | GET /streaks | Freezers remain at 2 |

---

## 🧪 Additional Edge Cases (Nice to Have)

### Edge Case 1: Invalid Steps Range
- **Test**: POST /steps with steps = 200,000 (above max)
- **Expected**: HTTP 400 - "steps must be between 0 and 150000"

### Edge Case 2: Double Validation Same Day
- **Test**: User validates steps twice in same day
- **Expected**: Counter doesn't increment twice, only first validation counts

### Edge Case 3: Monthly History for Empty Month
- **Test**: GET /streaks/month-history/2024-12 (month with no activity)
- **Expected**: HTTP 200 - Empty streaks array

### Edge Case 4: Invalid Month Format
- **Test**: GET /streaks/month-history/25-01 (invalid format)
- **Expected**: HTTP 400 or appropriate error

---

## 📋 Test Data Summary

| User ID | Initial Streak | Freezers | Coins | Purpose |
|---------|---------------|----------|-------|---------|
| test-user-new | 0 | 0 | 100 | New streak creation |
| test-user-active-streak | 5 | 1 | 50 | Streak increment |
| test-user-with-freezers | 8 | 2 | 200 | Freezer consumption |
| test-user-no-freezers | 10 | 0 | 0 | Streak loss |
| test-user-buyer | 0 | 0 | 100 | Freezer purchase |

---

## ✅ Test Execution Strategy

### Automated Tests (pytest)
- API endpoint calls with requests library
- Response validation (status codes, data structures)
- Database state verification queries
- Reusable helper functions for common operations

### Manual Verification
- Database records inspection after test runs
- Edge case exploratory testing
- UI integration testing (if applicable)

---

## 📊 Success Criteria

| Metric | Target |
|--------|--------|
| Test Coverage | 3 priority scenarios fully automated |
| Pass Rate | 100% for priority scenarios |
| Execution Time | < 30 seconds for full suite |
| Code Quality | All functions documented, no duplication |

---

## 🚀 Test Execution Order

1. **Setup Phase**: Run SQL inserts to create test data
2. **Priority 1**: Test basic streak functionality
3. **Priority 2**: Test freezer mechanism
4. **Priority 3**: Test purchase functionality
5. **Cleanup**: (Optional) Reset database to initial state

---

## 📝 Notes for Developers

- Ensure test database is isolated from production
- All timestamps should use UTC timezone
- Consider adding database constraints for max freezers (2)
- API should handle concurrent requests gracefully

## 📝 Notes for Product Managers

- Priority scenarios cover 80% of user journey
- Freezer mechanic is critical for retention - must work flawlessly
- Consider analytics tracking for streak milestones (7, 14, 30 days)
- Purchase flow errors should be user-friendly in production