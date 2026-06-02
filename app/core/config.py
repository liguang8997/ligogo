from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # 应用
    APP_NAME: str = "TeacherManagementSystem"
    APP_ENV: str = "development"
    APP_DEBUG: bool = True
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000

    # MySQL
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = ""
    MYSQL_DATABASE: str = "teacher_system"

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""
    REDIS_DB: int = 0

    # Milvus
    MILVUS_HOST: str = "localhost"
    MILVUS_PORT: int = 19530
    MILVUS_COLLECTION: str = "teacher_knowledge"

    # DeepSeek API
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com/anthropic"
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_PRO_MODEL: str = "deepseek-v4-pro"
    DEEPSEEK_FLASH_MODEL: str = "deepseek-v4-flash"

    # Embedding API (DashScope)
    EMBEDDING_BASE_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    EMBEDDING_API_KEY: str = ""
    EMBEDDING_MODEL: str = "text-embedding-v3"

    # JWT
    JWT_SECRET_KEY: str = ""
    JWT_REFRESH_SECRET_KEY: str = ""
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # AES
    AES_ENCRYPTION_KEY: str = ""

    # 文件上传
    UPLOAD_DIR: str = "./uploads"
    MAX_AVATAR_SIZE: int = 2097152
    MAX_ATTACHMENT_SIZE: int = 10485760
    ALLOWED_IMAGE_TYPES: str = "jpg,jpeg,png,gif"
    ALLOWED_DOC_TYPES: str = "pdf,doc,docx,xls,xlsx"

    # 考勤规则
    CHECK_IN_START: str = "08:00"
    CHECK_IN_END: str = "09:00"
    CHECK_OUT_START: str = "17:00"
    CHECK_OUT_END: str = "18:00"

    # Agent
    AGENT_SESSION_TTL: int = 86400
    AGENT_MAX_HISTORY: int = 20

    @property
    def mysql_url(self) -> str:
        return (
            f"mysql+aiomysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}"
            f"@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"
        )

    @property
    def redis_url(self) -> str:
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    @property
    def allowed_image_extensions(self) -> list[str]:
        return [ext.strip() for ext in self.ALLOWED_IMAGE_TYPES.split(",")]

    @property
    def allowed_doc_extensions(self) -> list[str]:
        return [ext.strip() for ext in self.ALLOWED_DOC_TYPES.split(",")]

    @property
    def allowed_extensions(self) -> list[str]:
        return self.allowed_image_extensions + self.allowed_doc_extensions

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
