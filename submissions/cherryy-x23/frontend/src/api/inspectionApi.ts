import {
  HealthResponse,
  Inspection,
  InspectionCreatePayload,
  OverridePayload,
} from '../types/inspection';

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export class ApiError extends Error {
  statusCode: number;
  data: any;

  constructor(message: string, statusCode: number, data?: any) {
    super(message);
    this.name = 'ApiError';
    this.statusCode = statusCode;
    this.data = data;
  }
}

async function request<T>(endpoint: string, options: RequestInit = {}, orgId?: string): Promise<T> {
  const url = `${BASE_URL}${endpoint}`;
  const headers = new Headers(options.headers || {});
  headers.set('Content-Type', 'application/json');

  if (orgId) {
    headers.set('X-Org-ID', orgId);
  }

  try {
    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (!response.ok) {
      let errorMessage = `HTTP Error ${response.status}`;
      let errorData: any = null;

      try {
        errorData = await response.json();
        if (errorData?.detail) {
          if (typeof errorData.detail === 'string') {
            errorMessage = errorData.detail;
          } else if (Array.isArray(errorData.detail)) {
            errorMessage = errorData.detail.map((d: any) => d.msg || JSON.stringify(d)).join(', ');
          }
        }
      } catch {
        // Response was not JSON
      }

      if (response.status === 404) {
        throw new ApiError(errorMessage || 'Inspection not found or inaccessible.', 404, errorData);
      } else if (response.status === 422) {
        throw new ApiError(errorMessage || 'Validation error in request payload.', 422, errorData);
      } else if (response.status >= 500) {
        throw new ApiError('Something went wrong while processing this inspection.', response.status, errorData);
      }

      throw new ApiError(errorMessage, response.status, errorData);
    }

    return (await response.json()) as T;
  } catch (err: any) {
    if (err instanceof ApiError) {
      throw err;
    }
    // Network / connection errors
    throw new ApiError(
      'Backend unavailable. Please make sure the FastAPI server is running.',
      0,
      { originalError: err.message }
    );
  }
}

export const inspectionApi = {
  async getHealth(): Promise<HealthResponse> {
    return request<HealthResponse>('/health');
  },

  async createInspection(payload: InspectionCreatePayload): Promise<Inspection> {
    return request<Inspection>(
      '/api/v1/inspections',
      {
        method: 'POST',
        body: JSON.stringify(payload),
      },
      payload.org_id
    );
  },

  async runInspection(inspectionId: string, orgId: string): Promise<any> {
    const query = new URLSearchParams({ org_id: orgId }).toString();
    return request<any>(
      `/api/v1/inspections/${inspectionId}/run?${query}`,
      {
        method: 'POST',
      },
      orgId
    );
  },

  async getInspection(inspectionId: string, orgId: string): Promise<Inspection> {
    const query = new URLSearchParams({ org_id: orgId }).toString();
    return request<Inspection>(
      `/api/v1/inspections/${inspectionId}?${query}`,
      {
        method: 'GET',
      },
      orgId
    );
  },

  async listInspections(
    orgId: string,
    filters?: { status?: string; verdict?: string; limit?: number }
  ): Promise<Inspection[]> {
    const params = new URLSearchParams({ org_id: orgId });
    if (filters?.status) params.append('status', filters.status);
    if (filters?.verdict) params.append('verdict', filters.verdict);
    if (filters?.limit) params.append('limit', String(filters.limit));

    return request<Inspection[]>(
      `/api/v1/inspections?${params.toString()}`,
      {
        method: 'GET',
      },
      orgId
    );
  },

  async overrideInspection(
    inspectionId: string,
    orgId: string,
    payload: OverridePayload
  ): Promise<any> {
    const query = new URLSearchParams({ org_id: orgId }).toString();
    return request<any>(
      `/api/v1/inspections/${inspectionId}/override?${query}`,
      {
        method: 'POST',
        body: JSON.stringify(payload),
      },
      orgId
    );
  },

  async seedDemoScenarios(): Promise<any> {
    return request<any>('/api/v1/demo/seed', {
      method: 'POST',
    });
  },

  async resetDemoRepository(): Promise<any> {
    return request<any>('/api/v1/demo/reset', {
      method: 'POST',
    });
  },
};

