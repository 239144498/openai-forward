import atexit
import datetime
import os
import pickle
import platform
import signal
import subprocess
from pathlib import Path

import fire
import uvicorn
import yaml


def save_yaml(path: Path, data: dict):
    with open(path, 'w') as f:
        yaml.dump(data, f)


class Cli:
    def run(self, port=8000, workers=1, start_ui=True, ui_port=8001):
        """
        Runs the application using the Uvicorn server.

        Args:
            port (int): The port number on which to run the server.
            workers (int): The number of worker processes to run.
            start_ui (bool): Whether to start the web UI.
            ui_port (int): The port number on which to run streamlit.

        Returns:
            None
        """

        if platform.system() == "Windows":
            os.environ["TZ"] = ""

        ssl_keyfile = os.environ.get("ssl_keyfile", None) or None
        ssl_certfile = os.environ.get("ssl_certfile", None) or None

        uvicorn.run(
            app="openai_forward.app:app",
            host="0.0.0.0",
            port=port,
            workers=workers,
            app_dir="..",
            ssl_keyfile=ssl_keyfile,
            ssl_certfile=ssl_certfile,
        )

    def _start_uvicorn(self, port, workers, ssl_keyfile=None, ssl_certfile=None):
        from openai_forward.helper import wait_for_serve_start

        self.uvicorn_proc = subprocess.Popen(
            [
                'uvicorn',
                'openai_forward.app:app',
                '--host',
                '0.0.0.0',
                '--port',
                str(port),
                '--app-dir',
                '..',
                '--workers',
                str(workers),
            ]
            + (['--ssl-keyfile', ssl_keyfile] if ssl_keyfile else [])
            + (['--ssl-certfile', ssl_certfile] if ssl_certfile else [])
        )
        suppress_exception = platform.system() == "Windows"
        wait_for_serve_start(
            f"http://localhost:{port}/healthz",
            timeout=10,
            suppress_exception=suppress_exception,
        )

    def _restart_uvicorn(self, **kwargs):
        self._stop_uvicorn()
        self._start_uvicorn(**kwargs)

    def _stop_streamlit(self):
        self._stop(uvicorn=False)

    def _stop_uvicorn(self):
        self._stop(streamlit=False)

    def _stop(self, uvicorn=True, streamlit=True):
        if uvicorn and self.uvicorn_proc.poll() is None:
            self.uvicorn_proc.send_signal(signal.SIGINT)
            try:
                self.uvicorn_proc.wait(timeout=15)
            except subprocess.TimeoutExpired:
                self.uvicorn_proc.kill()
        if streamlit and self.streamlit_proc.poll() is None:
            self.streamlit_proc.send_signal(signal.SIGINT)
            try:
                self.streamlit_proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.streamlit_proc.kill()

    @staticmethod
    def convert(log_folder: str = None, target_path: str = None):
        """
        Converts log files in a folder to a JSONL file.

        Args:
            log_folder (str, optional): The path to the folder containing the log files. Default is None.
            target_path (str, optional): The path to the target JSONL file. Default is None.

        Returns:
            None
        """
        from openai_forward.config.settings import OPENAI_ROUTE_PREFIX
        from openai_forward.helper import convert_folder_to_jsonl, route_prefix_to_str

        print(60 * '-')
        if log_folder is None:
            if target_path is not None:
                raise ValueError("target_path must be None when log_folder is None")
            _prefix_list = [route_prefix_to_str(i) for i in OPENAI_ROUTE_PREFIX]
            for prefix in _prefix_list:
                log_folder = f"./Log/{prefix}/chat"
                target_path = f"./Log/chat_{prefix}.json"
                print(f"Convert {log_folder}/*.log to {target_path}")
                convert_folder_to_jsonl(log_folder, target_path)
                print(60 * '-')
        else:
            print(f"Convert {log_folder}/*.log to {target_path}")
            convert_folder_to_jsonl(log_folder, target_path)
            print(60 * '-')

    @staticmethod
    def gen_config(dir: str = "."):
        """
        Generates a .env file in the specified directory.
        """
        from pathlib import Path

        from openai_forward.config.interface import Config

        config = Config()
        env_dict = config.convert_to_env(set_env=False)
        dir = Path(dir)

        with open(dir / ".env", "w") as f:
            env_content = "\n".join(
                [f"{key}={value}" for key, value in env_dict.items()]
            )
            f.write(env_content)


def main():
    fire.Fire(Cli)


if __name__ == "__main__":
    main()
