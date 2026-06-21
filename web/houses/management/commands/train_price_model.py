from django.core.management.base import BaseCommand

from houses.services.prediction import train_price_model


class Command(BaseCommand):
    help = "Train the house price prediction model."

    def handle(self, *args, **options):
        result = train_price_model()
        if result.get("trained"):
            self.stdout.write(self.style.SUCCESS(f"训练完成: {result}"))
            return

        self.stdout.write(
            self.style.WARNING(
                f"训练跳过: {result.get('reason', '未知原因')}"
            )
        )
