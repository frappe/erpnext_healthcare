import frappe


def execute():
	diagnostic_report = frappe.db.get_all("Diagnostic Report", pluck="name")

	for diag in diagnostic_report:
		diag_doc = frappe.get_doc("Diagnostic Report", diag)

		subject = frappe.render_template(
			"healthcare/healthcare/doctype/diagnostic_report/diagnostic_report.html", dict(doc=diag_doc)
		)
		medical_record = frappe.new_doc("Patient Medical Record")
		medical_record.patient = diag_doc.patient
		medical_record.subject = subject
		medical_record.status = "Open"
		medical_record.communication_date = diag_doc.reference_posting_date
		medical_record.reference_doctype = "Diagnostic Report"
		medical_record.reference_name = diag_doc.name
		medical_record.reference_owner = diag_doc.owner
		medical_record.save(ignore_permissions=True)
