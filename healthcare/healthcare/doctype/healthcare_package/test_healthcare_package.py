# Copyright (c) 2024, earthians Health Informatics Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from healthcare.healthcare.doctype.observation_template.test_observation_template import (
	create_observation_template,
)
from healthcare.healthcare.doctype.package_subscription.test_package_subscription import (
	create_healthcare_package,
	create_subscription,
)
from healthcare.healthcare.doctype.patient_appointment.test_patient_appointment import (
	create_patient,
)
from healthcare.healthcare.doctype.therapy_type.test_therapy_type import create_therapy_type


class TestHealthcarePackage(FrappeTestCase):
	def test_healthcare_package(self):
		frappe.delete_doc_if_exists("Healthcare Package", "Package - 1")
		obs_name = "Total Cholesterol"
		obs_template = create_observation_template(obs_name, "_Test")
		patient = create_patient()
		therapy_type = create_therapy_type()
		income_account = frappe.db.exists(
			"Account", {"root_type": "Income", "account_type": "Income Account"}
		)

		package = create_healthcare_package(therapy_type, obs_template, income_account)

		self.assertTrue(package.name)
		self.assertTrue(frappe.db.exists("Item", package.item_code))

		self.assertEqual(
			package.total_package_amount,
			5200,
		)

		self.assertEqual(
			frappe.db.get_value("Item Price", {"item_code": package.item_code}, "price_list_rate"),
			package.total_package_amount,
		)

		subscription = create_subscription(patient, package, income_account)

		self.assertTrue(subscription.name)
		self.assertEqual(
			subscription.outstanding_amount,
			subscription.total_package_amount,
		)

		self.assertEqual(
			subscription.paid_amount,
			0,
		)
