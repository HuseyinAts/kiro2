/**
 * Organization Service — B2B okul onboarding (org üye/lisans/DPA)
 * Backend: backend/api/org_api.py + backend/api/org_billing_api.py (prefix /api/v1/org)
 * Auth: httpOnly cookie (apiClient withCredentials)
 */

import apiClient from './apiClient';

export type OrgRole = 'SCHOOL_ADMIN' | 'TEACHER' | 'STUDENT' | 'PARENT' | 'OBSERVER';

export interface OrgMember {
  user_id: string
  email?: string | null
  org_role: OrgRole
}

export interface OrgInfo {
  organization_id: string
  name: string
  status: string
  member_count: number
}

export interface DpaStatus {
  organization_id: string
  signed: boolean
}

export interface DpaSignPayload {
  signer_name?: string
  signer_email?: string
  version?: string
}

export interface DpaSignResult {
  dpa_id: string
  signed: boolean
}

export interface ActivationStatus {
  organization_id: string
  dpa_signed: boolean
  has_active_license: boolean
  active: boolean
}

export interface ActiveLicense {
  license_id: string
  status: string
  seat_count: number
  plan_code: string
  plan_name: string
  seat_limit: number | null
  features: Record<string, unknown>
}

export interface SeatUsage {
  used: number
  limit: number | null
  over_limit: boolean
}

export interface LicenseInfo {
  organization_id: string
  license: ActiveLicense | null
  seat_usage: SeatUsage
}

class OrganizationService {
  private baseURL = '/api/v1/org';

  async getInfo(): Promise<OrgInfo> {
    const { data } = await apiClient.get<OrgInfo>(`${this.baseURL}/info`);
    return data;
  }

  async getMembers(): Promise<OrgMember[]> {
    const { data } = await apiClient.get<OrgMember[]>(`${this.baseURL}/members`);
    return data;
  }

  async addMember(email: string, orgRole: OrgRole): Promise<OrgMember> {
    const { data } = await apiClient.post<OrgMember>(`${this.baseURL}/members`, {
      email,
      org_role: orgRole,
    });
    return data;
  }

  async updateMember(
    userId: string,
    updates: { org_role?: OrgRole; is_active?: boolean },
  ): Promise<OrgMember> {
    const { data } = await apiClient.patch<OrgMember>(
      `${this.baseURL}/members/${userId}`,
      updates,
    );
    return data;
  }

  async removeMember(userId: string): Promise<void> {
    await apiClient.delete(`${this.baseURL}/members/${userId}`);
  }

  async getActivation(): Promise<ActivationStatus> {
    const { data } = await apiClient.get<ActivationStatus>(`${this.baseURL}/billing/activation`);
    return data;
  }

  async getLicense(): Promise<LicenseInfo> {
    const { data } = await apiClient.get<LicenseInfo>(`${this.baseURL}/billing/license`);
    return data;
  }

  async getDpa(): Promise<DpaStatus> {
    const { data } = await apiClient.get<DpaStatus>(`${this.baseURL}/billing/dpa`);
    return data;
  }

  async signDpa(payload: DpaSignPayload = {}): Promise<DpaSignResult> {
    const { data } = await apiClient.post<DpaSignResult>(`${this.baseURL}/billing/dpa/sign`, payload);
    return data;
  }
}

export const organizationService = new OrganizationService();
export default organizationService;
