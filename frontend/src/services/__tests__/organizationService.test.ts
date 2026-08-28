/**
 * OrganizationService Tests
 * B2B okul onboarding — org üye/lisans/DPA API sözleşmesi
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'

const mockGet = vi.fn()
const mockPost = vi.fn()
const mockPatch = vi.fn()
const mockDelete = vi.fn()

vi.mock('../apiClient', () => ({
  default: {
    get: (...args: unknown[]) => mockGet(...args),
    post: (...args: unknown[]) => mockPost(...args),
    patch: (...args: unknown[]) => mockPatch(...args),
    delete: (...args: unknown[]) => mockDelete(...args),
  },
}))

const { organizationService } = await import('../organizationService')

describe('OrganizationService', () => {
  beforeEach(() => {
    mockGet.mockReset()
    mockPost.mockReset()
    mockPatch.mockReset()
    mockDelete.mockReset()
  })

  it('getInfo fetches /api/v1/org/info', async () => {
    const info = { organization_id: 'org-1', name: 'Test Okul', status: 'active', member_count: 5 }
    mockGet.mockResolvedValueOnce({ data: info })

    const result = await organizationService.getInfo()

    expect(mockGet).toHaveBeenCalledWith('/api/v1/org/info')
    expect(result).toEqual(info)
  })

  it('getMembers fetches /api/v1/org/members', async () => {
    const members = [{ user_id: 'u1', email: 'a@b.com', org_role: 'STUDENT' }]
    mockGet.mockResolvedValueOnce({ data: members })

    const result = await organizationService.getMembers()

    expect(mockGet).toHaveBeenCalledWith('/api/v1/org/members')
    expect(result).toEqual(members)
  })

  it('addMember posts email + org_role', async () => {
    const created = { user_id: 'u2', email: 'c@d.com', org_role: 'TEACHER' }
    mockPost.mockResolvedValueOnce({ data: created })

    const result = await organizationService.addMember('c@d.com', 'TEACHER')

    expect(mockPost).toHaveBeenCalledWith('/api/v1/org/members', {
      email: 'c@d.com',
      org_role: 'TEACHER',
    })
    expect(result).toEqual(created)
  })

  it('addMember propagates 409 conflict errors from apiClient', async () => {
    mockPost.mockRejectedValueOnce(new Error('kullanıcı zaten bu kurumun üyesi'))

    await expect(organizationService.addMember('dup@d.com', 'STUDENT')).rejects.toThrow(
      'kullanıcı zaten bu kurumun üyesi',
    )
  })

  it('updateMember patches /members/{userId} with partial updates', async () => {
    const updated = { user_id: 'u1', email: null, org_role: 'TEACHER' }
    mockPatch.mockResolvedValueOnce({ data: updated })

    const result = await organizationService.updateMember('u1', { org_role: 'TEACHER' })

    expect(mockPatch).toHaveBeenCalledWith('/api/v1/org/members/u1', { org_role: 'TEACHER' })
    expect(result).toEqual(updated)
  })

  it('removeMember deletes /members/{userId}', async () => {
    mockDelete.mockResolvedValueOnce({ data: undefined })

    await organizationService.removeMember('u1')

    expect(mockDelete).toHaveBeenCalledWith('/api/v1/org/members/u1')
  })

  it('getDpa fetches DPA status', async () => {
    const dpa = { organization_id: 'org-1', signed: false }
    mockGet.mockResolvedValueOnce({ data: dpa })

    const result = await organizationService.getDpa()

    expect(mockGet).toHaveBeenCalledWith('/api/v1/org/billing/dpa')
    expect(result).toEqual(dpa)
  })

  it('signDpa posts signer payload', async () => {
    const signed = { dpa_id: 'dpa-1', signed: true }
    mockPost.mockResolvedValueOnce({ data: signed })

    const result = await organizationService.signDpa({ signer_name: 'Ali', signer_email: 'ali@okul.com' })

    expect(mockPost).toHaveBeenCalledWith('/api/v1/org/billing/dpa/sign', {
      signer_name: 'Ali',
      signer_email: 'ali@okul.com',
    })
    expect(result).toEqual(signed)
  })

  it('getLicense fetches seat usage + license', async () => {
    const license = {
      organization_id: 'org-1',
      license: null,
      seat_usage: { used: 3, limit: 10, over_limit: false },
    }
    mockGet.mockResolvedValueOnce({ data: license })

    const result = await organizationService.getLicense()

    expect(mockGet).toHaveBeenCalledWith('/api/v1/org/billing/license')
    expect(result).toEqual(license)
  })
})
