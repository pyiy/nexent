-- Add agent_id column to conversation_record_t table
-- This migration adds the agent_id field to track which agent was used in each conversation

-- Add the agent_id column to the conversation_record_t table
ALTER TABLE nexent.conversation_record_t 
ADD COLUMN agent_id INTEGER;

-- Add comment to the new column
COMMENT ON COLUMN nexent.conversation_record_t.agent_id IS 'Agent ID used in this conversation';