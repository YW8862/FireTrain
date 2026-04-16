import { beforeEach, describe, expect, it, vi } from 'vitest'

const { requestMock } = vi.hoisted(() => ({
  requestMock: vi.fn()
}))

vi.mock('../src/api/request', () => ({
  default: requestMock
}))

import {
  createUser,
  getAdminDetail,
  getUserStatistics,
  getUserTrainings,
  updateAdmin,
  updateUser
} from '../src/api/admin'

describe('admin api', () => {
  beforeEach(() => {
    requestMock.mockClear()
  })

  it('builds user detail statistics and trainings requests', () => {
    getUserStatistics(12, { days: 15 })
    getUserTrainings(12, { page: 2, page_size: 20 })

    expect(requestMock).toHaveBeenNthCalledWith(1, {
      url: '/admin/users/12/stats/overview',
      method: 'get',
      params: { days: 15 }
    })
    expect(requestMock).toHaveBeenNthCalledWith(2, {
      url: '/admin/users/12/trainings',
      method: 'get',
      params: { page: 2, page_size: 20 }
    })
  })

  it('builds create and update payloads for users and admins', () => {
    createUser({ username: 'u1' })
    updateUser(3, { username: 'u2' })
    getAdminDetail(8)
    updateAdmin(8, { username: 'admin2' })

    expect(requestMock).toHaveBeenNthCalledWith(1, {
      url: '/admin/users',
      method: 'post',
      data: { username: 'u1' }
    })
    expect(requestMock).toHaveBeenNthCalledWith(2, {
      url: '/admin/users/3',
      method: 'put',
      data: { username: 'u2' }
    })
    expect(requestMock).toHaveBeenNthCalledWith(3, {
      url: '/admin/admins/8',
      method: 'get'
    })
    expect(requestMock).toHaveBeenNthCalledWith(4, {
      url: '/admin/admins/8',
      method: 'put',
      data: { username: 'admin2' }
    })
  })
})
