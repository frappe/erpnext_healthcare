from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
	custom_field = {
		"Payment Entry": [
			{
				"fieldname": "package_subscription",
				"label": "Package Subscription",
				"fieldtype": "Link",
				"options": "Package Subscription",
				"insert_after": "treatment_counselling",
				"read_only": True,
			},
		]
	}

	create_custom_fields(custom_field)
