import json
from typing import Literal

from attrs import asdict, define, field

from openai_forward.config.settings import *


class Base:
    def to_dict(self, drop_none=True):
        if drop_none:

            def custom_filter(attribute, value):
                if drop_none:
                    return value is not None
                return True

            return asdict(self, filter=custom_filter)
        return asdict(self)

    def to_dict_str(self):
        return {k: str(v) for k, v in self.to_dict(drop_none=True).items()}


@define(slots=True)
class ForwardItem(Base):
    base_url: str
    route: str
    type: Literal["openai", "general"] = field(default="general")


@define(slots=True)
class Forward(Base):
    forward: List[ForwardItem] = [
        ForwardItem(base_url="https://api.openai.com", route="/", type="openai"),
        ForwardItem(
            base_url="https://generativelanguage.googleapis.com",
            route="/gemini",
            type="general",
        ),
    ]

    def convert_to_env(self, set_env=False):
        env_dict = {'FORWARD_CONFIG': json.dumps([i.to_dict() for i in self.forward])}

        if set_env:
            os.environ.update(env_dict)
        return env_dict


@define(slots=True)
class CacheConfig(Base):
    backend: str = 'LevelDB'
    root_path_or_url: str = './FLAXKV_DB'
    default_request_caching_value: bool = True
    openai: bool = False
    general: bool = False
    routes: List = ['/v1/chat/completions']

    def convert_to_env(self, set_env=False):
        env_dict = {}

        env_dict['CACHE_OPENAI'] = str(self.openai)
        env_dict['CACHE_GENERAL'] = str(self.general)

        env_dict['CACHE_BACKEND'] = self.backend
        env_dict['CACHE_ROOT_PATH_OR_URL'] = self.root_path_or_url
        env_dict['DEFAULT_REQUEST_CACHING_VALUE'] = str(
            self.default_request_caching_value
        )
        env_dict['CACHE_ROUTES'] = json.dumps(self.routes)

        if set_env:
            os.environ.update(env_dict)
        return env_dict


@define(slots=True)
class RateLimitType(Base):
    route: str
    value: List[Dict[str, str]]


@define(slots=True)
class RateLimit(Base):
    backend: str = ''
    global_rate_limit: str = 'inf'
    token_rate_limit: List[RateLimitType] = [
        RateLimitType(
            route="/v1/chat/completions",
            value=[{"level": 0, "limit": "60/second"}],
        ),
        RateLimitType(
            route="/v1/completions", value=[{"level": 0, "limit": "60/second"}]
        ),
    ]
    req_rate_limit: List[RateLimitType] = [
        RateLimitType(
            route="/v1/chat/completions",
            value=[{"level": 0, "limit": "100/2minutes"}],
        ),
        RateLimitType(
            route="/v1/completions", value=[{"level": 0, "limit": "60/minute"}]
        ),
        RateLimitType(
            route="/v1/embeddings", value=[{"level": 0, "limit": "100/2minutes"}]
        ),
    ]
    iter_chunk: Literal['one-by-one', 'efficiency'] = 'one-by-one'
    strategy: Literal[
        'fixed_window', 'moving-window', 'fixed-window-elastic-expiry'
    ] = 'moving-window'

    def convert_to_env(self, set_env=False):
        env_dict = {}
        env_dict['GLOBAL_RATE_LIMIT'] = self.global_rate_limit
        env_dict['RATE_LIMIT_STRATEGY'] = self.strategy
        env_dict['TOKEN_RATE_LIMIT'] = json.dumps(
            {i.route: i.value for i in self.token_rate_limit if i.route and i.value}
        )
        env_dict['REQ_RATE_LIMIT'] = json.dumps(
            {i.route: i.value for i in self.req_rate_limit if i.route and i.value}
        )
        env_dict['ITER_CHUNK_TYPE'] = self.iter_chunk
        if set_env:
            os.environ.update(env_dict)
        return env_dict


@define(slots=True)
class ApiKey(Base):
    openai_key: Dict = {"sk-xx1": [0]}
    forward_key: Dict = {0: ["fk-1"]}
    level: Dict = {1: ["gpt-3.5-turbo"]}

    def convert_to_env(self, set_env=False):
        env_dict = {}
        openai_key_dict = {}
        for key, value in self.openai_key.items():
            value: str
            values = value.strip().replace('，', ',').split(',')
            openai_key_dict[key] = [int(i) for i in values]
        env_dict['OPENAI_API_KEY_CONFIG'] = json.dumps(openai_key_dict)
        env_dict['FORWARD_KEY_CONFIG'] = json.dumps(self.forward_key)
        env_dict['LEVEL_MODELS'] = json.dumps(self.level)
        if set_env:
            os.environ.update(env_dict)
        return env_dict


