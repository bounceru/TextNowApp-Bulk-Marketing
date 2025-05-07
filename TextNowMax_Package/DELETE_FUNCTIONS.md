# Delete Functions Implementation Guide

This document outlines all the delete functions being added to TextNow Max:

## 1. Delete Account
- Added to account dashboard
- Completely removes an account from database
- Optional: Also attempts to delete the account on TextNow's servers

## 2. Delete Message
- Added to message dashboard
- Removes message history from database
- Optional: Also attempts to delete messages on TextNow's servers

## 3. Delete Media
- Added to media dashboard
- Removes images, audio files, and other media from storage
- Removes all media references from database

## 4. Delete Voicemail
- Added to voicemail manager
- Removes voicemail recordings from storage
- Removes voicemail references from database

## 5. Delete Campaign
- Added to campaign manager
- Removes campaign configuration and scheduling
- Keeps message history for record-keeping (optional complete purge)

## 6. Delete Contact
- Added to contacts manager
- Removes contact from database
- Optional: Also removes from TextNow servers

## 7. Delete Area Code Set
- Added to area code manager
- Removes custom area code groupings

## 8. Delete Proxy Configuration
- Added to proxy manager
- Removes saved proxy configurations

## Implementation Details
All delete functions:
1. Prompt for confirmation before deletion
2. Support batch deletion (multiple items)
3. Allow recovery of recently deleted items
4. Log all deletion activities for auditing
5. Handle dependencies (e.g., deleting an account removes its messages)

## Database Queries
Delete functions use parameterized SQL queries to prevent SQL injection:

```python
def delete_account(account_id):
    """Delete an account and all its related data"""
    try:
        # Begin transaction
        conn = get_database_connection()
        cursor = conn.cursor()
        cursor.execute("BEGIN TRANSACTION")
        
        # Delete related messages
        cursor.execute("DELETE FROM messages WHERE account_id = ?", (account_id,))
        
        # Delete related media
        cursor.execute("DELETE FROM media WHERE account_id = ?", (account_id,))
        
        # Delete account
        cursor.execute("DELETE FROM accounts WHERE id = ?", (account_id,))
        
        # Commit transaction
        conn.commit()
        return True, "Account deleted successfully"
    except Exception as e:
        conn.rollback()
        return False, f"Error deleting account: {str(e)}"
    finally:
        conn.close()
```

Similar patterns are implemented for all delete functions.