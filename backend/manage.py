#!/usr/bin/env python
import os
import sys


def main() -> None:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "无法导入 Django。请先安装 requirements.txt 中的依赖。"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
