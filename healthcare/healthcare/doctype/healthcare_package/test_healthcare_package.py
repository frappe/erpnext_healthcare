# Copyright (c) 2024, earthians Health Informatics Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_to_date, getdate

from healthcare.healthcare.doctype.observation_template.test_observation_template import (
	create_observation_template,
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


def create_healthcare_package(therapy_type=None, obs_template=None, income_account=None):
	if not therapy_type or not obs_template:
		return

	package = frappe.get_doc(
		{
			"doctype": "Healthcare Package",
			"package_name": "Package - 1",
			"price_list": "Standard Selling",
			"currency": "INR",
			"income_account": income_account,
			"discount_amount": 100,
			"item_code": "Package - 1",
			"item_group": "Services",
			"item_wise_invoicing": 0,
		}
	)
	package.append(
		"package_items",
		{
			"package_item_type": "Observation Template",
			"package_item": obs_template.name,
			"no_of_sessions": 1,
			"rate": obs_template.rate,
			"amount": obs_template.rate,
			"amount_with_discount": obs_template.rate,
		},
	)
	package.append(
		"package_items",
		{
			"package_item_type": "Therapy Type",
			"package_item": therapy_type.name,
			"no_of_sessions": 1,
			"rate": therapy_type.rate,
			"amount": therapy_type.rate,
			"amount_with_discount": therapy_type.rate,
		},
	)
	package.insert(ignore_permissions=True, ignore_mandatory=True)

	return package


def create_subscription(patient=None, package=None, income_account=None):
	if not patient and not package.name:
		return

	subscription = frappe.get_doc(
		{
			"doctype": "Package Subscription",
			"healthcare_package": package.name,
			"patient": patient,
			"valid_to": add_to_date(getdate(), months=1),
			"income_account": income_account,
			"total_package_amount": package.total_package_amount,
		}
	)
	for item in package.package_items:
		subscription.append("package_details", (frappe.copy_doc(item)).as_dict())

	subscription.insert(ignore_permissions=True, ignore_mandatory=True)

	return subscription
