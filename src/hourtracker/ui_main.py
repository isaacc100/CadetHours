from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QComboBox, QDateEdit,
    QDoubleSpinBox, QTableWidget, QTableWidgetItem, QLineEdit, QHBoxLayout, 
    QFileDialog, QMessageBox, 
)
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt, QDate
from .database import add_entry, fetch_entries, get_summary, delete_entry, update_entry, reset_all_entries
import csv
from .excel_exporter import export_to_excel
from pathlib import Path



class TimeTrackerUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hour Tracker")
        self.setMinimumSize(700, 500)
        self.categories = ["Event Cover", "Community Outreach", "Unit Running", "Other"]
        icon_path = Path(__file__).parent.parent.parent / "icons" / "icon.ico"
        icon = QIcon(str(icon_path.resolve()))
        self.setWindowIcon(icon)

        self.editing_id = None  # Keep track of whether we're editing


        self.init_ui()
        self.refresh_table()

    def init_ui(self):
        layout = QVBoxLayout()

        # --- Row 1: Export/Import and Reset
        row1_layout = QHBoxLayout()
        self.export_import_btn = QPushButton("Export/Import")
        self.export_import_btn.clicked.connect(self.handle_export_import)
        self.reset_btn = QPushButton("Reset All Data")
        self.reset_btn.clicked.connect(self.reset_data)
        row1_layout.addWidget(self.export_import_btn)
        row1_layout.addWidget(self.reset_btn)

        # --- Row 2: Date, Hours, Travel, Type, Custom Tag
        row2_layout = QHBoxLayout()
        self.date_input = QDateEdit()
        self.date_input.setDate(QDate.currentDate())
        self.hours_input = QDoubleSpinBox()
        self.hours_input.setMaximum(24)
        self.hours_input.setSuffix(" hrs")
        self.travel_input = QDoubleSpinBox()
        self.travel_input.setMaximum(24)
        self.travel_input.setSuffix(" hrs (travel)")
        self.type_input = QComboBox()
        self.type_input.addItems(self.categories)
        self.custom_tag = QLineEdit()
        self.custom_tag.setPlaceholderText("Custom Tag (optional)")
        row2_layout.addWidget(QLabel("Date:"))
        row2_layout.addWidget(self.date_input)
        row2_layout.addWidget(QLabel("Hours:"))
        row2_layout.addWidget(self.hours_input)
        row2_layout.addWidget(QLabel("Travel:"))
        row2_layout.addWidget(self.travel_input)
        row2_layout.addWidget(QLabel("Type:"))
        row2_layout.addWidget(self.type_input)
        row2_layout.addWidget(self.custom_tag)

        # --- Row 3: Name, Note, Add Entry
        row3_layout = QHBoxLayout()
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Name (optional)")
        self.note_input = QLineEdit()
        self.note_input.setPlaceholderText("Note (optional)")
        self.submit_btn = QPushButton("Add Entry")
        self.submit_btn.clicked.connect(self.handle_submit)
        row3_layout.addWidget(QLabel("Name:"))
        row3_layout.addWidget(self.name_input)
        row3_layout.addWidget(QLabel("Note:"))
        row3_layout.addWidget(self.note_input)
        row3_layout.addWidget(self.submit_btn)

        # --- Table (Row 4)
        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels(["Date", "Name", "Type", "Hours", "Travel", "Total", "Recorded", "Notes"])
        self.table.itemChanged.connect(self.handle_recorded_change)

        # --- Row 5: Delete, Edit
        row5_layout = QHBoxLayout()
        self.delete_btn = QPushButton("Delete Selected")
        self.edit_btn = QPushButton("Edit Selected")
        self.delete_btn.clicked.connect(self.handle_delete)
        self.edit_btn.clicked.connect(self.handle_edit)
        row5_layout.addWidget(self.delete_btn)
        row5_layout.addWidget(self.edit_btn)

        # --- Summary (Totals)
        self.summary_left = QLabel()
        self.summary_left.setWordWrap(True)
        self.summary_right = QLabel()
        self.summary_right.setWordWrap(True)
        summary_layout = QHBoxLayout()
        summary_layout.addWidget(self.summary_left, stretch=2)
        summary_layout.addWidget(self.summary_right, stretch=1)

        layout.addLayout(row1_layout)
        layout.addLayout(row2_layout)
        layout.addLayout(row3_layout)
        layout.addWidget(self.table)
        layout.addLayout(row5_layout)
        layout.addLayout(summary_layout)
        self.setLayout(layout)
    def handle_export_import(self):
        # Dialog to choose Export or Import
        from PySide6.QtWidgets import QInputDialog
        choice, ok = QInputDialog.getText(self, "Export/Import", "Type 'export' to export or 'import' to import:")
        if not ok:
            return
        choice = choice.strip().lower()
        if choice == "export":
            self.export_excel()
        elif choice == "import":
            self.import_data()
        else:
            QMessageBox.warning(self, "Invalid Choice", "Please type 'export' or 'import'.")

    def handle_submit(self):
        date = self.date_input.date().toString("yyyy-MM-dd")
        name = self.name_input.text()
        type_ = self.type_input.currentText()
        if self.custom_tag.text():
            type_ = self.custom_tag.text()
        hours = self.hours_input.value()
        travel = self.travel_input.value()
        notes = self.note_input.text()
        if hours == 0 and travel == 0:
            return
        recorded = False  # New entries default to unrecorded
        if self.editing_id:
            # If editing, get the current state of the Recorded checkbox from the table
            row = None
            for i, entry in enumerate(self.entries):
                if entry[0] == self.editing_id:
                    row = i
                    break
            if row is not None:
                recorded_item = self.table.item(row, 6)
                if recorded_item is not None:
                    recorded = recorded_item.checkState() == Qt.Checked
            else:
                # fallback to old entry value
                old_entry = next((e for e in self.entries if e[0] == self.editing_id), None)
                recorded = old_entry[6] if old_entry else False
            update_entry(self.editing_id, date, name, type_, hours, travel, recorded, notes)
            self.submit_btn.setText("Add Entry")
            self.editing_id = None
        else:
            add_entry(date, name, type_, hours, travel, recorded, notes)
        self.custom_tag.clear()
        self.note_input.clear()
        self.name_input.clear()
        self.refresh_table()
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
        if hasattr(self, "name_input"):
            self.name_input.setText(entry[2])
        if entry[3] in self.categories:
            self.type_input.setCurrentText(entry[3])
            self.custom_tag.clear()
        else:
            self.type_input.setCurrentText("Other")
            self.custom_tag.setText(entry[3])

        self.hours_input.setValue(entry[4])
        self.travel_input.setValue(entry[5])
        self.submit_btn.setText("Update Entry")
    
    def handle_delete(self):
        selected = self.table.currentRow()
        if selected < 0:
            return  # Nothing selected

        entry_id = self.entries[selected][0]
        delete_entry(entry_id)
        self.refresh_table()

    def refresh_table(self):
        self.table.blockSignals(True)
        self.table.setRowCount(0)
        self.entries = fetch_entries()
        for row_idx, entry in enumerate(self.entries):
            # entry: (id, date, name, type, hours, travel, recorded, notes)
            if len(entry) == 8:
                id_, date, name, type_, hours, travel, recorded, notes = entry
            else:
                # fallback for old entries
                id_, date, type_, hours, travel = entry
                name = ""
                recorded = False
                notes = ""

            self.table.insertRow(row_idx)
            total = hours + travel
            for col_idx, value in enumerate([date, name, type_, f"{hours:.2f}", f"{travel:.2f}", f"{total:.2f}"]):
                self.table.setItem(row_idx, col_idx, QTableWidgetItem(str(value)))

            # Recorded checkbox
            item = QTableWidgetItem()
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked if recorded else Qt.Unchecked)
            self.table.setItem(row_idx, 6, item)

            # Notes column
            self.table.setItem(row_idx, 7, QTableWidgetItem(notes or ""))

        self.table.blockSignals(False)
        self.refresh_summary()
    def handle_edit_note(self):
        selected = self.table.currentRow()
        if selected < 0:
            return
        entry = self.entries[selected]
        note, ok = QMessageBox.getText(self, "Edit Note", "Enter note:", text=entry[7] if len(entry) == 8 else "")
        if ok:
            # Update note in database
            if len(entry) == 8:
                update_entry(entry[0], entry[1], entry[2], entry[3], entry[4], entry[5], entry[6], note)
            else:
                # fallback for old entries
                update_entry(entry[0], entry[1], "", entry[2], entry[3], entry[4], False, note)
            self.refresh_table()

    def refresh_summary(self):
        summary, totals = get_summary()
        # Category totals (right column)
        cat_lines = ["<b>Category Totals:</b>"]
        for type_, h, t in summary:
            cat_lines.append(f"{type_}: {h or 0:.2f} hrs + {t or 0:.2f} travel")
        self.summary_right.setText("<br>".join(cat_lines))

        # Overall/recorded/unrecorded totals (left column)
        left_lines = []
        recorded_hours = recorded_travel = unrec_hours = unrec_travel = 0.0
        for entry in self.entries:
            if len(entry) == 5:
                # old format: id, date, type, hours, travel
                _, _, _, h, t = entry
                rec = False
            elif len(entry) == 8:
                # new format: id, date, name, type, hours, travel, recorded, notes
                _, _, _, _, h, t, rec, _ = entry
            else:
                # fallback: try to get hours/travel/recorded
                h = entry[4] if len(entry) > 4 else 0
                t = entry[5] if len(entry) > 5 else 0
                rec = entry[6] if len(entry) > 6 else False
            if rec:
                recorded_hours += h
                recorded_travel += t
            else:
                unrec_hours += h
                unrec_travel += t

        left_lines.append(f"<b>Recorded:</b> {recorded_hours:.2f} hrs + {recorded_travel:.2f} travel")
        left_lines.append(f"<b>Unrecorded:</b> {unrec_hours:.2f} hrs + {unrec_travel:.2f} travel")

        if totals:
            total_hours = totals[0] if totals[0] is not None else 0
            total_travel = totals[1] if totals[1] is not None else 0
            overall = total_hours + total_travel

            left_lines.append(f"<b>Overall (excluding travel):</b> {total_hours:.2f} hrs")
            left_lines.append(f"<b>Total (including travel):</b> {overall:.2f} hrs")

        self.summary_left.setText("<br>".join(left_lines))

    def handle_recorded_change(self, item):
        # Only handle changes in the Recorded column (column 6)
        if item.column() != 6:
            return
        row = item.row()
        entry = self.entries[row]
        recorded = item.checkState() == Qt.Checked
        # Update entry in database, preserving all other fields
        if len(entry) == 8:
            id_, date, name, type_, hours, travel, _, notes = entry
            update_entry(id_, date, name, type_, hours, travel, recorded, notes)
        elif len(entry) == 5:
            id_, date, type_, hours, travel = entry
            update_entry(id_, date, '', type_, hours, travel, recorded, '')
        else:
            # fallback for any other format
            id_ = entry[0]
            date = entry[1] if len(entry) > 1 else ''
            name = entry[2] if len(entry) > 2 else ''
            type_ = entry[3] if len(entry) > 3 else ''
            hours = entry[4] if len(entry) > 4 else 0
            travel = entry[5] if len(entry) > 5 else 0
            notes = entry[7] if len(entry) > 7 else ''
            update_entry(id_, date, name, type_, hours, travel, recorded, notes)
        self.refresh_table()
        
    def export_data(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export to CSV", "hours.csv", "CSV Files (*.csv)")
        if not path:
            return
        try:
            with open(path, "w", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerow(["Date", "Type", "Hours", "Travel", "Recorded"])
                for entry in self.entries:
                    # skip the ID, add recorded as 1/0
                    row = list(entry[1:5]) + [1 if len(entry) > 5 and entry[5] else 0]
                    writer.writerow(row)
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
                    if len(row) < 4:
                        continue
                    date, type_, hours, travel = row[:4]
                    recorded = False
                    if len(row) > 4:
                        recorded = bool(int(row[4]))
                    add_entry(date, type_, float(hours), float(travel), recorded)
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
