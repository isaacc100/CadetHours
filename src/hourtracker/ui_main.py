from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QComboBox, QDateEdit,
    QDoubleSpinBox, QTableWidget, QTableWidgetItem, QLineEdit, QHBoxLayout, QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt, QDate
from .database import add_entry, fetch_entries, get_summary, delete_entry, update_entry, reset_all_entries
import csv
from .excel_exporter import export_to_excel



class TimeTrackerUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hour Tracker")
        self.setMinimumSize(700, 500)
        self.categories = ["Event Cover", "Community Outreach", "Unit Running", "Other"]

        self.editing_id = None  # Keep track of whether we're editing


        self.init_ui()
        self.refresh_table()

    def init_ui(self):
        layout = QVBoxLayout()

        # --- Form layout
        form_layout = QHBoxLayout()

        self.date_input = QDateEdit()
        self.date_input.setDate(QDate.currentDate())

        self.type_input = QComboBox()
        self.type_input.addItems(self.categories)
        self.custom_tag = QLineEdit()
        self.custom_tag.setPlaceholderText("Custom Tag (optional)")

        self.hours_input = QDoubleSpinBox()
        self.hours_input.setMaximum(24)
        self.hours_input.setSuffix(" hrs")

        self.travel_input = QDoubleSpinBox()
        self.travel_input.setMaximum(24)
        self.travel_input.setSuffix(" hrs (travel)")

        self.submit_btn = QPushButton("Add Entry")
        self.export_btn = QPushButton("Export CSV")
        self.export_btn.clicked.connect(self.export_data)

        self.import_btn = QPushButton("Import CSV")
        self.import_btn.clicked.connect(self.import_data)

        self.reset_btn = QPushButton("Reset All Data")
        self.reset_btn.clicked.connect(self.reset_data)

        self.export_excel_btn = QPushButton("Export Excel")
        self.export_excel_btn.clicked.connect(self.export_excel)
        form_layout.addWidget(self.export_excel_btn)

        form_layout.addWidget(self.export_btn)
        form_layout.addWidget(self.import_btn)
        form_layout.addWidget(self.reset_btn)
        
        self.submit_btn.clicked.connect(self.handle_submit)

        form_layout.addWidget(QLabel("Date:"))
        form_layout.addWidget(self.date_input)
        form_layout.addWidget(QLabel("Type:"))
        form_layout.addWidget(self.type_input)
        form_layout.addWidget(self.custom_tag)
        form_layout.addWidget(QLabel("Hours:"))
        form_layout.addWidget(self.hours_input)
        form_layout.addWidget(QLabel("Travel:"))
        form_layout.addWidget(self.travel_input)
        form_layout.addWidget(self.submit_btn)

        # --- Table
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Date", "Type", "Hours", "Travel", "Total"])

        # --- Delete and Edit buttons
        self.delete_btn = QPushButton("Delete Selected")
        self.edit_btn = QPushButton("Edit Selected")
        self.delete_btn.clicked.connect(self.handle_delete)
        self.edit_btn.clicked.connect(self.handle_edit)

        # --- Summary
        self.summary_label = QLabel()
        self.summary_label.setWordWrap(True)

        layout.addLayout(form_layout)
        layout.addWidget(self.table)

        # Add delete and edit buttons here
        layout.addWidget(self.delete_btn)
        layout.addWidget(self.edit_btn)

        layout.addWidget(self.summary_label)

        self.setLayout(layout)

    def handle_submit(self):
        date = self.date_input.date().toString("yyyy-MM-dd")
        type_ = self.type_input.currentText()
        if self.custom_tag.text():
            type_ = self.custom_tag.text()

        hours = self.hours_input.value()
        travel = self.travel_input.value()

        if hours == 0 and travel == 0:
            return

        if self.editing_id:
            update_entry(self.editing_id, date, type_, hours, travel)
            self.submit_btn.setText("Add Entry")
            self.editing_id = None
        else:
            add_entry(date, type_, hours, travel)

        self.custom_tag.clear()
        self.refresh_table()
        self.custom_tag.clear()
        self.hours_input.setValue(0)
        self.travel_input.setValue(0)

    def handle_edit(self):
        selected = self.table.currentRow()
        if selected < 0:
            return

        entry = self.entries[selected]
        self.editing_id = entry[0]  # Save ID

        # Populate form
        self.date_input.setDate(QDate.fromString(entry[1], "yyyy-MM-dd"))
        if entry[2] in self.categories:
            self.type_input.setCurrentText(entry[2])
            self.custom_tag.clear()
        else:
            self.type_input.setCurrentText("Other")
            self.custom_tag.setText(entry[2])

        self.hours_input.setValue(entry[3])
        self.travel_input.setValue(entry[4])
        self.submit_btn.setText("Update Entry")
    
    def handle_delete(self):
        selected = self.table.currentRow()
        if selected < 0:
            return  # Nothing selected

        entry_id = self.entries[selected][0]
        delete_entry(entry_id)
        self.refresh_table()

    def refresh_table(self):
        self.table.setRowCount(0)
        self.entries = fetch_entries()
        for row_idx, entry in enumerate(self.entries):
            id_, date, type_, hours, travel = entry

            self.table.insertRow(row_idx)
            total = hours + travel
            for col_idx, value in enumerate([date, type_, f"{hours:.2f}", f"{travel:.2f}", f"{total:.2f}"]):
                self.table.setItem(row_idx, col_idx, QTableWidgetItem(str(value)))

        self.refresh_summary()

    def refresh_summary(self):
        summary, totals = get_summary()
        lines = ["<b>Category Totals:</b>"]
        for type_, h, t in summary:
            lines.append(f"{type_}: {h or 0:.2f} hrs + {t or 0:.2f} travel")

        if totals:
            total_hours = totals[0] if totals[0] is not None else 0
            total_travel = totals[1] if totals[1] is not None else 0
            overall = total_hours + total_travel

            lines.append(f"\n<b>Overall (excluding travel):</b> {total_hours:.2f} hrs")
            lines.append(f"<b>Total (including travel):</b> {overall:.2f} hrs")

        self.summary_label.setText("<br>".join(lines))
        
    def export_data(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export to CSV", "hours.csv", "CSV Files (*.csv)")
        if not path:
            return
        try:
            with open(path, "w", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerow(["Date", "Type", "Hours", "Travel"])
                for entry in self.entries:
                    writer.writerow(entry[1:])  # skip the ID
            QMessageBox.information(self, "Export Complete", f"Data exported to:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not export:\n{e}")

    def import_data(self):
        path, _ = QFileDialog.getOpenFileName(self, "Import CSV", "", "CSV Files (*.csv)")
        if not path:
            return
        try:
            with open(path, newline="", encoding="utf-8") as file:
                reader = csv.reader(file)
                next(reader)  # Skip header
                for row in reader:
                    if len(row) != 4:
                        continue
                    date, type_, hours, travel = row
                    add_entry(date, type_, float(hours), float(travel))
            self.refresh_table()
            QMessageBox.information(self, "Import Complete", f"Data loaded from:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not import:\n{e}")

    def reset_data(self):
        confirm = QMessageBox.question(
            self,
            "Confirm Reset",
            "This will delete ALL entries. Are you sure?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes:
            reset_all_entries()
            self.refresh_table()
            
    def export_excel(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export Excel", "hours.xlsx", "Excel Files (*.xlsx)")
        if not path:
            return
        export_to_excel(path, self.entries, parent_widget=self)
