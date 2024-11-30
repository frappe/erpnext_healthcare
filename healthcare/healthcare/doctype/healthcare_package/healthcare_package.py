# Copyright (c) 2024, earthians Health Informatics Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt, today


class HealthcarePackage(Document):
	def validate(self):
		self.calculate_totals()
		self.create_item_from_package()

	def calculate_totals(self):
		total, net_total = 0, 0

		for item in self.package_items:
			total += item.amount_with_discount
			net_total += item.amount

		self.total_amount = total
		self.net_total = net_total

		if self.discount_amount:
			self.discount_percentage = (flt(self.discount_amount) / self.total_amount) * 100
			self.total_package_amount = self.total_amount - self.discount_amount
		elif self.discount_percentage:
			self.discount_amount = flt(self.total_amount * flt(self.discount_percentage) / 100)
			self.total_package_amount = self.total_amount - self.discount_amount
		else:
			self.total_package_amount = self.total_amount

	def create_item_from_package(self):
		item_name = self.item
		if not item_name:
			uom = frappe.db.exists("UOM", "Nos") or frappe.db.get_single_value(
				"Stock Settings", "stock_uom"
			)

			item_exists = frappe.db.exists("Item", self.item_code)
			if not item_exists:
				# Insert item
				item = frappe.get_doc(
					{
						"doctype": "Item",
						"item_code": self.item_code,
						"item_name": self.package_name,
						"item_group": self.item_group,
						"description": self.package_name,
						"is_sales_item": 1,
						"is_service_item": 1,
						"is_purchase_item": 0,
						"is_stock_item": 0,
						"include_item_in_manufacturing": 0,
						"show_in_website": 0,
						"is_pro_applicable": 0,
						"disabled": 0,
						"stock_uom": uom,
					}
				).insert(ignore_permissions=True, ignore_mandatory=True)

				item_name = item.name
			else:
				item_name = item_exists

			# Set item in the template
			self.item = item_name

		self.make_item_price(item_name, self.total_package_amount)

	def make_item_price(self, item, item_price=0.0):
		exists = frappe.db.exists(
			"Item Price",
			{
				"price_list": self.price_list,
				"item_code": item,
				"valid_from": today(),
			},
		)
		if not exists:
			frappe.get_doc(
				{
					"doctype": "Item Price",
					"price_list": self.price_list,
					"item_code": item,
					"price_list_rate": item_price,
					"valid_from": today(),
				}
			).insert(ignore_permissions=True, ignore_mandatory=True)
		else:
			frappe.db.set_value("Item Price", exists, "price_list_rate", item_price)
