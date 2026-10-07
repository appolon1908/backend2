"""Seeded authorization regressions for GH18; all data is synthetic."""
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import AccessToken

from blog_app.models import Blog
from career_app.models import Career, CareerApplication, Question, Answer
from cms.models import ContactUs, ElectronicBillingInterest, FAQs, TaxPayer, TaxPayerMedia
from customers.models import Customer
from employee.models import Employee


@override_settings(MIDDLEWARE_ACCESS_TOKEN="")
class PrivateRecordsTests(APITestCase):
    def setUp(self):
        self.regular = get_user_model().objects.create_user(email="regular@example.invalid", password="test-pass")
        self.staff = get_user_model().objects.create_user(email="staff@example.invalid", password="test-pass", is_staff=True)
        self.taxpayer = TaxPayer.objects.create(name_of_tax_payer="Private company", tax_payer_rnc="SENSITIVE-RNC")
        ContactUs.objects.create(full_name="Contact fixture", email="contact@example.invalid", message="Private message")
        ElectronicBillingInterest.objects.create(full_name="Billing fixture", email="billing@example.invalid", phone="5550100", uses_erp=True, consent_to_contact=True)
        self.career = Career.objects.create(title="Public opening", description="Public description")
        self.application = CareerApplication.objects.create(career=self.career, full_name="Private applicant", email="applicant@example.invalid")
        self.question = Question.objects.create(career=self.career, text="Public question", question_type=Question.TEXT)
        Answer.objects.create(question=self.question, full_name="Private answerer", email="answer@example.invalid", text_answer="Private answer")
        self.customer = Customer.objects.create(first_name="Private", last_name="Customer", email="customer@example.invalid")
        self.private_urls = [
            "/api/cms/tax-payer/",
            f"/api/cms/tax-payer/{self.taxpayer.pk}/",
            "/api/cms/contact-us/",
            "/api/cms/electronic-billing-interest/",
            "/api/career/applications/",
            f"/api/career/applications/{self.application.pk}/",
            f"/api/career/{self.career.pk}/applications/",
            f"/api/career/{self.question.pk}/answers/",
            "/api/customers/",
            f"/api/customers/{self.customer.pk}/",
        ]

    def authenticate(self, user):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(user)}")

    def test_anonymous_cannot_read_populated_private_records(self):
        for url in self.private_urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 401)
                self.assertIn("Bearer", response["WWW-Authenticate"])

    def test_regular_jwt_cannot_read_populated_private_records(self):
        self.authenticate(self.regular)
        for url in self.private_urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 403)

    def test_staff_reads_each_correct_collection(self):
        self.authenticate(self.staff)
        for url in self.private_urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)
        contacts = self.client.get("/api/cms/contact-us/").data
        billing = self.client.get("/api/cms/electronic-billing-interest/").data
        self.assertEqual(contacts[0]["email"], "contact@example.invalid")
        self.assertEqual(billing[0]["email"], "billing@example.invalid")
        self.assertNotIn("message", billing[0])

    def test_regular_user_cannot_update_or_delete_taxpayer_or_customer(self):
        self.authenticate(self.regular)
        for url in [f"/api/cms/tax-payer/{self.taxpayer.pk}/", f"/api/customers/{self.customer.pk}/"]:
            with self.subTest(url=url):
                self.assertEqual(self.client.put(url, {}, format="json").status_code, 403)
        self.assertEqual(self.client.delete(f"/api/cms/tax-payer/{self.taxpayer.pk}/").status_code, 403)
        self.assertTrue(TaxPayer.objects.filter(pk=self.taxpayer.pk).exists())

    def test_staff_can_update_and_delete_taxpayer(self):
        self.authenticate(self.staff)
        response = self.client.put(f"/api/cms/tax-payer/{self.taxpayer.pk}/", {"name_of_tax_payer": "Updated"}, format="json")
        self.assertEqual(response.status_code, 200)
        self.taxpayer.refresh_from_db()
        self.assertEqual(self.taxpayer.name_of_tax_payer, "Updated")
        self.assertEqual(self.client.delete(f"/api/cms/tax-payer/{self.taxpayer.pk}/").status_code, 204)

    def test_public_content_and_taxpayer_intake_remain_available(self):
        FAQs.objects.create(question="Public FAQ", answer="Public answer")
        self.assertEqual(self.client.get("/api/cms/faqs/").data[0]["answer"], "Public answer")
        self.assertEqual(self.client.get("/api/career/").status_code, 200)
        response = self.client.post("/api/cms/tax-payer/", {"name_of_tax_payer": "New submission"}, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertTrue(TaxPayer.objects.filter(name_of_tax_payer="New submission").exists())

    def test_anonymous_calendar_read_is_denied_before_provider_access(self):
        self.client.raise_request_exception = False
        self.assertEqual(self.client.get("/api/calendar/").status_code, 401)

    def test_regular_user_cannot_publish_blog(self):
        self.authenticate(self.regular)
        response = self.client.post("/api/blog/", {"title": "Unauthorized", "content": "Private", "status": "PUBLISHED"}, format="json")
        self.assertEqual(response.status_code, 403)
        self.assertFalse(Blog.objects.filter(title="Unauthorized").exists())

    def test_staff_can_publish_blog_and_public_can_read_it(self):
        self.authenticate(self.staff)
        response = self.client.post("/api/blog/", {"title": "Staff publication", "content": "Public", "status": "PUBLISHED"}, format="json")
        self.assertEqual(response.status_code, 201)
        self.client.credentials()
        self.assertEqual(self.client.get(f"/api/blog/{response.data['id']}/").status_code, 200)


class PrivateMediaTests(APITestCase):
    def setUp(self):
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.media_override = override_settings(MEDIA_ROOT=self.directory.name)
        self.media_override.enable()
        self.addCleanup(self.media_override.disable)
        self.staff = get_user_model().objects.create_user(email="staffmedia@example.invalid", is_staff=True)
        self.regular = get_user_model().objects.create_user(email="regularmedia@example.invalid")
        taxpayer = TaxPayer.objects.create(name_of_tax_payer="Private")
        self.tax_file = TaxPayerMedia.objects.create(taxpayer=taxpayer, media_file=SimpleUploadedFile("tax.txt", b"private tax bytes"))
        self.application = CareerApplication.objects.create(full_name="Applicant", email="private@example.invalid", resume=SimpleUploadedFile("resume.txt", b"private resume bytes"), user_id=SimpleUploadedFile("id.txt", b"private identity bytes"))
        self.urls = [self.tax_file.media_file.url, self.application.resume.url, self.application.user_id.url]

    def test_private_file_urls_require_authentication(self):
        for url in self.urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 401)

    def test_private_file_urls_reject_regular_cookie_session(self):
        self.client.cookies["codestra_access"] = str(AccessToken.for_user(self.regular))
        for url in self.urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 403)

    def test_staff_cookie_download_returns_exact_file_as_private_attachment(self):
        self.client.cookies["codestra_access"] = str(AccessToken.for_user(self.staff))
        for url, expected in zip(self.urls, [b"private tax bytes", b"private resume bytes", b"private identity bytes"]):
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(b"".join(response.streaming_content), expected)
                self.assertTrue(response["Content-Disposition"].startswith("attachment;"))
                self.assertIn("no-store", response["Cache-Control"])
                self.assertEqual(response["X-Content-Type-Options"], "nosniff")
                response.close()

    def test_unknown_files_and_traversal_are_not_served(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(self.staff)}")
        for url in ["/media/career/not-registered.txt", "/media/tax/images/../../secret.txt", "/media/career/%2e%2e/secret.txt"]:
            with self.subTest(url=url):
                self.assertIn(self.client.get(url).status_code, [400, 404])

    @override_settings(DEBUG=True)
    def test_debug_media_route_does_not_bypass_private_authorization(self):
        self.assertEqual(self.client.get(self.application.resume.url).status_code, 401)


