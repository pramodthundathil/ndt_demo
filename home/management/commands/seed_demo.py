import os
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from PIL import Image, ImageDraw
import io
from home.models import UserProfile, InspectionProcedure, NDTReport

class Command(BaseCommand):
    help = "Seed demo accounts, test procedures, and initial MTQ Gangway Inspection certificate matching the sample image."

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Seeding demo data for NDT Marine Inspection Portal..."))

        # 1. Create Admin User
        admin_user, created_admin = User.objects.get_or_create(
            username="admin",
            defaults={
                "email": "admin@mtq-products.com",
                "first_name": "Admin",
                "last_name": "Supervisor",
                "is_staff": True,
                "is_superuser": True,
            }
        )
        if created_admin:
            admin_user.set_password("admin123")
            admin_user.save()
            self.stdout.write(self.style.SUCCESS("Created Admin user: admin / admin123"))

        admin_profile, _ = UserProfile.objects.get_or_create(user=admin_user)
        admin_profile.role = "ADMIN"
        admin_profile.qualification = "Senior Marine NDT Supervisor / Level III"
        admin_profile.company_name = "MTQ Products B.V."
        admin_profile.save()

        # 2. Create Tester User
        tester_user, created_tester = User.objects.get_or_create(
            username="tester",
            defaults={
                "email": "inspector@mtq-products.com",
                "first_name": "John",
                "last_name": "Inspector",
            }
        )
        if created_tester:
            tester_user.set_password("tester123")
            tester_user.save()
            self.stdout.write(self.style.SUCCESS("Created Inspector user: tester / tester123"))

        tester_profile, _ = UserProfile.objects.get_or_create(user=tester_user)
        tester_profile.role = "INSPECTOR"
        tester_profile.qualification = "ISO 9712 NDT Inspector Level II (Visual & UTM)"
        tester_profile.certification_no = "ISO-9712-NL-8839"
        tester_profile.company_name = "MTQ Products B.V."

        # Generate a sample signature image for tester profile
        sig_img = Image.new('RGBA', (300, 100), (255, 255, 255, 0))
        draw = ImageDraw.Draw(sig_img)
        # Draw realistic signature lines
        draw.arc([20, 20, 120, 80], 40, 300, fill=(15, 43, 92, 255), width=3)
        draw.line([(30, 60), (90, 30), (140, 70), (200, 40), (260, 50)], fill=(15, 43, 92, 255), width=3)
        draw.line([(80, 55), (240, 55)], fill=(15, 43, 92, 255), width=2)

        buffer = io.BytesIO()
        sig_img.save(buffer, format='PNG')
        tester_profile.profile_signature.save('tester_sig_default.png', ContentFile(buffer.getvalue()), save=False)
        tester_profile.save()

        # 3. Create NDT Inspection Procedures
        proc_gangway, _ = InspectionProcedure.objects.get_or_create(
            standard_code="EN 526:2016",
            defaults={
                "title": "Gangway Visual Inspection Certificate",
                "description": "Visual inspection & structural integrity verification of ship gangways and boarding platforms in conformity with EN 526:2016.",
                "default_statement": "This Gangway / Platform has been visually inspected in conformity with NEN-EN 526 and approved for use for the period of one year."
            }
        )

        proc_loadtest, _ = InspectionProcedure.objects.get_or_create(
            standard_code="26-C095 / ISO7061-A",
            defaults={
                "title": "Load Test Report 26-C095 / ISO7061-A",
                "description": "Proof load testing and structural deflection assessment for aluminum shore gangways & marine lifting equipment.",
                "default_statement": "Proof load test conducted in accordance with ISO 7061-A & 26-C095 guidelines. Maximum test load applied without permanent deformation."
            }
        )

        proc_mpi, _ = InspectionProcedure.objects.get_or_create(
            standard_code="ISO 17638:2016",
            defaults={
                "title": "Magnetic Report",
                "description": "Surface and near-surface flaw detection in ferromagnetic welds and ship structures using AC Yoke.",
                "default_statement": "Magnetic particle testing performed on critical structural welds. No surface breaking linear discontinuities or cracks detected."
            }
        )

        proc_rec, _ = InspectionProcedure.objects.get_or_create(
            standard_code="NDT-REC-2026",
            defaults={
                "title": "Recommendation report",
                "description": "Technical recommendation and corrective action evaluation report for marine equipment and structural components.",
                "default_statement": "Comprehensive technical evaluation completed. Equipment recommended for continued service subject to routine inspection."
            }
        )

        proc_utm, _ = InspectionProcedure.objects.get_or_create(
            standard_code="ISO 16809 / IACS DCN",
            defaults={
                "title": "UTM Survey – Draft – Overboard pipes",
                "description": "Ultrasonic thickness measurement survey of overboard discharge pipes, sea chests, and draft line hull plating.",
                "default_statement": "Ultrasonic thickness survey performed on overboard discharge piping and draft line hull plating. Pipe wall thickness meets class minimum safety requirements."
            }
        )

        proc_weld, _ = InspectionProcedure.objects.get_or_create(
            standard_code="ISO 5817:2014",
            defaults={
                "title": "Visual & Weld Inspection Certificate",
                "description": "General visual surface examination of structural steel welds, joint alignment, and defect evaluation.",
                "default_statement": "Visual weld examination performed according to ISO 5817 Quality Level B. All inspected welds satisfy acceptance criteria."
            }
        )

        # 4. Create Initial Certificate matching the uploaded image exactly!
        today = date.today()
        validity_until = today + timedelta(days=365)

        report, created_report = NDTReport.objects.get_or_create(
            report_number="MTQ-PR017Rev00",
            defaults={
                "procedure": proc_gangway,
                "inspector": tester_user,
                "vessel_name": "MV Atlantic Pioneer",
                "project_no": "MTQ-2026-9402",
                "make_manufacturer": "MTQ Products B.V.",
                "year_manufactured": "2023",
                "size_length": "12.5 meters",
                "marking_tag": "GW-8849-B",
                "inspection_date": today,
                "validity_until": validity_until,
                "status": "APPROVED",
                "approval_statement": "This Gangway / Platform has been visually inspected in conformity with NEN-EN 526 and approved for use for the period of one year.",
                "notes": "Annual visual inspection completed. Structure, locking pins, safety net hooks, and swivel joints in excellent condition.",
                "signature_type": "LIVE"
            }
        )

        if created_report:
            # Save signature image for report
            buffer.seek(0)
            report.signature_image.save('MTQ-PR017Rev00_sig.png', ContentFile(buffer.getvalue()), save=True)
            self.stdout.write(self.style.SUCCESS("Created initial demo certificate MTQ-PR017Rev00 matching sample image!"))

        self.stdout.write(self.style.SUCCESS("Demo seeding completed successfully!"))
