# Copyright (c) 2024, earthians Health Informatics Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_to_date, getdate

import erpnext

from healthcare.healthcare.doctype.healthcare_settings.healthcare_settings import (
	get_income_account,
	get_receivable_account,
)
from healthcare.healthcare.doctype.observation_template.test_observation_template import (
	create_observation_template,
)
from healthcare.healthcare.doctype.package_subscription.package_subscription import (
	create_payment_entry,
)
from healthcare.healthcare.doctype.patient_appointment.test_patient_appointment import (
	create_patient,
)
from healthcare.healthcare.doctype.therapy_type.test_therapy_type import create_therapy_type


class TestPackageSubscription(FrappeTestCase):
	def test_package_subscription(self):
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

		subscription = create_subscription(patient, package, income_account)

		self.assertTrue(subscription.name)
		self.assertEqual(
			package.total_package_amount,
			subscription.total_package_amount,
		)

		self.assertEqual(
			subscription.paid_amount,
			0,
		)

		if subscription.docstatus == 0:
			subscription.submit()

			payment_entry = create_payment_entry(subscription.name)
			self.assertTrue(payment_entry)

			pe_doc = frappe.get_doc("Payment Entry", payment_entry)
			mop_account = frappe.get_cached_value(
				"Mode of Payment Account", {"company": pe_doc.company, "parent": "Cash"}, "default_account"
			)
			if not mop_account:
				mop_account = frappe.get_cached_value("Company", pe_doc.company, "default_cash_account")
			paid_to_currency = frappe.get_cached_value("Account", mop_account, "account_currency")
			if not paid_to_currency:
				paid_to_currency = frappe.get_cached_value("Company", pe_doc.company, "default_currency")

			pe_doc.mode_of_payment = "Cash"
			pe_doc.paid_to = mop_account
			pe_doc.paid_to_account_currency = paid_to_currency
			pe_doc.submit()
			self.assertEqual(pe_doc.paid_amount, subscription.total_package_amount)

			self.assertEqual(
				pe_doc.paid_amount,
				frappe.get_cached_value("Package Subscription", subscription.name, "paid_amount"),
			)

			self.assertEqual(
				frappe.get_cached_value("Package Subscription", subscription.name, "outstanding_amount"), 0
			)

		sales_invoice = create_sales_invoice(patient, subscription.name)

		self.assertTrue(sales_invoice.name)
		self.assertEqual(sales_invoice.grand_total, 5200)

		if sales_invoice:
			self.assertEqual(sales_invoice.items[0].reference_dt, "Package Subscription")


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


def create_sales_invoice(patient, subscription=None):
	if not subscription:
		return

	subscriptions_to_invoice = []
	subscription_doc = frappe.get_cached_doc("Package Subscription", subscription)
	item, item_wise_invoicing = frappe.get_cached_value(
		"Healthcare Package", subscription_doc.healthcare_package, ["item", "item_wise_invoicing"]
	)
	if not item_wise_invoicing:
		subscriptions_to_invoice.append(
			{
				"reference_type": "Package Subscription",
				"reference_name": subscription,
				"service": item,
				"qty": 1,
				"amount": subscription_doc.total_package_amount,
			}
		)
	else:
		for item in subscription_doc.package_details:
			if not item.invoiced:
				subscriptions_to_invoice.append(
					{
						"reference_type": item.doctype,
						"reference_name": item.name,
						"service": item.item_code,
						"qty": item.no_of_sessions,
						"amount": item.amount_with_discount,
					}
				)

	sales_invoice = frappe.new_doc("Sales Invoice")
	sales_invoice.patient = patient
	sales_invoice.customer = frappe.get_cached_value("Patient", patient, "customer")
	sales_invoice.due_date = getdate()
	sales_invoice.currency = frappe.get_cached_value(
		"Company", subscription_doc.company, "default_currency"
	)
	sales_invoice.company = subscription_doc.company
	sales_invoice.debit_to = get_receivable_account(subscription_doc.company)
	for item in subscriptions_to_invoice:
		sales_invoice.append(
			"items",
			{
				"qty": item.get("qty"),
				"uom": "Nos",
				"conversion_factor": 1,
				"income_account": get_income_account(None, subscription_doc.company),
				"rate": item.get("amount") / item.get("qty"),
				"amount": item.get("amount"),
				"reference_dt": item.get("reference_type"),
				"reference_dn": item.get("reference_name"),
				"cost_center": erpnext.get_default_cost_center(subscription_doc.company),
				"item_code": item.get("service"),
				"item_name": item.get("service"),
				"description": item.get("service"),
			},
		)

	sales_invoice.set_missing_values()
	sales_invoice.submit()

	return sales_invoice


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
