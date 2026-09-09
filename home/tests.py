from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse

class SidebarNavigationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.client = Client()
        self.client.login(username='testuser', password='password123')

    def test_create_report_active_sidebar_item(self):
        response = self.client.get(reverse('create_report'))
        self.assertEqual(response.status_code, 200)
        # Check that 'New Certificate' is active, but 'Inspection Reports' is not active
        html = response.content.decode('utf-8')
        # Inspection Reports link shouldn't have class active
        self.assertIn('href="/reports/" class="nav-item "', html)
        self.assertNotIn('href="/reports/" class="nav-item active"', html)
        # New Certificate link should have class active
        self.assertIn('href="/reports/new/" class="nav-item active"', html)

    def test_report_list_active_sidebar_item(self):
        response = self.client.get(reverse('report_list'))
        self.assertEqual(response.status_code, 200)
        html = response.content.decode('utf-8')
        # Inspection Reports link should have class active
        self.assertIn('href="/reports/" class="nav-item active"', html)
        # New Certificate link should not have class active
        self.assertNotIn('href="/reports/new/" class="nav-item active"', html)


class CertificateCardSelectionTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testinspector', password='password123')
        self.client = Client()
        self.client.login(username='testinspector', password='password123')
        from home.models import InspectionProcedure
        self.proc1 = InspectionProcedure.objects.create(
            title="Gangway Visual Inspection Certificate",
            standard_code="EN 526:2016",
            default_statement="Gangway approval statement test."
        )
        self.proc2 = InspectionProcedure.objects.create(
            title="Load Test Report 26-C095 / ISO7061-A",
            standard_code="26-C095 / ISO7061-A",
            default_statement="Load test statement test."
        )

    def test_select_certificate_cards_view(self):
        response = self.client.get(reverse('create_report'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'select_certificate.html')
        self.assertContains(response, 'Gangway Visual Inspection Certificate')
        self.assertContains(response, 'Load Test Report 26-C095 / ISO7061-A')

    def test_select_specific_certificate_form(self):
        # Accessing active certificate (Gangway) opens report_form.html
        response = self.client.get(reverse('create_report') + f'?procedure_id={self.proc1.id}')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'report_form.html')
        self.assertContains(response, 'Gangway Visual Inspection Certificate')
        self.assertContains(response, 'EN 526:2016')
        self.assertContains(response, 'Gangway approval statement test.')

    def test_disabled_certificate_redirects(self):
        # Accessing disabled certificate redirects with warning
        response = self.client.get(reverse('create_report') + f'?procedure_id={self.proc2.id}')
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('create_report'))