@define(slots=True)
class Log(Base):
    general: bool = True
    openai: bool = True

    def convert_to_env(self, set_env=False):
        env_dict = {}
        env_dict['LOG_GENERAL'] = str(self.general)
        env_dict['LOG_OPENAI'] = str(self.openai)
        if set_env:
            os.environ.update(env_dict)
        return env_dict


@define(slots=True)
class Config(Base):
    # forward: Forward = Forward()
    forward: List[ForwardItem] = [
        ForwardItem(base_url="https://api.openai.com", route="/", type="openai"),
        ForwardItem(
            base_url="https://generativelanguage.googleapis.com",
            route="/gemini",
            type="general",
        ),
    ]

    api_key: ApiKey = ApiKey()

    cache: CacheConfig = CacheConfig()

    rate_limit: RateLimit = RateLimit()

    log: Log = Log()

    timezone: str = 'Asia/Shanghai'
    timeout: int = 6
    benchmark_mode: bool = False
    proxy: str = ''
    default_stream_response: bool = True

    def convert_to_env(self, set_env=False):
        # env_dict = {}
        # env_dict.update(self.forward.convert_to_env())
        env_dict = {'FORWARD_CONFIG': json.dumps([i.to_dict() for i in self.forward])}
        env_dict.update(self.api_key.convert_to_env())
        env_dict.update(self.cache.convert_to_env())
        env_dict.update(self.rate_limit.convert_to_env())
        env_dict.update(self.log.convert_to_env())

        env_dict['TZ'] = self.timezone
        env_dict['TIMEOUT'] = str(self.timeout)
        env_dict['BENCHMARK_MODE'] = str(self.benchmark_mode)
        env_dict['DEFAULT_STREAM_RESPONSE'] = str(self.default_stream_response)

        if self.proxy:
            env_dict['PROXY'] = self.proxy

        if set_env:
            os.environ.update(env_dict)
        return env_dict

    def come_from_env(self):

        self.timeout = TIMEOUT
        self.timezone = os.environ.get('TZ', 'Asia/Shanghai')
        self.benchmark_mode = BENCHMARK_MODE
        self.proxy = PROXY or ""
        self.log.openai = LOG_OPENAI
        self.log.general = LOG_GENERAL

        self.rate_limit.strategy = RATE_LIMIT_STRATEGY
        self.rate_limit.global_rate_limit = GLOBAL_RATE_LIMIT
        self.rate_limit.iter_chunk = ITER_CHUNK_TYPE
        self.rate_limit.backend = RATE_LIMIT_BACKEND or self.rate_limit.backend
        self.rate_limit.req_rate_limit = [
            RateLimitType(key, value) for key, value in req_rate_limit_dict.items()
        ] or self.rate_limit.req_rate_limit
        self.rate_limit.token_rate_limit = [
            RateLimitType(key, value) for key, value in token_rate_limit_conf.items()
        ] or self.rate_limit.token_rate_limit

        self.cache.backend = CACHE_BACKEND
        self.cache.root_path_or_url = CACHE_ROOT_PATH_OR_URL
        self.cache.default_request_caching_value = DEFAULT_REQUEST_CACHING_VALUE
        self.cache.openai = CACHE_OPENAI or self.cache.openai
        self.cache.general = CACHE_GENERAL or self.cache.general
        self.cache.routes = list(CACHE_ROUTE_SET) or self.cache.routes
        self.api_key.level = LEVEL_MODELS or self.api_key.level
        self.api_key.openai_key = OPENAI_API_KEY or self.api_key.openai_key
        self.api_key.forward_key = LEVEL_TO_FWD_KEY or self.api_key.forward_key
        self.forward = [ForwardItem(**i) for i in FORWARD_CONFIG]

        return self


if __name__ == "__main__":
    import yaml

    def save_dict_to_yaml(data, file_path):
        with open(file_path, 'w') as file:
            yaml.dump(data, file, default_flow_style=False)

    config = Config()
    print(config.to_dict())
    save_dict_to_yaml(config.to_dict(), 'config.yaml')
