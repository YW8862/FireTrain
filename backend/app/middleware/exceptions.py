"""统一异常处理"""
import logging
from typing import Union

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)


async def validation_exception_handler(
    request: Request, 
    exc: RequestValidationError
) -> JSONResponse:
    """
    请求参数验证异常处理器
    
    当 Pydantic Schema 验证失败时调用
    """
    logger.warning(f"请求参数验证失败：{exc.errors()}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "参数验证失败",
            "detail": exc.errors(),
            "body": exc.body
        },
    )


async def sqlalchemy_exception_handler(
    request: Request,
    exc: SQLAlchemyError
) -> JSONResponse:
    """
    数据库异常处理器
    
    当 SQLAlchemy 操作失败时调用
    """
    logger.error(f"数据库错误：{str(exc)}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "数据库错误",
            "detail": "数据操作失败，请稍后重试"
        },
    )


async def value_error_handler(
    request: Request,
    exc: ValueError
) -> JSONResponse:
    """
    ValueError 异常处理器
    
    用于处理业务逻辑中的值错误
    """
    logger.warning(f"值错误：{str(exc)}")
    
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": "请求数据错误",
            "detail": str(exc)
        },
    )


async def generic_exception_handler(
    request: Request,
    exc: Exception
) -> JSONResponse:
    """
    通用异常处理器
    
    捕获所有未处理的异常，返回友好的错误信息
    """
    logger.error(f"未处理的异常：{str(exc)}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "服务器内部错误",
            "detail": "请求处理失败，请稍后重试"
        },
    )


def setup_exception_handlers(app: FastAPI):
    """
    为应用添加异常处理器
    
    Args:
        app: FastAPI 应用实例
    """
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
    app.add_exception_handler(ValueError, value_error_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
