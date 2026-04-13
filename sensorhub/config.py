from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    minio_access_key: str
    minio_secret_key: str
    minio_port: int
    minio_ip: str
    minio_bucket: str

    mongo_username: str
    mongo_root_password: str
    mongo_port: int
    mongo_ip: str
    mongo_db: str

    api_port: int

    rabbitmq_url: str = "amqp://guest:guest@localhost:5672/"
