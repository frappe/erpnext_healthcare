// Copyright (c) 2024, earthians Health Informatics Pvt. Ltd. and contributors
// For license information, please see license.txt

let package_docs_filter = ["Item","Clinical Procedure Template", "Observation Template", "Therapy Type"]

frappe.ui.form.on("Healthcare Package", {
	refresh: function (frm) {
		frm.set_query("price_list", function() {
			return {
				filters: {
					"selling": 1,
				}
			};
		});

		frm.set_query("package_item_type", "package_items", function() {
			return {
				filters: {
					"name": ["in", package_docs_filter],
				}
			};
		});

		frm.set_query("income_account", function() {
			return {
				filters: {
					"account_type": "Income Account",
					"is_group": 0
				}
			};
		});
	},

	onload: function (frm) {
		if (frm.doc.is_billable) {
			let read_only = frm.doc.item ? 1 : 0;
			frm.set_df_property("item_code", "read_only", read_only);
			frm.set_df_property("item_group", "read_only", read_only);
		}
	},

	total_amount: function (frm) {
		calculate_total_payable(frm);
	},

	apply_discount_on: function (frm) {
		if(frm.doc.discount_percentage) {
			frm.trigger("discount_percentage");
		}
	},

	discount_percentage: function (frm) {
		frm.via_discount_percentage = true;

		if(frm.doc.discount_percentage && frm.doc.discount_amount) {
			frm.doc.discount_amount = 0;
		}

		let discount_field = frm.doc.apply_discount_on == "Total" ? "total_amount" : "net_total";
		var total = flt(frm.doc[discount_field]);

		var discount_amount = flt(total * flt(frm.doc.discount_percentage) / 100,
			precision("discount_amount"));

		frm.set_value("discount_amount", discount_amount)
			.then(() => delete frm.via_discount_percentage);
		calculate_total_payable(frm);
	},

	discount_amount: function (frm) {
		if (!frm.via_discount_percentage) {
			frm.doc.additional_discount_percentage = 0;
			let discount_field = frm.doc.apply_discount_on == "Total" ? "total_amount" : "net_total";
			var total = flt(frm.doc[discount_field]);
			var discount_percentage = (flt(frm.doc.discount_amount) / total) * 100;

			frm.set_value("discount_percentage", discount_percentage)
			calculate_total_payable(frm);
		}
	}
});

frappe.ui.form.on("Healthcare Package Item", {
	package_item: async function(frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		if (frm.doc.price_list && row.package_item_type && row.package_item) {
			if (row.package_item_type == "Item") {
				frappe.model.set_value(cdt, cdn, "item_code", row.package_item)
				set_item_rate(frm, row, row.package_item);
			} else {
				let item = (await frappe.db.get_value(row.package_item_type, row.package_item, "item")).message.item;
				if (item) {
					console.log()
					frappe.model.set_value(cdt, cdn, "item_code", item)
					set_item_rate(frm, row, item);
				}
			}
		}
	},

	rate: function (frm, cdt, cdn) {
		set_amount(frm, cdt, cdn);
	},

	no_of_sessions: function (frm, cdt, cdn) {
		set_amount(frm, cdt, cdn);
	},

	amount: function (frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		set_child_discounted_amount(row);
	},

	amount_with_discount: function (frm, cdt, cdn) {
		set_totals(frm);
	},

	discount_percentage: function (frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		frm.via_child_discount_percentage = true;

		if(row.discount_percentage && row.discount_amount) {
			row.discount_amount = 0;
		}

		var discount_amount = flt(row.amount * flt(row.discount_percentage) / 100,
			precision("discount_amount"));

		frappe.model.set_value(cdt, cdn, "discount_amount", discount_amount)
			.then(() => delete frm.via_child_discount_percentage);
		set_child_discounted_amount(row);
	},

	discount_amount: function (frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		if (!frm.via_child_discount_percentage) {
			row.discount_percentage = 0;
			var discount_percentage = (flt(row.discount_amount) / row.amount) * 100;

			frappe.model.set_value(cdt, cdn, "discount_percentage", discount_percentage)
			set_child_discounted_amount(row);
		}
	}
});

var set_totals = function (frm) {
	let total = 0;
	let net_total = 0;
	frm.doc.package_items.forEach((item) => {
		total += item.amount_with_discount;
		net_total += item.amount;
	});
	frm.set_value("total_amount", total);
	frm.set_value("net_total", net_total);
};

var set_amount = function (frm, cdt, cdn) {
	row = locals[cdt][cdn];
	if (row.rate && row.no_of_sessions) {
		frappe.model.set_value(cdt, cdn, "amount", (row.rate * row.no_of_sessions) - row.discount_amount);
	}
};

var calculate_total_payable = function (frm) {
	if (frm.doc.discount_amount) {
		let discount_field = frm.doc.apply_discount_on == "Total" ? "total_amount" : "net_total";
		var total = flt(frm.doc[discount_field]);
		frm.set_value("discount_amount", flt(total * flt(frm.doc.discount_percentage) / 100));
		frm.set_value("total_package_amount", total - flt(total * flt(frm.doc.discount_percentage) / 100));
	} else {
		frm.set_value("total_package_amount", frm.doc.total_amount);
	}
};

var set_child_discounted_amount = function (row) {
	frappe.model.set_value(row.doctype, row.name, "amount_with_discount", row.amount - row.discount_amount)
};

var set_item_rate = function (frm, row, item) {
	frappe.db.get_value("Item Price", {
		"item_code": item,
		"price_list": frm.doc.price_list
	}, "price_list_rate")
	.then(r => {
		let price_list_rate = r.message.price_list_rate ? r.message.price_list_rate : 0;
		frappe.model.set_value(row.doctype, row.name, "rate", price_list_rate);
	});
};
