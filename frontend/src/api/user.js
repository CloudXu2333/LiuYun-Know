/**
 * 用户管理相关 API
 */
import axios from './axios'

/**
 * 获取个人信息
 */
export const getMyProfile = () => {
  return axios.get('/users/me')
}

/**
 * 更新个人信息
 */
export const updateMyProfile = (data) => {
  return axios.put('/users/me', data)
}

/**
 * 修改密码
 */
export const changePassword = (data) => {
  return axios.put('/users/password', data)
}

