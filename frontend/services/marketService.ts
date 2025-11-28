/**
 * Market service for agent marketplace API calls
 */

import { API_ENDPOINTS } from './api';
import log from '@/lib/logger';
import {
  MarketAgentListResponse,
  MarketAgentDetail,
  MarketCategory,
  MarketTag,
  MarketMcpServer,
  MarketAgentListParams,
} from '@/types/market';

/**
 * Fetch agent list from market with pagination and filters
 */
export async function fetchMarketAgentList(
  params?: MarketAgentListParams
): Promise<MarketAgentListResponse> {
  try {
    const url = API_ENDPOINTS.market.agents(params);
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch market agents: ${response.statusText}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    log.error('Error fetching market agent list:', error);
    throw error;
  }
}

/**
 * Fetch agent detail by agent_id
 */
export async function fetchMarketAgentDetail(
  agentId: number
): Promise<MarketAgentDetail> {
  try {
    const url = API_ENDPOINTS.market.agentDetail(agentId);
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(
        `Failed to fetch market agent detail: ${response.statusText}`
      );
    }

    const data = await response.json();
    return data;
  } catch (error) {
    log.error('Error fetching market agent detail:', error);
    throw error;
  }
}

/**
 * Fetch all categories from market
 */
export async function fetchMarketCategories(): Promise<MarketCategory[]> {
  try {
    const url = API_ENDPOINTS.market.categories;
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(
        `Failed to fetch market categories: ${response.statusText}`
      );
    }

    const data = await response.json();
    return data;
  } catch (error) {
    log.error('Error fetching market categories:', error);
    throw error;
  }
}

/**
 * Fetch all tags from market
 */
export async function fetchMarketTags(): Promise<MarketTag[]> {
  try {
    const url = API_ENDPOINTS.market.tags;
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch market tags: ${response.statusText}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    log.error('Error fetching market tags:', error);
    throw error;
  }
}

/**
 * Fetch MCP servers for specific agent
 */
export async function fetchMarketAgentMcpServers(
  agentId: number
): Promise<MarketMcpServer[]> {
  try {
    const url = API_ENDPOINTS.market.mcpServers(agentId);
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(
        `Failed to fetch agent MCP servers: ${response.statusText}`
      );
    }

    const data = await response.json();
    return data;
  } catch (error) {
    log.error('Error fetching agent MCP servers:', error);
    throw error;
  }
}

const marketService = {
  fetchMarketAgentList,
  fetchMarketAgentDetail,
  fetchMarketCategories,
  fetchMarketTags,
  fetchMarketAgentMcpServers,
};

export default marketService;

