from django.core.management.base import BaseCommand

from apps.core.demo_roster import ensure_demo_roster


class Command(BaseCommand):
    help = "创建或更新只包含虚拟数据的 Pilot UI 演示学校。"

    def handle(self, *args, **options):
        data = ensure_demo_roster()
        self.stdout.write(
            self.style.SUCCESS(
                f"Demo ready: {data['school'].code} / {data['cycle'].name} / roster={len(data['reports'])} / report={data['report'].pk}"
            )
        )
