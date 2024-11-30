// Copyright (c) 2024, earthians Health Informatics Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Package Subscription", {
	setup: function (frm) {
		frm.set_query("patient", function () {
			return {
				filters: {
					status: "Active",
				},
			};
		});
		frm.set_query("healthcare_package", function () {
			return {
				filters: {
					disabled: 0,
				},
			};
		});
	},

	refresh: function (frm) {
		if (frm.doc.outstanding_amount > 0) {
			frm.add_custom_button(__("Payment Entry"), function() {
				frappe.call({
					method: "healthcare.healthcare.doctype.package_subscription.package_subscription.create_payment_entry",
					args: {
						package_subscription: frm.doc.name
					},
					callback: function (r) {
						if (r && r.message) {
							frappe.set_route("Form", "Payment Entry", r.message);
						}
					}
				});
			}, "Create")
		}
	},

	healthcare_package: function (frm) {
		if (frm.doc.healthcare_package) {
			frappe.call({
				doc: frm.doc,
				method: "get_package_details",
				callback: function (r) {
					frm.refresh();
				},
			});
		}
	}
});
