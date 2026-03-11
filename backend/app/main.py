from fastapi import FastAPI


app = FastAPI(
    title="FireTrain Backend",
    description="智能消防技能训练评测系统单体后端",
    version="0.1.0",
)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
