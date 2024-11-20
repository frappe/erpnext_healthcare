import json

import frappe


def execute():
	settings = frappe.get_single("Patient History Settings")
	selected_fields = [
		{"label": "Observation Template", "fieldname": "observation_template", "fieldtype": "Link"},
		{"label": "Posting Date", "fieldname": "posting_date", "fieldtype": "Date"},
		{"label": "Status", "fieldname": "status", "fieldtype": "Select"},
		{"label": "Time of Result", "fieldname": "time_of_result", "fieldtype": "Datetime"},
	]

	settings.append(
		"standard_doctypes",
		{
			"document_type": "Observation",
			"date_fieldname": "posting_date",
			"selected_fields": json.dumps(selected_fields),
		},
	)
	settings.save()
