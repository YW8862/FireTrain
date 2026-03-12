import request from './request'

/**
 * 开始训练
 */
export function startTraining(data) {
  return request({
    url: '/training/start',
    method: 'post',
    data
  })
}

/**
 * 上传训练视频
 */
export function uploadVideo(trainingId, videoPath) {
  return request({
    url: '/training/upload',
    method: 'post',
    data: {
      training_id: trainingId,
      video_path: videoPath
    }
  })
}

/**
 * 完成训练并获取评分
 */
export function completeTraining(trainingId) {
  return request({
    url: `/training/complete/${trainingId}`,
    method: 'post'
  })
}

/**
 * 获取训练详情
 */
export function getTrainingDetail(trainingId) {
  return request({
    url: `/training/${trainingId}`,
    method: 'get'
  })
}

/**
 * 获取训练历史
 */
export function getTrainingHistory(params) {
  return request({
    url: '/training/history',
    method: 'get',
    params
  })
}
