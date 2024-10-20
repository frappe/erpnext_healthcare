import frappe
from frappe.tests.utils import FrappeTestCase

test_records = frappe.get_test_records("Sales Invoice")

EXTRA_TEST_RECORD_DEPENDENCIES = ["Sales Invoice"]


class TestSalesInvoice(FrappeTestCase):
	def test_set_healthcare_services_should_preserve_state(self):
<<<<<<< HEAD
		invoice = frappe.copy_doc(test_records[0])
=======
		invoice = frappe.copy_doc(self.globalTestRecords["Sales Invoice"][0])
>>>>>>> ce21bc0 (test: sales invoice override - use globalTestRecords)

		count = len(invoice.items)
		item = invoice.items[0]
		checked_values = [
			{
				"dt": "Item",
				"dn": item.item_name,
				"item": item.item_code,
				"qty": False,
				"rate": False,
				"income_account": False,
				"description": False,
			}
		]

		invoice.set_healthcare_services(checked_values)
		self.assertEqual(count + 1, len(invoice.items))

		invoice.set_healthcare_services(checked_values)
		self.assertEqual(count + 2, len(invoice.items))