class EmployeeDirectoryTests(APITestCase):
    def setUp(self):
        self.employee = Employee.objects.create(first_name="Public", last_name="Person", email="private@example.invalid", phone="5550101", date_of_birth="1980-01-01", extra_fields={"passport": "PRIVATE"}, is_active=True)

    @patch("employee.views.requests.get", side_effect=__import__("requests").ConnectionError("offline"))
    def test_public_local_directory_omits_private_fields(self, _request):
        for url in ["/api/employee/", f"/api/employee/{self.employee.pk}/"]:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            records = response.data if isinstance(response.data, list) else [response.data]
            for record in records:
                self.assertEqual(record["first_name"], "Public")
                for field in ["date_of_birth", "email", "phone", "extra_fields", "employee_id"]:
                    self.assertNotIn(field, record)

    @patch("employee.views.requests.get")
    def test_public_provider_directory_uses_same_field_allowlist(self, get):
        get.return_value.status_code = 200
        get.return_value.json.return_value = [{"id": 42, "first_name": "Public", "last_name": "Provider", "date_of_birth": "1980-01-01", "email": "private@example.invalid", "arbitrary_secret": "PRIVATE"}]
        response = self.client.get("/api/employee/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]["first_name"], "Public")
        self.assertNotIn("date_of_birth", response.data[0])
        self.assertNotIn("email", response.data[0])
        self.assertNotIn("arbitrary_secret", response.data[0])

class PublicCareerIntakeTests(APITestCase):
    def test_anonymous_application_is_saved_with_private_file_urls(self):
        with TemporaryDirectory() as directory, override_settings(MEDIA_ROOT=directory):
            career = Career.objects.create(title="Public vacancy", description="Apply")
            response = self.client.post("/api/career/application/", {
                "career_id": career.pk, "full_name": "Synthetic applicant",
                "email": "newapplicant@example.invalid", "primary_profession": "Developer",
                "project_link": "https://example.invalid", "github_repo": "https://example.invalid/code",
                "user_id": SimpleUploadedFile("identity.txt", b"synthetic identity"),
                "resume": SimpleUploadedFile("resume.txt", b"synthetic resume"),
            }, format="multipart")
            self.assertEqual(response.status_code, 201)
            application = CareerApplication.objects.get()
            self.assertEqual(application.email, "newapplicant@example.invalid")
            self.assertEqual(self.client.get(application.resume.url).status_code, 401)
