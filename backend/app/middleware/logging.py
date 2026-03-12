"""请求日志中间件"""
import logging
import time
import uuid
from typing import Callable

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

# 配置日志
logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    请求日志中间件
    
    功能：
    - 为每个请求生成唯一的 trace_id
    - 记录请求方法、路径、耗时
    - 记录响应状态码
    - 支持记录请求体（可选，生产环境建议关闭）
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 生成 trace_id
        trace_id = str(uuid.uuid4())
        
        # 将 trace_id 添加到请求头中，方便后续追踪
        request.state.trace_id = trace_id
        
        # 记录请求开始时间
        start_time = time.time()
        
        # 获取请求信息
        method = request.method
        url = str(request.url)
        client_host = request.client.host if request.client else "unknown"
        
        # 记录请求日志
        logger.info(
            f"[{trace_id}] 请求开始 | {method} {url} | 客户端：{client_host}"
        )
        
        try:
            # 处理请求
            response = await call_next(request)
            
            # 计算耗时
            process_time = time.time() - start_time
            
            # 在响应头中添加 trace_id
            response.headers["X-Trace-ID"] = trace_id
            
            # 记录响应日志
            logger.info(
                f"[{trace_id}] 请求完成 | {method} {url} | "
                f"状态码：{response.status_code} | 耗时：{process_time:.3f}s"
            )
            
            return response
            
        except Exception as e:
            # 计算耗时
            process_time = time.time() - start_time
            
            # 记录异常日志
            logger.error(
                f"[{trace_id}] 请求异常 | {method} {url} | "
                f"耗时：{process_time:.3f}s | 错误：{str(e)}",
                exc_info=True
            )
            
            # 重新抛出异常
            raise


def setup_request_logging(app: FastAPI):
    """
    为应用添加请求日志中间件
    
    Args:
        app: FastAPI 应用实例
    """
    app.add_middleware(RequestLoggingMiddleware)
