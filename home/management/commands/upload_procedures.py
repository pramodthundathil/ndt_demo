import os
import json
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from home.models import InspectionProcedure


class Command(BaseCommand):
    help = "Upload or export test procedure data into/from the active database."

    def add_arguments(self, parser):
        default_fixture = Path(__file__).resolve().parent.parent.parent / "fixtures" / "test_procedures_data.json"
        parser.add_argument(
            "--file", "-f",
            default=str(default_fixture),
            help="Path to JSON file for importing procedure data (default: home/fixtures/test_procedures_data.json)."
        )
        parser.add_argument(
            "--export", "-e",
            nargs="?",
            const=str(default_fixture),
            metavar="OUTPUT_FILE",
            help="Export live procedure data from database into a JSON file."
        )

    def handle(self, *args, **options):
        export_file = options.get("export")
        if export_file:
            self.export_procedures(export_file)
        else:
            file_path = options.get("file")
            self.upload_procedures(file_path)

    def upload_procedures(self, file_path):
        if not os.path.exists(file_path):
            raise CommandError(f"Fixture file '{file_path}' does not exist.")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                procedures = json.load(f)
        except Exception as err:
            raise CommandError(f"Failed to parse JSON file '{file_path}': {err}")

        if not isinstance(procedures, list):
            raise CommandError("JSON file must contain a list/array of procedure objects.")

        self.stdout.write(self.style.NOTICE(f"Uploading test procedures from: {file_path}"))
        created_count = 0
        updated_count = 0

        for idx, item in enumerate(procedures, start=1):
            title = item.get("title", "").strip()
            standard_code = item.get("standard_code", "").strip()
            description = item.get("description", "").strip()
            default_statement = item.get("default_statement", "").strip()

            if not standard_code or not title:
                self.stdout.write(self.style.WARNING(f"  [{idx}] Skipped entry missing title or standard_code: {item}"))
                continue

            procedure, created = InspectionProcedure.objects.update_or_create(
                standard_code=standard_code,
                defaults={
                    "title": title,
                    "description": description,
                    "default_statement": default_statement,
                }
            )

            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"  [{idx}] Created: '{procedure.title}' ({procedure.standard_code})"))
            else:
                updated_count += 1
                self.stdout.write(self.style.SUCCESS(f"  [{idx}] Updated: '{procedure.title}' ({procedure.standard_code})"))

        self.stdout.write(self.style.SUCCESS(
            f"\nUpload complete! Total: {len(procedures)} | Created: {created_count} | Updated: {updated_count} | Total DB: {InspectionProcedure.objects.count()}"
        ))

    def export_procedures(self, output_path):
        procedures = InspectionProcedure.objects.all().order_by("id")
        data = [
            {
                "title": p.title,
                "standard_code": p.standard_code,
                "description": p.description,
                "default_statement": p.default_statement,
            }
            for p in procedures
        ]

        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        self.stdout.write(self.style.SUCCESS(f"Exported {len(data)} test procedures to: {output_path}"))
