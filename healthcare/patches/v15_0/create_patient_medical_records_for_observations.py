import frappe
from frappe.utils import getdate


def execute():
	observations = frappe.db.get_all("Observation", filters={"docstatus": 1}, pluck="name")

	for obs in observations:
		obs_doc = frappe.get_doc("Observation", obs)

		subject = frappe.render_template(
			"healthcare/healthcare/doctype/observation/observation.html", dict(doc=obs_doc)
		)

		reference = obs
		if obs_doc.parent_observation:
			reference = obs_doc.parent_observation

		exists = frappe.db.exists(
			"Patient Medical Record", {"reference_doctype": "Observation", "reference_name": reference}
		)

		if exists:
			frappe.db.set_value("Patient Medical Record", exists, "subject", subject)
		else:
			medical_record = frappe.new_doc("Patient Medical Record")
			medical_record.patient = obs_doc.patient
			medical_record.subject = subject
			medical_record.status = "Open"
			medical_record.communication_date = getdate(obs_doc.modified)
			medical_record.reference_doctype = "Observation"
			medical_record.reference_name = reference
			medical_record.reference_owner = obs_doc.owner
			medical_record.save(ignore_permissions=True)
