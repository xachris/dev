from django.core.management.base import BaseCommand

from apps.core.demo_data import ensure_demo_data


class Command(BaseCommand):
    help = "创建或更新只包含虚拟数据的 Pilot UI 演示学校。"

    def handle(self, *args, **options):
        data = ensure_demo_data()
        self.stdout.write(
            self.style.SUCCESS(
                f"Demo ready: {data['school'].code} / {data['cycle'].name} / report={data['report'].pk}"
            )
        )
