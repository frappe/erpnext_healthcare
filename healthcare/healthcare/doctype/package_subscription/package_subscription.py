# Copyright (c) 2024, earthians Health Informatics Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document, _
from frappe.utils import get_link_to_form


class PackageSubscription(Document):
	def validate(self):
		self.get_package_details()
		if self.total_package_amount:
			self.outstanding_amount = self.total_package_amount - self.paid_amount

		if not self.status == "Discontinued":
			if self.paid_amount == 0:
				self.status = "Unpaid"
			else:
				self.status = "Paid" if self.outstanding_amount == 0 else "Partially Paid"

	def on_update_after_submit(self):
		if self.total_package_amount:
			self.db_set("outstanding_amount", self.total_package_amount - self.paid_amount)

		if not self.status == "Discontinued":
			if self.paid_amount == 0:
				self.db_set("status", "Unpaid")
			else:
				self.db_set("status", "Paid" if self.outstanding_amount == 0 else "Partially Paid")

	def before_insert(self):
		exists = frappe.db.exists(
			"Package Subscription",
			{
				"patient": self.patient,
				"healthcare_package": self.healthcare_package,
				"valid_to": [">=", self.valid_to],
				"docstatus": ["!=", 2],
			},
		)

		if exists:
			frappe.throw(
				_("Subscription already exists for patient {0}: {1}").format(
					frappe.bold(self.patient_name), get_link_to_form("Package Subscription", exists)
				)
			)

	@frappe.whitelist()
	def get_package_details(self):
		if not self.healthcare_package:
			return

		package_doc = frappe.get_doc("Healthcare Package", self.healthcare_package)

		self.package_details = []
		for item in package_doc.package_items:
			self.append("package_details", (frappe.copy_doc(item)).as_dict())
		self.total_package_amount = package_doc.total_package_amount
		self.outstanding_amount = package_doc.total_package_amount
		self.discount_amount = package_doc.discount_amount
		self.total_amount = package_doc.total_amount


@frappe.whitelist()
def create_payment_entry(package_subscription):
	subscription_doc = frappe.get_doc("Package Subscription", package_subscription)
	customer = frappe.db.get_value("Patient", subscription_doc.patient, "customer")
	if customer:
		payment_entry_doc = frappe.new_doc("Payment Entry")
		payment_entry_doc.update(
			{
				"payment_type": "Receive",
				"party_type": "Customer",
				"party": customer,
				"package_subscription": package_subscription,
				"paid_amount": subscription_doc.outstanding_amount,
				"received_amount": subscription_doc.outstanding_amount,
				"target_exchange_rate": 1,
			}
		)

		payment_entry_doc.insert(ignore_mandatory=True)

		return payment_entry_doc.name
